frontend = {
    "labels":{
        "feats":["eto"],

        "metrics_raster":[
            "min", "max", "mean", "stddev",
            "p10", "p25", "p50", "p75", "p90",
            #"max-min", "p95-05", "p90-10", "p75-25",
            "max-min", "p95-05", "p75-25",
            ],

        "metrics_pgroup":[
            "min", "max", "mean", "stddev",
            "p10", "p25", "p50", "p75", "p90",
            #"p05", "p10", "p25", "p50", "p75", "p90", "p95",
            "max-min", "p95-05", "p75-25",
            ],

        "metrics_spread":[
            "stddev", "max-min", "p95-05", "p75-25"
            ],

        "regions":[
            "northeast", "southeast", "northplains", "southplains",
            "northwest", "southwest", "midwest",
            ],

        "pgroups":[
            "states", "counties",
            ],
        },

    ## number of valid timesteps per array should be consistent;
    ## hard-code it so they don't always have to be sent.
    "nvtimes":10,

    "norm_bounds":{
        "eto-anom":{
            "min":(-12., 12.),
            "max":(-12., 12.),
            "mean":(-12., 12.),
            "mean":(-12., 12.),
            "stddev":(0., 5.),
            "p10":(-12., 12.),
            "p25":(-12., 12.),
            "p25":(-12., 12.),
            "p50":(-12., 12.),
            "p75":(-12., 12.),
            "p90":(-12., 12.),
            "max-min":(0., 18.),
            "p95-05":(0., 18.),
            "p90-10":(0., 18.),
            "p75-25":(0., 18.),
            },
        "eto":{
            "min":(-0.1, 0.75),
            "max":(-0.1, 0.75),
            "mean":(-0.1, 0.75),
            "mean":(-0.1, 0.75),
            "stddev":(0., 0.75),
            "p10":(-0.1, 0.75),
            "p25":(-0.1, 0.75),
            "p25":(-0.1, 0.75),
            "p50":(-0.1, 0.75),
            "p75":(-0.1, 0.75),
            "p90":(-0.1, 0.75),
            "max-min":(0., 0.75),
            "p95-05":(0., 0.75),
            "p90-10":(0., 0.75),
            "p75-25":(0., 0.75),
            },
        },
    "norm_resolution":8192,
    "mask_val":65535,

    "long_labels":{
        "feats":{
            "eto":"Reference Evapotranspiration",
            "eto-anom":"Reference Evapotranspiration Anomaly",
            },
        "metrics":{
            "min":"Minimum",
            "max":"Maximum",
            "mean":"Average",
            "stddev":"Std Dev",
            "p05":"5th Pctl",
            "p10":"10th Pctl",
            "p25":"25th Pctl",
            "p50":"Median",
            "p75":"75th Pctl",
            "p90":"90th Pctl",
            "p95":"95th Pctl",
            "max-min":"Max-Min",
            "p95-05":"95-5 Pctl",
            "p90-10":"90-10 Pctl",
            "p75-25":"75-25 Pctl"
            },
        "regions":{
            "northeast":"Northeast",
            "northwest":"Northwest",
            "southeast":"Southeast",
            "southwest":"Southwest",
            "northplains":"Northern Plains",
            "southplains":"Southern Plains",
            "midwest":"Midwest"
            },
        "units":{
            "eto":"Inches",
            "eto-anom":"Deviation",
            },
        },

    "short_labels":{
        "feats":{
            "eto":"ETo",
            "eto-anom":"ETo Anom",
            },
        "metrics":{
            "min":"Min",
            "max":"Max",
            "mean":"Avg",
            "stddev":"Std",
            "p05":"5 pct",
            "p10":"10 pct",
            "p25":"25 pct",
            "p50":"Median",
            "p75":"75 pct",
            "p90":"90 pct",
            "p95":"95 pct",
            "max-min":"Max-Min",
            "p95-05":"95-5 pct",
            "p90-10":"90-10 pct",
            "p75-25":"75-25 pct"
            },
        "regions":{
            "northeast":"NE",
            "northwest":"NW",
            "southeast":"SE",
            "southwest":"SW",
            "northplains":"N Plains",
            "southplains":"S Plains",
            "midwest":"Midwest"
            },
        "units":{
            "eto":"in",
            "eto-anom":"dev",
            },
        },

    "cmap_default_bounds":{
        "eto-anom":{
            "min":(-12., 12.),
            "max":(-12., 12.),
            "mean":(-12., 12.),
            "mean":(-12., 12.),
            "stddev":(0., 5.),
            "p10":(-12., 12.),
            "p25":(-12., 12.),
            "p25":(-12., 12.),
            "p50":(-12., 12.),
            "p75":(-12., 12.),
            "p90":(-12., 12.),
            "max-min":(0., 18.),
            "p95-05":(0., 18.),
            "p90-10":(0., 18.),
            "p75-25":(0., 18.),
            },
        "eto":{
            "min":(0., 0.4),
            "max":(0., 0.4),
            "mean":(0., 0.4),
            "mean":(0., 0.4),
            "stddev":(0., 0.1),
            "p10":(0., 0.4),
            "p25":(0., 0.4),
            "p25":(0., 0.4),
            "p50":(0., 0.4),
            "p75":(0., 0.4),
            "p90":(0., 0.4),
            "max-min":(0., 0.4),
            "p95-05":(0., 0.3),
            "p90-10":(0., 0.3),
            "p75-25":(0., 0.3),
            },
        },

    "cmap_default_name":{
        "eto-anom":{
            "min":"magma",
            "max":"magma",
            "mean":"magma",
            "mean":"magma",
            "stddev":"magma",
            "p10":"magma",
            "p25":"magma",
            "p25":"magma",
            "p50":"magma",
            "p75":"magma",
            "p90":"magma",
            "max-min":"magma",
            "p95-05":"magma",
            "p90-10":"magma",
            "p75-25":"magma",
            },
        "eto":{
            "min":"cmr.chroma",
            "max":"cmr.chroma",
            "mean":"cmr.chroma",
            "stddev":"nipy_spectral",
            "p10":"cmr.chroma",
            "p25":"cmr.chroma",
            "p25":"cmr.chroma",
            "p50":"cmr.chroma",
            "p75":"cmr.chroma",
            "p90":"cmr.chroma",
            "max-min":"nipy_spectral",
            "p95-05":"nipy_spectral",
            "p90-10":"nipy_spectral",
            "p75-25":"nipy_spectral",
            },
        },
    }

