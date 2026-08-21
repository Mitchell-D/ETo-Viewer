import zarr
import geopandas as gpd
import rasterio as rio
import shapely
import numpy as np
import pyproj
import netCDF4 as nc
from affine import Affine
from rasterio.warp import calculate_default_transform
from rasterio.transform import array_bounds
from rasterio.warp import reproject, Resampling
from rasterio.features import rasterize
from pathlib import Path
from datetime import date

import config

def get_region_mapping(
        domain_polygon, lat, lon, crs_out, m_valid=None, degree_buffer=0.1,
        mask_oversample_factor=16, mask_coverage_cutoff=.3,
        ):
    """
    Given a shapely polygon depicting the outer boundary of a subdomain,
    source array coordinates, and a valid pixel mask, develop an array matching
    the resampled output array shape that assigns pixel indeces with respect
    to the source array.
    """
    ## get bounding box around the domain polygon
    lon_min, lat_min, lon_max, lat_max = domain_polygon.bounds
    lat_min -= degree_buffer
    lon_min -= degree_buffer
    lat_max += degree_buffer
    lon_max += degree_buffer

    assert lat.ndim == 1
    assert lon.ndim == 1
    if m_valid is None:
        m_valid = np.full((lat.size, lon.size), True)
    assert (lat.size, lon.size) == m_valid.shape, \
        f"shapes don't match: {lat.shape=} {lon.shape=}, {m_valid.shape=}"

    #'''
    yix0 = int(np.argmin(np.abs(lat-lat_max)))
    yixf = int(np.argmin(np.abs(lat-lat_min)))
    xix0 = int(np.argmin(np.abs(lon-lon_min)))
    xixf = int(np.argmin(np.abs(lon-lon_max)))
    lat = lat[yix0:yixf]
    lon = lon[xix0:xixf]
    m_valid = m_valid[yix0:yixf,xix0:xixf]
    #'''

    assert lat.size > 1, f"polygon out of range of {lat_min} - {lat_max}"
    assert lon.size > 1, f"polygon out of range of {lon_min} - {lon_max}"

    geo_ref_src = {
        "crs":"EPSG:4326",
        "height":lat.size,
        "width":lon.size,
        }

    ## determine the input transform
    dlon = np.abs(lon[1]-lon[0])
    dlat = np.abs(lat[1]-lat[0])
    geo_ref_src["transform"] = rio.transform.from_bounds(
        lon.min() - dlon / 2,
        lat.min() - dlat / 2,
        lon.max() + dlon / 2,
        lat.max() + dlat / 2,
        geo_ref_src["width"],
        geo_ref_src["height"],
        )

    ## determine the output dimensions and transform
    t_out,w_out,h_out = calculate_default_transform(
        geo_ref_src["crs"],
        crs_out,
        geo_ref_src["width"],
        geo_ref_src["height"],
        *array_bounds(
            geo_ref_src["height"],
            geo_ref_src["width"],
            geo_ref_src["transform"],
            ),
        )

    geo_ref_out = {
        "crs":crs_out,
        "width":w_out,
        "height":h_out,
        "transform":t_out,
        }

    ## determine the output lat/lon coordinate bounds
    lon0_out,lat0_out,lonf_out,latf_out = rio.warp.transform_bounds(
        geo_ref_out["crs"],
        "EPSG:4326",
        *rio.transform.array_bounds(
            geo_ref_out["height"],
            geo_ref_out["width"],
            geo_ref_out["transform"]
            ),
        )
    coord_range_out = ((lat0_out, latf_out), (lon0_out, lonf_out))

    ## determine an index mapping from the source on the destination grid
    j_out,i_out = np.meshgrid(
        np.arange(h_out),
        np.arange(w_out),
        indexing="ij"
        )
    ## convert from indices to spatial coordinates
    x_out,y_out = map(np.asarray, rio.transform.xy(t_out, j_out, i_out))
    ## transform the spatial coordinates to the source domain
    x_src,y_src = rio.warp.transform(
        geo_ref_out["crs"],
        geo_ref_src["crs"],
        x_out,
        y_out,
        )
    ## convert coordinates to spatial indices on the source domain
    j_src,i_src = rio.transform.rowcol(
        geo_ref_src["transform"],
        x_src,
        y_src,
        )
    ## reshape back to the destination grid dimensions
    j_src = np.asarray(j_src).reshape(h_out, w_out)
    i_src = np.asarray(i_src).reshape(h_out, w_out)

    ## develop a latlon array and boolean mask for the destination grid
    lon_out,lat_out = rio.warp.transform(
        geo_ref_out["crs"],
        "EPSG:4326", ## lat/lon coordinates
        x_out.ravel(),
        y_out.ravel(),
        )
    lon_out = np.asarray(lon_out).reshape(h_out, w_out)
    lat_out = np.asarray(lat_out).reshape(h_out, w_out)

    ## calculate a boolean mask on a super-resolution array given the threshold
    transformer = pyproj.Transformer.from_crs(
        pyproj.CRS("EPSG:4326"),
        pyproj.CRS(geo_ref_out["crs"]),
        always_xy=True,
        ).transform
    ppoly = shapely.ops.transform(transformer, domain_polygon)
    fine_mask = rasterize(
        [(ppoly, 1)],
        out_shape=(h_out*mask_oversample_factor, w_out*mask_oversample_factor),
        transform=geo_ref_out["transform"] * Affine.scale(
            1/mask_oversample_factor, 1/mask_oversample_factor),
        fill=0,
        default_value=1,
        dtype=np.uint8
        )
    frac = fine_mask.reshape(
            h_out,
            mask_oversample_factor,
            w_out,
            mask_oversample_factor,
            ).mean(axis=(1,3))
    m_inside = frac >= mask_coverage_cutoff
    m_all_valid = np.copy(m_inside)

    for j,i in np.ndindex(m_inside.shape):
        if not m_inside[j,i]:
            continue
        if not m_valid[j_src[j,i], i_src[j,i]]:
            m_all_valid[j,i] = False

    geo_ref_src["transform"] = geo_ref_src["transform"].to_gdal()
    geo_ref_out["transform"] = geo_ref_out["transform"].to_gdal()
    return coord_range_out, \
        (geo_ref_src,geo_ref_out), \
        np.stack((j_src,i_src), axis=0), \
        (lat_out, lon_out), \
        m_all_valid

