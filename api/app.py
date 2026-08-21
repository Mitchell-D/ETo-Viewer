"""
Defines fastapi endpoints for RxBurn Dashboard

This script is run by the ASGI server (uvicorn) once on startup, then the
decorated functions implementing the endpionts are invoked asynchronously
whenever a request is issued.
"""
import json
import zarr
import os
import numpy as np
import redis.asyncio as redis
import asyncio
from time import perf_counter
from redis.commands.core import HashDataPersistOptions as HDPO
from fastapi import FastAPI, HTTPException, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from contextlib import asynccontextmanager
from starlette_compress import CompressMiddleware
from pathlib import Path

## amount of time to keep a cache key after a hit
CACHE_TTL = 600 ## 10 minutes
## amount of time a lock can be held
LOCK_TTL = 10 ## 10 seconds
## how long each waiting process waits between cache pings
LOCK_WAIT = .01 ## seconds
DEBUG = True

""" ---( data sourcing )--- """

## zarr store reference
zarr.config.set({"async.concurrency": 64})
zgrp = zarr.open("eto-forecast.zarr", mode="r")
zattrs = dict(zgrp.attrs)

## determine the initialization times available for each region/feat combo
itimes = {} ## region:feat:[times]
for rk in zgrp["regions"].keys():
    itimes[rk] = {fk:[] for fk in zattrs["labels"]["feats"]}
    for dstr in zgrp[f"/regions/{rk}/data"].keys():
        if "eto_spatial" in zgrp[f"/regions/{rk}/data/{dstr}"].keys():
            itimes[rk]["eto"].append(dstr)

## load all the date strings for valid times at each available init time
vtimes = {}
for dstr in zgrp["vtimes"].keys():
    t = zgrp[f"/vtimes/{dstr}"][...]
    vtimes[dstr] = [
        v.strftime("%Y%m%d")
        for v in t.astype("datetime64[us]").astype("O")
        ]

pgroups = zattrs["pgroups"] ## pgroup:region:{geojson}

## explicitly collect metadata relevant to IFS ensemble data.
meta_eto = {
    ## metadata
    "labels":{
        **zattrs["labels"],
        "itimes":itimes,
        "vtimes":vtimes,
        },
    "regions":zattrs["regions"],

    "nvtimes":zattrs["nvtimes"],

    ## data normalization
    "norm_bounds":zattrs["norm_bounds"],
    "norm_res":zattrs["norm_resolution"],
    "mask_val":zattrs["mask_val"],

    ## labels
    "long_labels":zattrs["long_labels"],
    "short_labels":zattrs["short_labels"],

    #"vector_toggle_state":zgrp.attrs["gefs"]["vector_toggle_state"],
    }

## color map metadata and concatenated color map array
cmap_info = {
    **zgrp.attrs["cmaps"],
    "cmaps":zgrp["cmaps"][...].tolist(),
    "default_bounds":zattrs["cmap_default_bounds"],
    "default_name":zattrs["cmap_default_name"],
    }

