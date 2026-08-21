import numpy as np
import netCDF4 as nc
import matplotlib.pyplot as plt
import matplotlib.pyplot as plt
import matplotlib.colors as pltc
import matplotlib.patches as pltp
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from pathlib import Path

def plot_geo_raster(data, lats, lons, shapes=None,
    geo_bounds=None, latlon_ticks=True,
    out_path=None, cbar_ticks=False, cmap=None,
    show=False, plot_spec={}):
    """
    Plots a map from a single-channel raster.

    :@param data: 2D numpy array of scalar values
    :@param lats: 1D array of latitudes corresponding to rows in `data`
    :@param lons: 1D array of longitudes corresponding to columns in `data`
    :@param cmap: matplotlib colormap name or Colormap object
    """
    ps = {
        "xlabel":"", "ylabel":"", "title":"", "dpi":80, "norm":None,
        "figsize":(11,9), "legend_ncols":1, "line_opacity":1,
        "cmap":"magma", "label_size":14, "title_size":20, "cbar_disable":True,
        "cartopy_feats":["land", "borders", "states"],
        "shape_params":{},
        }
    ps.update(plot_spec)
    map_crs = plot_spec.get("projection", ccrs.PlateCarree())
    fig, ax = plt.subplots(
        subplot_kw={"projection": map_crs}
        )

    if shapes:
        tmp_fc = ps.get("shape_params", {}).get("facecolor", None)
        tmp_ec = ps.get("shape_params", {}).get("edgecolor", "white")
        tmp_lw = ps.get("shape_params", {}).get("linewidth", 1)
        tmp_ls = ps.get("shape_params", {}).get("linestyle", "solid")
        tmp_zo = ps.get("shape_params", {}).get("zorder", 10)
        tmp_aa = ps.get("shape_params", {}).get("alpha", .5)
        if not isinstance(tmp_fc, (list, tuple)):
            tmp_fc = [tmp_fc for i in range(len(shapes))]
        if not isinstance(tmp_ec, (list, tuple)):
            tmp_ec = [tmp_ec for i in range(len(shapes))]
        if not isinstance(tmp_lw, (list, tuple, np.ndarray)):
            tmp_lw = [tmp_lw for i in range(len(shapes))]
        if not isinstance(tmp_ls, (list, tuple)):
            tmp_ls = [tmp_ls for i in range(len(shapes))]
        if not isinstance(tmp_zo, (list, tuple)):
            tmp_zo = [tmp_zo for i in range(len(shapes))]
        if not isinstance(tmp_aa, (list, tuple, np.ndarray)):
            tmp_aa = [tmp_aa for i in range(len(shapes))]
        for i,s in enumerate(shapes):
            geom = s["geometry"]
            print(f"{tmp_fc[i]=}")
            if geom["type"] == "Polygon":
                for rings in geom["coordinates"]:
                    # expects an nx2 array or list of (x, y) tuples
                    poly_patch = pltp.Polygon(
                        s,
                        closed=True,
                        facecolor=tmp_fc[i],
                        edgecolor=tmp_ec[i],
                        linewidth=tmp_lw[i],
                        linestyle=tmp_ls[i],
                        zorder=tmp_zo[i],
                        alpha=tmp_aa[i],
                        )
                    ax.add_patch(poly_patch)

            elif geom["type"] == "MultiPolygon":
                for polygon in geom["coordinates"]:
                    for p in polygon:
                        poly_patch = pltp.Polygon(
                            p,
                            closed=True,
                            facecolor=tmp_fc[i],
                            edgecolor=tmp_ec[i],
                            linewidth=tmp_lw[i],
                            linestyle=tmp_ls[i],
                            zorder=tmp_zo[i],
                            alpha=tmp_aa[i],
                            )
                        ax.add_patch(poly_patch)

    if "land" in ps.get("cartopy_feats"):
        ax.add_feature(cfeature.LAND)

    if "borders" in ps.get("cartopy_feats"):
        ax.add_feature(
                cfeature.BORDERS,
                linestyle=ps.get("border_style", "-"),
                linewidth=ps.get("border_linewidth", 2),
                edgecolor=ps.get("border_color", "black"),
                )

    if "states" in ps.get("cartopy_feats"):
        ax.add_feature(
                cfeature.STATES,
                linestyle=ps.get("border_style", "-"),
                linewidth=ps.get("border_linewidth", 2),
                edgecolor=ps.get("border_color", "black"),
                )

    if geo_bounds is None:
        geo_bounds = [
            np.amin(lons), np.amax(lons),
            np.amin(lats), np.amax(lats)
            ]
    lower_left = map_crs.transform_point(
        geo_bounds[0], geo_bounds[2], src_crs=ccrs.PlateCarree())
    upper_right = map_crs.transform_point(
        geo_bounds[1], geo_bounds[3], src_crs=ccrs.PlateCarree())

    proj_ext = [lower_left[0], upper_right[0], lower_left[1], upper_right[1]]

    ax.set_extent(proj_ext, crs=map_crs)

    if isinstance(data, np.ma.MaskedArray):
        plot_data = data.filled(np.nan)
    else:
        plot_data = np.asarray(data, dtype=float).copy()

    plot_data[~np.isfinite(plot_data)] = np.nan

    if cmap is None:
        cmap = ps.get("cmap", "viridis")

    im = ax.imshow(
            plot_data,
            origin=ps.get("origin", "upper"),
            cmap=cmap,
            norm=ps.get("norm"),
            vmin=ps.get("vmin"),
            vmax=ps.get("vmax"),
            extent=proj_ext,
            interpolation=ps.get("interpolation"),
            )

    if latlon_ticks:
        lonmin,lonmax,latmin,latmax = geo_bounds
        frq = ps.get("tick_frequency", 1)

        ax.set_yticks(
                np.linspace(latmin, latmax, plot_data.shape[0])[::frq],
                crs=ccrs.PlateCarree())

        ax.set_xticks(
                np.linspace(lonmin, lonmax, plot_data.shape[1])[::frq],
                crs=ccrs.PlateCarree())

        lon_formatter = LongitudeFormatter(zero_direction_label=True)
        lat_formatter = LatitudeFormatter()
        ax.xaxis.set_major_formatter(lon_formatter)
        ax.yaxis.set_major_formatter(lat_formatter)
        ax.tick_params(rotation=ps.get("tick_rotation", 0))

    if not ps.get("cbar_disable"):
        cbar = plt.colorbar(
                im, ax=ax,
                orientation=ps.get("cbar_orient", "vertical"),
                pad=ps.get("cbar_pad", 0.05),
                shrink=ps.get("cbar_shrink", 1.)
                )

        if cbar_ticks not in (False, None):
            cbar.set_ticks(cbar_ticks)

        cbar.ax.tick_params(
                rotation=ps.get("cbar_tick_rotation", 0))
        cbar.ax.tick_params(
                labelsize=ps.get("cbar_fontsize", 14))
        cbar.set_label(ps.get("cbar_label"))

    ax.set_title(
            ps.get("title", ""),
            fontsize=ps.get("title_fontsize", 18))

    if out_path is not None:
        fig.set_size_inches(*ps.get("figsize"))
        fig.savefig(
            out_path.as_posix(),
            bbox_inches="tight",
            dpi=ps.get("dpi", 100),
            )

    if show:
        plt.show()

    plt.close()
    return

