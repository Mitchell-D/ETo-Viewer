frontend = {
    "feats":["eto"],

    "metrics_raster":[
        "min", "max", "mean", "stddev",
        "p10", "p25", "p50", "p75", "p90",
        "max-min", "p95-05", "p75-25",
        ],

    "metrics_pgroup":[
        "min", "max", "mean", "stddev",
        "p10", "p25", "p50", "p75", "p90",
        "max-min", "p95-05", "p75-25",
        ],

    "regions":[
        "northeast", "southeast", "northplains", "southplains",
        "northwest", "southwest", "midwest",
        ],

    "pgroups":[
        "states", "counties",
        ],

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
    }

