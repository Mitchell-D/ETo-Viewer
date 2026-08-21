export const map_anchors = [
    {
        id: "background-layer",
        type: "background",
        paint: {
            "background-color": "#000000",
            "background-opacity":1,
        },
    },
    {
        id: "bottom-anchor",
        type: "background",
        layout: { visibility: "none" },
    },
    {
        id: "basemap-tiles",
        type: "raster",
        source: "basemap",
        paint: {
            "raster-opacity":.4,
            "raster-contrast": -0.2,
            "raster-saturation": -0.4,
        },
        //layout: {visibility: "none"},
    },
    {
        id: "raster-anchor",
        type: "background",
        layout: { visibility: "none" },
    },
    {
        id: "rivers-anchor",
        type: "background",
        layout: { visibility: "none" },
    },
    {
        id: "roads-anchor",
        type: "background",
        layout: { visibility: "none" },
    },
    {
        id: "forests-anchor",
        type: "background",
        layout: { visibility: "none" },
    },
    {
        id: "counties-anchor",
        type: "background",
        layout: { visibility: "none" },
    },
    {
        id: "states-anchor",
        type: "background",
        layout: { visibility: "none" },
    },
    {
        id: "places-anchor",
        type: "background",
        layout: { visibility: "none" },
    },
    {
        id: "top-anchor",
        type: "background",
        layout: { visibility: "none" },
    }
];

export const vector_anchors = {
    states:"states-anchor",
    counties:"counties-anchor",
    rivers:"rivers-anchor",
    forests:"forests-anchor",
    roads:"roads-anchor",
    places:"places-anchor",
};

export const vector_styles = {
    states:[
        {
            name:"core",
            type:"line",
            paint:{
                "line-color":[
                    "case",
                    ["boolean", ["feature-state", "selected"], false],
                    "#0f9423", // enabled
                    "#2a2c2e", // disabled
                ],
                "line-opacity":1,
                "line-width":[
                    "case",
                    ["boolean", ["feature-state", "selected"], false],
                    3, // enabled
                    2, // disabled
                ],
            },
        },
        {
            name:"case",
            type:"line",
            paint:{
                "line-color":[
                    "case",
                    ["boolean", ["feature-state", "selected"], false],
                    "#0f9423", // enabled
                    "#d0d0d1", // disabled
                ],
                "line-opacity":1,
                "line-width":[
                    "case",
                    ["boolean", ["feature-state", "selected"], false],
                    3.5, // enabled
                    2.5, // disabled
                ],
            },
        },
        {
            name:"fill",
            type:"fill",
            paint:{
                "fill-color": "#f0d099",
                "fill-opacity": 0.0 // invisible but clickable
            },
        },
    ],
    counties:[
        {
            name:"core",
            type:"line",
            paint:{
                "line-color":[
                    "case",
                    ["boolean", ["feature-state", "selected"], false],
                    "#0f9423", // enabled
                    "#2a2c2e", // disabled
                ],
                "line-opacity":1,
                "line-width":[
                    "case",
                    ["boolean", ["feature-state", "selected"], false],
                    2, // enabled
                    1, // disabled
                ],
            },
        },
        {
            name:"case",
            type:"line",
            paint:{
                "line-color":[
                    "case",
                    ["boolean", ["feature-state", "selected"], false],
                    "#0f9423", // enabled
                    "#d0d0d1", // disabled
                ],
                "line-opacity":1,
                "line-width":[
                    "case",
                    ["boolean", ["feature-state", "selected"], false],
                    2.5, // enabled
                    1.5, // disabled
                ],
            },
        },
        {
            name:"fill",
            type:"fill",
            paint:{
                "fill-color": "#f0d099",
                "fill-opacity": 0.0 // invisible but clickable
            },
        },
    ],
    forests:[
        {
            name:"core",
            type:"line",
            paint:{
                "line-color":"#24783a",
                "line-opacity":1,
                "line-width":2,
            },
        },
        {
            name:"case",
            type:"line",
            paint:{
                "line-color":"#99f2b0",
                "line-opacity":1,
                "line-width":3,
            },
        },
        {
            name:"fill",
            type:"fill",
            paint:{
                "fill-color": "#f0d099",
                "fill-opacity": 0.0 // invisible but clickable
            },
        },
    ],
    roads:[
        {
            name:"core",
            type:"line",
            paint:{
                "line-color":"#6c757d",
                "line-opacity":1,
                "line-width":2,
                //"line-dasharray":[4,8],
            },
        },
        {
            name:"case",
            type:"line",
            paint:{
                "line-color":"#ffffff",
                "line-opacity":.8,
                "line-width":4,
                //"line-dasharray":[2, 4],
            },
        },
    ],
    rivers:[
        {
            name:"core",
            type:"line",
            paint:{
                "line-color":"#4257f5",
                "line-opacity":1,
                "line-width":1,
            },
        },
        {
            name:"case",
            type:"line",
            paint:{
                "line-color":"#adc5ff",
                "line-opacity":.8,
                "line-width":2,
            },
        },
    ],
    places:[
        {
            name:"core",
            type:"circle",
            paint:{
                "circle-radius":2,
            },
        },
        {
            name:"case",
            type:"circle",
            paint:{
                "circle-radius":4,
            },
        },
        {
            name:"label",
            type:"symbol",
            paint:{
                "text-color":"#000000",
                "text-halo-color":"#ffffff",
                "text-halo-width":.5,
            },
            layout:{
                "text-field":"{NAME}",
                "text-font":["Open Sans Bold"],
                "text-size":12,
                "text-anchor":"top",
            },
        },
    ],
};