def get_hist(x, nmin, nmax, resolution):
    vals,counts = np.unique(
        np.round(
            np.clip((x[np.isfinite(x)]-nmin)/(nmax-nmin),0,1) \
            * (resolution-1)
            ).astype(np.uint64).ravel(),
        return_counts=True,
        )
    coords = np.linspace(nmin, nmax, resolution)
    c = np.asarray([coords[v] for v in vals])
    return c,counts

def plot_line(coords, vals, title, fig_path):
    fig,ax = plt.subplots()
    ax.plot(coords, vals, color="black", linewidth=2)
    ax.set_title(title)
    fig.savefig(fig_path)

if __name__=="__main__":
    source_dir = Path("data/source/")
    source_path = source_dir.joinpath(
        "eto_forecast_gridmet_deg04_2026-08-17T00.nc")
    fig_dir = Path("data/figures")

    ds = nc.Dataset(source_path, "r")

    plot_mean = False
    plot_mean_ixs = [0]

    plot_hist = True
    hres = 512

    if plot_mean:
        lat,lon = np.meshgrid(
            ds["latitude"][...],
            ds["longitude"][...],
            indexing="ij",
            )
        for ix in plot_mean_ixs:
            mean = np.average(ds["ETo"][0], axis=0)[::-1]
            plot_geo_raster(
                data=mean,
                lats=lat[::-1],
                lons=lon[::-1],
                shapes=None,
                geo_bounds=None,
                latlon_ticks=False,
                out_path=fig_dir.joinpath(source_path.stem+f"_mean_{ix}.png"),
                cbar_ticks=False,
                cmap=None,
                show=False,
                plot_spec={}
                )

    if plot_hist:
        eto = ds["ETo"][...]
        hmin = np.amin(eto)
        hmax = np.amax(eto)
        c,v = get_hist(eto, hmin, hmax, hres)
        plot_line(c, v, "ETo Distribution", fig_dir.joinpath("eto_dist.png"))

    print("finished")
