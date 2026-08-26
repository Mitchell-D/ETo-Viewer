import zarr
import numpy as np
import geopandas as gpd
from pathlib import Path
from shapely.geometry import Point
from shapely import contains_xy

import config


def poly_to_pixels(polys, width, height, lon_range, lat_range):
    """
    Assign each pixel the index of the polygon containing its center.
    """
    lon_min,lon_max = lon_range
    lat_min,lat_max = lat_range

    lons = lon_min + (np.arange(width) + 0.5) * (lon_max - lon_min) / width
    lats = lat_max - (np.arange(height) + 0.5) * (lat_max - lat_min) / height
    lon_grid, lat_grid = np.meshgrid(lons, lats)

    ## fill pixels belonging to each polygon.
    result = np.full((height, width), -1, dtype=np.int32)
    for i, polygon in enumerate(polys):
        mask = contains_xy(polygon, lon_grid, lat_grid)
        result[mask] = i

    return result

if __name__=="__main__":
    vec_dir = Path("data/vector/")
    domain_template = "domain_{region}.geojson"
    zarr_out_path = Path("data/store/eto-forecast.zarr")
    lat_range = [24.3,50.]
    lon_range = [-125.1, -66.5]
    scale = 6
    height = int((lat_range[1]-lat_range[0])*scale)
    width = int((lon_range[1]-lon_range[0])*scale)
    border_color = np.asarray([[[10, 163, 86, 255]]]) ## RGBA
    border_fill = np.asarray([[[0, 0, 0, 0]]]) ## RGBA

    replace_existing = True

    """ ------------( end normal configuration )------------ """

    zgrp = zarr.open(zarr_out_path, mode="a")

    if "region_map" in zgrp.keys():
        if not replace_existing:
            raise ValueError(
                "'region_map' already exists in:",
                zarr_out_path.as_posix()
                )
        else:
            del zgrp["region_map"]

    polys = []
    for rk in config.frontend["labels"]["regions"]:
        gjpath = vec_dir.joinpath(domain_template.format(region=rk))
        polys.append(gpd.read_file(gjpath).geometry[0])

    raster = poly_to_pixels(
        polys=polys,
        width=width,
        height=height,
        lon_range=lon_range,
        lat_range=lat_range,
        ).astype(np.uint8)

    ny,nx = raster.shape
    m_borders = np.full((ny, nx), False)
    m_borders[:-1] = np.diff(raster, axis=0) != 0
    m_borders[:,:-1] |= np.diff(raster, axis=1) != 0
    m_borders[1:, 1:] |= m_borders[:-1, :-1]
    borders = np.where(
        m_borders[..., np.newaxis],
        border_color,
        border_fill,
        ).astype(np.uint8)

    zgrp.create_group("region_map")
    zgrp["region_map"].create_array("raster", data=raster)
    zgrp["region_map"].create_array("borders", data=borders)
    zgrp["region_map"].attrs.update({"width":nx, "height":ny});
