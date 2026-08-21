import numpy as np
import zarr
import multiprocessing  as mp
import netCDF4 as nc
from datetime import date,datetime,timedelta
from pathlib import Path

import config

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
        if fk == "p90-10":
            farrs[fk] = farrs["p90"] - farrs["p10"]
        if fk == "p75-25":
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

    adds new arrays under the region sub-path data/eto/<date_string>:

    - eto: (metric, vtime, lat, lon) < uint16 >
    - vtime: (vtime,) < M8[ns] >

    and under each pgroup's sub-path: data/eto/<date_string>:

    - eto: (polygon, metric, vtime) < float16 >
    """
    ds = nc.Dataset(nc_source_path, "r")
    times = np.asarray([
        date + timedelta(days=int(t)) for t in ds["time"][...]
        ], dtype="M8[ns]")
    eto_source = ds["ETo"][...] / 25.4 ## convert mm/day to in/day

    pgroups = config.frontend["pgroups"]
    rmetrics = config.frontend["metrics_raster"]
    pmetrics = config.frontend["metrics_pgroup"]
    norms = config.frontend["norm_bounds"]
    dep_rules = config.backend["dependent_metrics"]

    zgrp = zarr.open(zarr_out_path, path=zarr_region_path, mode="a")
    m_valid = zgrp["m_valid"][...]
    ixmap = zgrp["index_map"][...][:,m_valid]
    pslices = zgrp.attrs["pgroup_slices"]

    get_raster = True
    if not "data" in zgrp.keys():
        zgrp.create_group("data")
    if "eto" in zgrp["data"].keys():
        if overwrite_existing:
            del zgrp["/data/eto"]
        else:
            get_raster = False

    if get_raster:
        ## hard-code chunking each metric separately
        zgrp["data"].create_array(
            "eto",
            shape=(len(rmetrics), eto_source.shape[0], *m_valid.shape),
            chunks=(1, eto_source.shape[0], *m_valid.shape),
            shards=(len(rmetrics), eto_source.shape[0], *m_valid.shape),
            dtype=np.float32,
            )
        yixs,xixs = ixmap[0],ixmap[1]
        eto = np.full((*eto_source.shape[:2], *m_valid.shape), np.nan)
        eto[..., m_valid] = eto_source[..., yixs, xixs]
        del eto_source

        rdata = evaluate_feats(eto, rmetrics, dep_rules, axis=1)

        print("got raster")
        zgrp["/data/eto"][...] = np.stack(
            [rdata[fk] for fk in rmetrics],
            axis=0,
            )


    for pk in pgroups:
        if pk not in zgrp["pgroups"].keys():
            print("pgroup not initialized", pk)
            continue

        if "data" not in zgrp[f"/pgroups/{pk}"].keys():
            zgrp[f"/pgroups/{pk}"].create_group("data")
        get_pgroup = True
        if "eto" in zgrp[f"/pgroups/{pk}/data"].keys():
            if overwrite_existing:
                del zgrp[f"/pgroups/{pk}/data/eto"]
            else:
                get_pgroup = False

        ps = pslices[pk]
        if get_pgroup:
            zgrp[f"/pgroups/{pk}/data"].create_array(
                "eto",
                shape=(len(pslices[pk]), len(pmetrics), times.size),
                dtype=np.float16,
                )

        frac = zgrp[f"/pgroups/{pk}/fracs"][...]
        parr = np.full((len(ps), len(pmetrics), times.size), np.nan)
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
            parr[i] = np.stack([pdict[fk] for fk in pmetrics], axis=0)
        print(f"got pgroup {pk}")
        zgrp[f"/pgroups/{pk}/data/eto"][...] = parr.astype(np.float16)


if __name__=="__main__":
    source_dir = Path("/rhome/mdodson/ETo-Viewer/data/source")
    out_zarr_dir = Path("/rhome/mdodson/ETo-Viewer/data/store")
    vector_dir = Path("/rhome/mdodson/ETo-Viewer/data/vector")

    out_zarr_path = out_zarr_dir.joinpath("eto-forecast_new.zarr")
    domain_template = "domain_{domain}.geojson"
    source_template = "eto_forecast_gridmet_deg04_%Y-%m-%dT00.nc"

    date_start = date(2026, 8, 17)
    date_end = date(2026, 8, 17)

    overwrite_existing = True

    nworkers = 8

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
    for r in config.frontend["regions"]:
        for d,sf in zip(get_dates, source_files):
            args.append({
                "date":d,
                "nc_source_path":sf,
                "zarr_out_path":out_zarr_path,
                "zarr_region_path":f"/regions/{r}",
                "overwrite_existing":overwrite_existing,
                })

    with mp.Pool(nworkers) as pool:
        for a,_ in pool.imap_unordered(mp_extract_region_eto, args):
            print(
                "got:",
                f"{a['zarr_out_path'].name}",
                f"{a['zarr_region_path']}",
                f"{a['date']}",
                )