backend = {
    "crs_out":"EPSG:3857",
    "oversample_factor":16,
    "region_degree_buffer":0.1,
    "region_mask_coverage_cutoff":0.3,
    "dependent_metrics":{
        "max-min":["max", "min"],
        "p95-05":["p95", "p05"],
        "p90-10":["p90", "p10"],
        "p75-25":["p90", "p10"],
        },
    "temporal_shard_spatial_shape":(96,96),
    "temporal_chunk_spatial_shape":(6,6),
    "keep_pgroup_properties":{
        "states":["STATE"],
        "counties":["NAME", "STATE"],
        },
    }

cmap = {
    "options":[
        "viridis",
        #"viridis_r",
        #"gnuplot",
        "gist_rainbow",
        "jet",
        "hsv",
        #"gist_earth",
        #"gist_earth_r",
        "coolwarm",
        #"coolwarm_r",
        "cmr.chroma",
        "cmr.pride",
        "cmr.savanna",
        #"cmr.rainforest",
        #"cmr.rainforest_r",
        "nipy_spectral",
        "magma",
        #"cividis",
        #"cividis_r",
        "afmhot",
        #"BrBG",
        #"PuBuGn",
        "bone",
        #"RdGy",
        #"RdGy_r",
        #"RdYlGn",
        #"RdYlGn_r",
        ],
    "resolution":256,
    }

custom_cmaps = {
    "classic-9":{
        "type":"listed",
        "colors":[
            "#cc0000", "#ff6600", "#ffa000", "#ebeb50", "#8ce48c",
            "#00ff00", "#00c800", "#00af00", "#009600",
            ],
        },
    "classic-5":{
        "type":"listed",
        "colors":[
            "#cc0000", "#ffa000", "#8ce48c", "#00c800", "#009600",
            ],
        },
    "beach-9":{
        "type":"listed",
        "colors":[
            "#8c510a", "#bf812d", "#dfc27d", "#f6e8c3", "#f5f5f5",
            "#c7eae5", "#80cdc1", "#35978f", "#01665e",
            ],
        },
    "heat-5":{
        "type":"listed",
        "colors":[
            "#d7191c", "#fdae61", "#ffffbf", "#abd9e9", "#2c7bb6",
            ],
        },
    }

plot_config = {
    "stats":{
        "order":[
            "whisker-min", "whisker-max",
            "whisker-p10", "whisker-p90",
            "box-p25-p75",
            "surround-stddev", "line-mean",
            ],
        "layout":{
            "margin":{"top":10,"right":5,"bottom":160,"left":48},
            "y_label":"",
            "item_width":180,
            "item_height":14,
            "x_padding":0,
            #"y_padding":0,
            },
        "legends":{
            "cur":{
                "title":"Current",
                "x_offset":0,
                "y_offset":-70,
                "item_height":14,
                "item_width":240,
                },
            },
        "elements":{
            "line-mean":{
                "name":"Average",
                "plot_type":"line",
                "legend":"cur",

                "width":2,
                "color":"#ff6161",
                "show":True,

                "data":"mean",
                },
            "box-p25-p75":{
                "name":"25-75th pctl",
                "plot_type":"box",
                "legend":"cur",

                "width":1.5,
                "color":"#6ba7db",
                "opacity":1.,
                "box_width":12,
                "area_opacity":1.,
                "show":True,

                "data":{"lower":"p25", "upper":"p75"},
                },
            "whisker-p10":{
                "name":"10th pctl",
                "plot_type":"whisker",
                "legend":"cur",

                "width":2,
                "color":"#f5b073",
                "cap_width":12,
                "opacity":1.,
                "show":True,

                "data":{"origin":"mean", "extent":"p10"},
                },
            "whisker-p90":{
                "name":"90th pctl",
                "plot_type":"whisker",
                "legend":"cur",

                "width":2,
                "color":"#f5b073",
                "cap_width":12,
                "opacity":1.,
                "show":True,

                "data":{"origin":"mean", "extent":"p90"},
                },
            #"surround-stddev":{
            #    "name":"Standard Dev",
            #    "plot_type":"surround",
            #    "legend":"cur",
            #    "width":1,
            #    "color":"#e88e8e",
            #    "opacity":.7,
            #    "area_opacity":.7,
            #    "show":False,
            #    "data":{"center":"mean", "spread":"stddev"},
            #    },
            "whisker-min":{
                "name":"Min",
                "plot_type":"whisker",
                "legend":"cur",

                "width":1,
                "cap_width":7,
                "color":"#b3b3b3",
                "dashes":"1,1",
                "show":True,

                "data":{"origin":"mean", "extent":"min"},
                },
            "whisker-max":{
                "name":"Max",
                "plot_type":"whisker",
                "legend":"cur",

                "width":1,
                "cap_width":7,
                "color":"#b3b3b3",
                "dashes":"1,1",
                "show":True,

                "data":{"origin":"mean", "extent":"max"},
                },
            },
        },
    }