def polygon_fraction_subgrids(geo_ref_src, m_valid, multipolygon,
        mask_oversample_factor=16):
    """
    Compute per-polygon fractional coverage of valid raster pixels.

    Fractional coverage is computed by supersampling each source pixel and
    rasterizing the polygon at the supersampled resolution. ``oversample``
    controls the approximation accuracy.

    :@param geo_ref_src: dict with source crs, width, and height
    :@param m_valid: bool array assigning invalid pixels to False
    :@param multipolygon: geopandas datafram of polygon features

    :@return: 2-tuple (fractions, slices) where fractions is a list of
        2d arrays corresponding to the multipolygon rows clipped to the
        smallest bounding rectangle containing all non-zero coverage pixels,
        and slices is a list of 2-tuples of int (start_ix, end_ix+1)
        indicating the boundaries of the corresponding fractions array with
        respect to the source domain
    """
    height = geo_ref_src["height"]
    width = geo_ref_src["width"]
    if m_valid.shape != (height, width):
        raise ValueError(
            f"m_valid must have shape {(height, width)}, got {m_valid.shape}"
            )

    if multipolygon.crs != geo_ref_src["crs"]:
        multipolygon = multipolygon.to_crs(geo_ref_src["crs"])

    src_t = Affine.from_gdal(*geo_ref_src["transform"])

    ## rasterize all features at once with unique integer feature ids starting
    ## with 1 since 0 is the fill value.
    shapes = [
        (shapely.geometry.mapping(geom), i + 1)
        for i, geom in enumerate(multipolygon.geometry)
        if geom is not None and not geom.is_empty
        ]

    if not shapes:
        raise ValueError("no non-empty features found")

    ## oversample the raster
    hi_height = height * mask_oversample_factor
    hi_width = width * mask_oversample_factor
    hi_t = src_t * Affine.scale(
        1.0 / mask_oversample_factor,
        1.0 / mask_oversample_factor,
        )
    labels = rasterize(
        shapes,
        out_shape=(hi_height, hi_width),
        transform=hi_t,
        fill=0,
        dtype=np.int32,
        )

    ## match m_valid to the high resolution array
    m_valid_hi = np.repeat(
        np.repeat(m_valid, mask_oversample_factor, axis=0),
        mask_oversample_factor,
        axis=1,
        )

    fractions = []
    slices = []
    for feature_id in range(1, len(multipolygon)+1):
        covered = (labels == feature_id) & m_valid_hi

        ## count covered supersamples in each source pixel
        coverage = covered.reshape(
            height, mask_oversample_factor,
            width, mask_oversample_factor,
            ).sum(axis=(1, 3))

        ## normalize to [0,1]
        coverage = coverage.astype(np.float32) / mask_oversample_factor**2
        coverage[~m_valid] = 0.0

        rows,cols = np.nonzero(coverage > 0)
        if rows.size == 0:
            print(f"zero coverage for {feature_id}")
            fractions.append(np.empty((0, 0), dtype=np.float16))
            slices.append(((0, 0), (0, 0)))
            continue

        ## determine the minimum bounding box of nonzero fraciton pixels
        yix0,yixf = int(rows.min()), int(rows.max() + 1)
        xix0,xixf = int(cols.min()), int(cols.max() + 1)
        fractions.append(
            coverage[yix0:yixf, xix0:xixf].astype(np.float16, copy=False)
            )
        slices.append(((yix0, yixf), (xix0, xixf)))

    return fractions, slices

