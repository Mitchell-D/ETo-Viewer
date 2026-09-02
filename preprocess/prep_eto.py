import numpy as np
import zarr
import multiprocessing  as mp
import netCDF4 as nc
from datetime import date,datetime,timedelta
from pathlib import Path

import config

def norm_uint16(x, nmin, nmax, nres, mask_val):
    m_valid = np.isfinite(x)
    y = np.clip((x-nmin)/(nmax-nmin)*(nres-1), 0, nres-1)
    y[~m_valid] = mask_val
    return np.round(y).astype(np.uint16)

def evaluate_feats(data, get_feats, dependency_rules, axis, weights=None):
    """ """
    deps = []
    for mk,mdl in dependency_rules.items():
        if not (mk in get_feats):
            continue
        for md in mdl:
            if not (md in deps) and not (md in get_feats):
                deps.append(md)

    farrs = {}
    percentile_feats = []
    derived_feats = []
    pctl_options = [f"p{v:02}" for v  in range(1, 100)]
    for fk in get_feats + deps:
        if fk == "min":
            farrs[fk] = np.amin(data, axis=axis)
        elif fk == "max":
            farrs[fk] = np.amax(data, axis=axis)
        elif fk == "mean":
            if weights is None:
                farrs[fk] = np.average(data, axis=axis)
            else:
                farrs[fk] = np.average(data, axis=axis, weights=weights)
        elif fk == "stddev":
            if weights is None:
                farrs[fk] = np.std(data, axis=axis)
            else:
                avg = np.average(data, weights=weights,
                        axis=axis, keepdims=True)
                var = np.average((data - avg)**2, weights=weights, axis=axis)
                farrs[fk] = np.sqrt(var)
        elif fk in dependency_rules.keys():
            derived_feats.append(fk)
        elif fk in pctl_options:
            percentile_feats.append(int(fk[1:]))

    if percentile_feats:
        if weights is None:
            ps = np.percentile(data, percentile_feats, axis=axis)
        else:
            ps = np.percentile(data, percentile_feats, axis=axis,
                method="inverted_cdf", weights=weights)

        ps = np.split(ps, len(percentile_feats), axis=0)
        for fk,p in zip(percentile_feats, ps):
            farrs[f"p{fk:02}"] = p[0]

    for fk in derived_feats:
        if fk == "max-min":
            farrs[fk] = farrs["max"] - farrs["min"]
        elif fk == "p95-05":
            farrs[fk] = farrs["p95"] - farrs["p05"]
        elif fk == "p90-10":
            farrs[fk] = farrs["p90"] - farrs["p10"]
        elif fk == "p75-25":
            farrs[fk] = farrs["p75"] - farrs["p25"]

    return {fk:x for fk,x in farrs.items() if fk in get_feats}

def mp_extract_region_eto(args):
    return args,extract_region_eto(**args)