""" ---( cache methods )--- """

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    declare a context manager for each worker that guaruntees the connection
    is opened before the serve loop begins, and is closed when it ends.

    Each worker instantiates its own app, so gets its own connection via the
    app.state context.

    This generator essentially making sure the single reference to the redis
    cache reference stays alive as long as the app object stays alive.
    __aenter__() of the wrapping context manager calls the generator once
    (which then suspends at yield), then once again on __aexit__() to let
    the asynchronous cache shutdown process run.
    """
    app.state.redis = redis.from_url(
        os.environ["REDIS_URL"],
        encoding="utf-8",
        decode_responses=False,
        )
    yield

async def populate_locked_range(
        rcache:redis.Redis, lkey:str, group:str, mapping:dict):
    """
    Populates a cache group with multiple k/v pairs from a dict, with the
    assumption that the range is currently locked by the provided cache
    semaphore key.

    This method is expected to work as a background process whenever the
    first frame request in the range acquires the lock, which allows the first
    frame to be returned before the rest of the cache has been populated.
    """
    async with rcache.pipeline(transaction=True) as pipe:
        try:
            pipe.hsetex(
                group,
                mapping=mapping,
                data_persist_option=HDPO.FNX,
                ex=CACHE_TTL,
                )
            ## asynchronously add all the frames for this subkey
            await pipe.execute()
        finally:
            await rcache.hdel("lock", lkey)

async def raster_cache_get(request:Request, background:BackgroundTasks,
        rcache:redis.Redis, ckey:tuple):
    """
    retrieve raster data from the redis cache. includes logic for distributed
    mutex so that multiple workers don't try to read the same data from disc
    at the same time (which will be very common in frame-by-frame context)

    the lock works by manipulating a 1-byte value in the cache which has the
    "NX" flag (set if doesn't exist)

    :@param request: redis Request object for this worker
    :@param background: redis BackgroundTasks manager for bulk caching
    :@param rcache: redis cache connection object
    :@param ckey: 5-tuple (dataset, region, itime, feat, metric)
        for the current request
    """
    region, itime, feat, metric = ckey
    ## key for the group name
    gkey = f"{region}_{itime}_{feat}"
    ## key for the current frame
    fkey = f"{metric}"
    ## if possible, immediately get from the cache
    cached = await rcache.hget(gkey, fkey)
    if not cached is None:
        return cached

    ## if the cache missed, determine the lock that must be acquired.
    lkey = f"{region}_{itime}_{feat}"
    cache_being_filled = False
    while True:
        ## returns True only for the one worker that wins the race
        acquired = await rcache.hsetex(
                name="lock",
                key=lkey,
                value="1",
                data_persist_option=HDPO.FNX,
                ex=LOCK_TTL
                )
        if acquired:
            try:
                ## make sure cache hasn't been populated since requesting lock
                cached = await rcache.hget(gkey, fkey)
                if cached is not None:
                    ## detect if the request was aborted while waiting on
                    ## the lock to resolve
                    if await request.is_disconnected():
                        return None
                    return cached

                if DEBUG:
                    print(f"{os.getpid()} setting cache")

                ## go ahead and set the current cache value first
                fix = meta_eto["labels"]["feats"].index(feat)
                ## stored as: (feat, metric, horizon, lat, lon)
                X = zgrp[f"/regions/{region}/data/{itime}/{feat}_spatial"][...]
                frames = {
                    mk:X[mix].tobytes()
                    for mix,mk in enumerate(meta_eto["labels"]["metrics"])
                    }
                cur_frame = frames.pop(metric)
                await rcache.hsetex(
                    gkey, fkey, cur_frame,
                    data_persist_option=HDPO.FNX,
                    ex=CACHE_TTL,
                    )

                ## dispatch a background task for loading the requested data
                background.add_task(
                    populate_locked_range,
                    rcache=rcache,
                    lkey=lkey,
                    group=gkey,
                    mapping=frames,
                    )

                ## indicate that the cache is being filled, so the background
                ## task will handle releasing the semaphores
                cache_being_filled = True

                ## check whether the request disconnected while handling above
                if await request.is_disconnected():
                    return None
                ## otherwise return the currently-requested frame
                return cur_frame

            finally:
                ## If the lock has been acquired and the try block exits,
                ## either the value has been populated by a different worker
                ## and loaded from the cache, the request disconnected, or
                ## this worker kicked off a background process to load other
                ## frames. In all but the latter case, the lock needs to
                ## be immediately released.
                if not cache_being_filled:
                    await rcache.hdel("lock", lkey)
        else:
            ## another worker has the lock...
            ## see if the request has been cancelled
            if await request.is_disconnected():
                return None
            ## otherwise see if the worker with the lock has added the
            ## requested value to the cache
            cached = await rcache.hget(gkey, fkey)
            if not cached is None:
                return cached
            ## if neither of the above, wait before re-checking
            await asyncio.sleep(LOCK_WAIT)

""" ---( app initialization )--- """

## declare app and add middleware for logging requests
app = FastAPI(title="RxBurn Database", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"], ## all HTTP methods (GET, POST, PUT, etc.)
    allow_headers=["*"], ## all headers
    )
app.add_middleware(
    CompressMiddleware,
    minimum_size=500,
    zstd_level=4,
    brotli_quality=4,
    gzip_level=6,
    )

""" ---( app endpoints )--- """

@app.get("/eto/raster/{region}/{feat}/{metric}/{itime}")
async def gefs_raster(request:Request, background:BackgroundTasks,
        region:str, feat:str, metric:str, itime:str,
        ):
    """
    return a byte stream for the requested raster frame in the provided times

    If init time and frame aren't provided, default to the latest init time
    and the first horizon time.

    The same defaults assumption needs to be mirrored on the javascript side
    when it receives the metadata
    """
    if DEBUG:
        dbt0 = perf_counter()
    ## validate the inputs
    if not region in meta_gefs["labels"]["regions"]:
        raise HTTPException(status_code=400, detail=f"Invalid region:{region}")
    if not feat in meta_gefs["labels"]["feats"]:
        raise HTTPException(status_code=400, detail=f"Invalid feat:{feat}")
    if not metric in meta_gefs["labels"]["metrics"]:
        raise HTTPException(status_code=400, detail=f"Invalid metric:{metric}")
    if not itime in meta_gefs["labels"]["itimes"][region][feat]:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid init time:{itime}"
            )

    ## retrieve the cache reference from the app state namespace
    rc = app.state.redis

    ## get the data from the cache
    ckey = (region, itime, feat, metric)
    if DEBUG:
        print(f"retrieving {ckey}")
    cached = await raster_cache_get(
            request=request,
            background=background,
            rcache=rc,
            ckey=ckey,
            )
    cshape = (
        meta_gefs["nvtimes"],
        meta_gefs["regions"][region]["height"],
        meta_gefs["regions"][region]["width"],
        )
    carr = np.frombuffer(cached, dtype=np.uint16).reshape(cshape)
    nbytes = str(carr.nbytes)

    ## return as a byte stream
    r = Response(
        content=carr.tobytes(),
        media_type="application/octet-stream",
        headers={
            "Content-Type":"application/octet-stream",
            "X-Array-Shape":",".join(map(str, cshape)),
            "Content-Length":nbytes,
            }
        )
    if DEBUG:
        print(f"{os.getpid()} processed {nbytes} in {perf_counter()-dbt0:.3f}")

    return r

@app.get("/pgroup/{pgroup}/{region}")
def pgroup(pgroup:str, region:str):
    """ endpoint for map polygon geojsons """
    if not pgroup in pgroups.keys():
        raise HTTPException(status_code=400, detail=f"Invalid pgroup:{pgroup}")
    if not region in pgroups[pgroup].keys():
        raise HTTPException(status_code=400, detail=f"Invalid region:{region}")
    return pgroups[pgroup][region]

@app.get("/eto/menu")
def eto_menu():
    """ endpoint for menu information (labels, time range, etc) """
    return meta_eto

@app.get("/cmaps")
def cmaps():
    """ endpoint for concatenated color maps array and its metadata """
    return cmap_info
