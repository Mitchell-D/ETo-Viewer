frontend = {
    "feats":["eto"],

    "metrics_raster":[
        "min", "max", "mean", "stddev",
        "p10", "p25", "p50", "p75", "p90",
        "max-min", "p90-10", "p75-25",
        ],

    "metrics_pgroup":[
        "min", "max", "mean", "stddev",
        "p10", "p25", "p50", "p75", "p90",
        "max-min", "p90-10", "p75-25",
        ],

    "regions":[
        "northeast", "southeast", "northplains", "southplains",
        "northwest", "southwest", "midwest",
        ],

    "pgroups":[
        "states", "counties",
        ],

    "norm_bounds":{
        "eto":{
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
            "p90-10":(0., 18.),
            "p75-25":(0., 18.),
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
        "p90-10":["p90", "p10"],
        "p75-25":["p90", "p10"],
        },
    }