def extract_region_eto(
        date, nc_source_path, zarr_out_path, zarr_region_path,
        overwrite_existing=False,
        ):
    """
    High-level method extracting ensemble data for an already-initialized
    region, then statistically aggregating ensemble members per the config
    at the native (pixel) scale, and for each pgroup.

    adds new arrays under the region sub-path data/<date_string>:

    - eto_spatial: (metric, vtime, lat, lon) < uint16 >
    - eto_temporal: (lat, lon, metric, vtime) < float16 >

    and under each pgroup's sub-path: data/<date_string>:

    - eto: (polygon, metric, vtime) < float16 >
    """
    pgroups = config.frontend["labels"]["pgroups"]
    rmetrics = config.frontend["labels"]["metrics_raster"]
    pmetrics = config.frontend["labels"]["metrics_pgroup"]
    norms = config.frontend["norm_bounds"]
    nmask = config.frontend["mask_val"]
    nres = config.frontend["norm_resolution"]
    nvtimes = config.frontend["nvtimes"]
    dep_rules = config.backend["dependent_metrics"]
    tsss = config.backend["temporal_shard_spatial_shape"]
    tcss = config.backend["temporal_chunk_spatial_shape"]

    dstr = date.strftime("%Y%m%d")

    ## load the relevant information from the zarr store
    zgrp = zarr.open(zarr_out_path, path=zarr_region_path, mode="a")
    pslices = zgrp.attrs["pgroup_slices"]
    ((ixy0, ixyf), (ixx0, ixxf)) = zgrp.attrs["source_slice"]
    m_valid = zgrp["m_valid"][...]
    ixmap = zgrp["index_map"][...][:,m_valid]

    ## open and subset the source file to the regional subdomain
    ds = nc.Dataset(nc_source_path, "r")
    ## convert mm/day to in/day
    eto_source = ds["ETo"][:,:,::-1,:][..., ixy0:ixyf, ixx0:ixxf] / 25.4
    assert eto_source.shape[0] == nvtimes

    get_raster = True
    if not "data" in zgrp.keys():
        zgrp.create_group("data")
    if dstr in zgrp["data"].keys():
        if "eto_temporal" in zgrp[f"/data/{dstr}"].keys():
            if overwrite_existing:
                del zgrp[f"/data/{dstr}"]
            else:
                get_raster = False

    eto = np.full((*eto_source.shape[:2], *m_valid.shape), np.nan)
    eto[..., m_valid] = eto_source[..., ixmap[0], ixmap[1]]
    del eto_source

    if get_raster:
        zgrp["data"].create_group(dstr)
        ## hard-code chunking each metric separately
        zgrp[f"/data/{dstr}"].create_array(
            "eto_spatial",
            shape=(len(rmetrics), eto.shape[0], *m_valid.shape),
            chunks=(1, eto.shape[0], *m_valid.shape),
            shards=(len(rmetrics), eto.shape[0], *m_valid.shape),
            dtype=np.uint16,
            )

        rdata = evaluate_feats(eto, rmetrics, dep_rules, axis=1)

        zgrp[f"/data/{dstr}/eto_spatial"][...] = np.stack([
            norm_uint16(
                x=rdata[fk],
                nmin=norms["eto"][fk][0],
                nmax=norms["eto"][fk][1],
                nres=nres,
                mask_val=nmask,
                )
            for fk in rmetrics
            ], axis=0)

        zgrp[f"/data/{dstr}"].create_array(
            "eto_temporal",
            shape=(*m_valid.shape, len(pmetrics), eto.shape[0]),
            chunks=(*tcss, len(pmetrics), eto.shape[0]),
            shards=(*tsss, len(pmetrics), eto.shape[0]),
            dtype=np.float16,
            )
        pdata = evaluate_feats(eto, pmetrics, dep_rules, axis=1)
        zgrp[f"/data/{dstr}/eto_temporal"][...] = np.stack([
            pdata[fk].astype(np.float16) for fk in pmetrics
            ], axis=0).transpose(2,3,0,1)

    for pk in pgroups:
        if pk not in zgrp["pgroups"].keys():
            print("pgroup not initialized", pk)
            continue

        if "data" not in zgrp[f"/pgroups/{pk}"].keys():
            zgrp[f"/pgroups/{pk}"].create_group("data")
        if dstr not in zgrp[f"/pgroups/{pk}/data"].keys():
            zgrp[f"/pgroups/{pk}/data"].create_group(dstr)
        if "eto" in zgrp[f"/pgroups/{pk}/data/{dstr}"].keys():
            if overwrite_existing:
                del zgrp[f"/pgroups/{pk}/data/{dstr}/eto"]
            else:
                continue

        ps = pslices[pk]
        zgrp[f"/pgroups/{pk}/data/{dstr}"].create_array(
            "eto",
            shape=(len(pslices[pk]), len(pmetrics), nvtimes),
            dtype=np.float16,
            )
        frac = zgrp[f"/pgroups/{pk}/fracs"][...]
        parr = np.full((len(ps), len(pmetrics), nvtimes), np.nan)
        assert len(ps) == frac.shape[0]
        for i in range(len(ps)):
            sy,sx = ps[i]
            sub_frac = frac[i, :sy[1]-sy[0], :sx[1]-sx[0]]
            m_frac = (sub_frac != 0)
            if np.count_nonzero(m_frac) == 0:
                continue
            w = sub_frac[m_frac]
            w = np.tile(w, eto.shape[1])
            ## px should be shaped (vtime, ens, pixel)
            px = eto[..., slice(*sy), slice(*sx)][..., m_frac]
            px = px.reshape((px.shape[0], -1)).T.astype(np.float32)
            pdict = evaluate_feats(
                data=px,
                get_feats=pmetrics,
                dependency_rules=dep_rules,
                weights=w,
                axis=0,
                )
            ## result is (poly, metric, vtime)
            parr[i] = np.stack([
                pdict[fk].astype(np.float16)
                for fk in pmetrics
                ], axis=0)
        zgrp[f"/pgroups/{pk}/data/{dstr}/eto"][...] = parr

if __name__=="__main__":
    #source_dir = Path("/rhome/mdodson/ETo-Viewer/data/source")
    #out_zarr_dir = Path("/rhome/mdodson/ETo-Viewer/data/store")
    #vector_dir = Path("/rhome/mdodson/ETo-Viewer/data/vector")
    out_zarr_dir = Path("data/store")
    source_dir = Path("data/source")
    vector_dir = Path("data/vector")

    out_zarr_path = out_zarr_dir.joinpath("eto-forecast-dashboard.zarr")
    domain_template = "domain_{domain}.geojson"
    source_template = "eto_forecast_gridmet_deg04_%Y-%m-%dT00.nc"

    date_start = date(2026, 8, 27)
    date_end = date(2026, 8, 27)

    overwrite_existing = True

    nworkers = 4

    """ ------------( end normal configuration )------------ """

    get_dates = [
        date_start + timedelta(days=dt)
        for dt in range((date_end - date_start).days + 1)
        ]
    source_files = [
        source_dir.joinpath(d.strftime(source_template))
        for d in get_dates
        ]

    for sf in source_files:
        assert sf.exists(), f"source file not found: {sf.as_posix()}"

    ## extract and rescale raster data by region
    args = []
    zgrp_root = zarr.open(out_zarr_path, mode="a")
    for r in config.frontend["labels"]["regions"]:
        for d,sf in zip(get_dates, source_files):
            args.append({
                "date":d,
                "nc_source_path":sf,
                "zarr_out_path":out_zarr_path,
                "zarr_region_path":f"/regions/{r}",
                "overwrite_existing":overwrite_existing,
                })

    if "vtimes" not in zgrp_root.keys():
        zgrp_root.create_group("vtimes")
    for d in get_dates:
        dstr = d.strftime("%Y%m%d")
        if dstr not in zgrp_root["vtimes"].keys():
            vtimes = np.asarray([
                d + timedelta(days=i)
                for i in range(config.frontend["nvtimes"])
                ], dtype="M8[ns]")
            zgrp_root["vtimes"].create_array(dstr, data=vtimes)

    with mp.Pool(nworkers) as pool:
        for a,_ in pool.imap_unordered(mp_extract_region_eto, args):
            print(
                "got:",
                f"{a['zarr_out_path'].name}",
                f"{a['zarr_region_path']}",
                f"{a['date']}",
                )
    print("finished")