if __name__=="__main__":
    source_dir = Path("/rhome/mdodson/ETo-Viewer/data/source")
    out_zarr_dir = Path("/rhome/mdodson/ETo-Viewer/data/store")
    vector_dir = Path("/rhome/mdodson/ETo-Viewer/data/vector")

    out_zarr_path = out_zarr_dir.joinpath("eto-forecast.zarr")
    domain_template = "domain_{domain}.geojson"
    sample_file = source_dir.joinpath(
        "eto_forecast_gridmet_deg04_2026-08-17T00.nc")

    """ ------------( end normal configuration )------------ """

    domains = {}
    pgroups = {}
    for r in config.frontend["labels"]["regions"]:
        d = vector_dir.joinpath(domain_template.format(domain=r))
        assert d.exists(), f"domain file doesn't exist: {d.as_posix()}"
        domains[r] = d
        pgroups[r] = {}
        for pg in config.frontend["labels"]["pgroups"]:
            pgf = vector_dir.joinpath(f"{pg}_{r}.geojson")
            assert pgf.exists, f"pgroup file doesn't exist: {pgf.as_posix()}"
            pgroups[r][pg] = pgf

    ds = nc.Dataset(sample_file, "r")
    lat = ds["latitude"][...][::-1]
    lon = ds["longitude"][...]
    m_valid = ~ds["ETo"][0,0].mask[::-1]

    assert not out_zarr_path.exists(), f"exists: {out_zarr_path.as_posix()}"

    zgrp = zarr.open(out_zarr_path, mode="w")
    zgrp.create_group("regions")
    for r,d in domains.items():
        print(f"getting {r}")
        zgrp["regions"].create_group(r)
        poly = gpd.read_file(d).geometry[0]
        crout,(grs,gro),ixmap,(lat_out,lon_out),m_sub = get_region_mapping(
            domain_polygon=poly,
            lat=lat,
            lon=lon,
            crs_out=config.backend["crs_out"],
            m_valid=m_valid,
            degree_buffer=config.backend["region_degree_buffer"],
            mask_oversample_factor=config.backend["oversample_factor"],
            mask_coverage_cutoff=config.backend["region_mask_coverage_cutoff"],
            )
        print(crout, m_sub.shape, np.count_nonzero(m_sub))
        zgrp[f"/regions/{r}"].create_array("m_valid", data=m_sub)
        zgrp[f"/regions/{r}"].create_array("lat", data=lat_out)
        zgrp[f"/regions/{r}"].create_array("lon", data=lon_out)
        zgrp[f"/regions/{r}"].create_array("index_map", data=ixmap)
        zgrp[f"/regions/{r}"].attrs.update({
            "coord_range":crout,
            "geo_ref_src":grs,
            "geo_ref_out":gro,
            })

        zgrp[f"/regions/{r}"].create_group("pgroups")

        pgslcs = {}
        for pg in config.frontend["labels"]["pgroups"]:
            print(f"getting {r} {pg}")
            zgrp[f"/regions/{r}/pgroups"].create_group(pg)
            pgdf = gpd.read_file(pgroups[r][pg])
            if pgdf.geometry.is_empty.any():
                raise ValueError(f"empty geometries in {pgroups[r][pg]}")
            fracs,slices = polygon_fraction_subgrids(
                geo_ref_src=gro,
                m_valid=m_sub,
                multipolygon=pgdf,
                mask_oversample_factor=config.backend["oversample_factor"],
                )
            pgslcs[pg] = slices
            maxy,maxx = -1,-1
            for ys,xs in slices:
                if ys[1]-ys[0] > maxy:
                    maxy = ys[1]-ys[0]
                if xs[1]-xs[0] > maxx:
                    maxx = xs[1]-xs[0]

            zgrp[f"/regions/{r}/pgroups/{pg}"].create_array(
                "fracs",
                shape=(len(slices), maxy, maxx),
                chunks=(len(slices), maxy, maxx),
                shards=(len(slices), maxy, maxx),
                dtype=np.float16,
                )
            fk = f"/regions/{r}/pgroups/{pg}/fracs"
            for i,(ys,xs) in enumerate(slices):
                tmps = (i, slice(0, ys[1]-ys[0]))
                zgrp[fk][i, 0:ys[1]-ys[0], 0:xs[1]-xs[0]] = fracs[i]
        zgrp[f"/regions/{r}"].attrs.update({"pgroup_slices":pgslcs})
    print("finished")
