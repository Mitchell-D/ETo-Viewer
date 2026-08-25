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
        id: "states-highlight-anchor",
        type: "background",
        layout: { visibility: "none" },
    },
    {
        id: "counties-highlight-anchor",
        type: "background",
        layout: { visibility: "none" },
    },
    {
        id: "pixel-highlight-anchor",
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

export const highlight_anchors = {
    counties:"counties-highlight-anchor",
    states:"states-highlight-anchor",
    pixel:"pixel-highlight-anchor",
}

export const vector_styles = {
    states:[
        {
            name:"core",
            type:"line",
            paint:{
                "line-color":"#494d52",
                "line-opacity":.8,
                "line-width":2,
            },
        },
        {
            name:"case",
            type:"line",
            paint:{
                "line-color":"#777f85",
                "line-opacity":.6,
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
    counties:[
        {
            name:"core",
            type:"line",
            paint:{
                "line-color":"#494d52",
                "line-opacity":.8,
                "line-width":.5,
            },
        },
        {
            name:"case",
            type:"line",
            paint:{
                "line-color":"#777f85",
                "line-opacity":.6,
                "line-width":1,
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
                "line-opacity":1.,
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
                "line-opacity":1.,
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

export const highlight_styles = {
    counties:[
        {
            name:"core",
            type:"line",
            paint:{
                "line-color":"#02520e",
                "line-opacity":1.,
                "line-width":1.5,
            },
        },
        {
            name:"case",
            type:"line",
            paint:{
                "line-color":"#56b065",
                "line-opacity":1.,
                "line-width":4,
            },
        },
    ],
    states:[
        {
            name:"core",
            type:"line",
            paint:{
                "line-color":"#02520e",
                "line-opacity":1.,
                "line-width":1.5,
            },
        },
        {
            name:"case",
            type:"line",
            paint:{
                "line-color":"#56b065",
                "line-opacity":1.,
                "line-width":4,
            },
        },
    ],
    pixel:[
        {
            name:"core",
            type:"circle",
            paint:{
                "circle-color":"#02520e",
                "circle-radius":3,
            },
            layout:{},
        },
        {
            name:"case",
            type:"circle",
            paint:{
                "circle-color":"#56b065",
                "circle-radius":4,
            },
            layout:{},
        },
    ],
};

