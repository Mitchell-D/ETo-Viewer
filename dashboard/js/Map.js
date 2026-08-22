/**
Class for managing a MapLibre map supporting regionalized rasters,
arbitrary geojson features with optional clickability and highlight layers,
and pixel-level clicking on rendered rasters.

If the click_scope state is "pixel", subscribed callbacks are notified with
the clicked pixel's lat/lon and indeces.

If a click_scope is assigned to a geojson source, subscribed callbacks will
be notified any time the click_scope state equals that string and a feature
within the source is clicked on.

If a source with click_scope defined has highlight layers, each feature
within that source must have a unique "UID" property, and the clicked
feature will be activated within all of the corresponding highlight layers.
*/
export class Map {
    #ready;
    #map;
    constructor({
        map_container,
        map_anchors,
        glyphs_url,
        click_scope,
        pixel_marker_anchor=null,
        pixel_marker_layers=[],
    }) {
        this.#ready = new Promise((resolve, reject) => {
            const tmp_ctr = [-92.195082, 37.104743];
            this.#map = new maplibregl.Map({
                container:map_container,
                center:tmp_ctr,
                style: {
                    version: 8,
                    glyphs:glyphs_url,
                    sources: {
                        "basemap":{
                            type:"raster",
                            tiles: [
                                //"https://c.tile.opentopomap.org/{z}/{x}/{y}.png"
                                "/basemap/natural_earth_2_shaded_relief.raster"
                                + "/{z}/{x}/{y}",
                            ],
                            minzoom:2,
                            maxzoom:6,
                            tileSize:256,
                            //attribution:"© OpenStreetMap",
                        }
                    },
                    layers:map_anchors,
                },
                zoom: 3,
                minZoom:2,
                maxZoom:8,
            });

            if (!click_scope) {
                this.click_scope = null;
            }

            this.#map.once("load", resolve);
            this.#map.once("error", (e) => {
                reject(e.error ?? new Error("map load failed"));
            });
            this.canvas = document.createElement("canvas");
            this.ctx = this.canvas.getContext("2d");
            this.cur_bbox = null;
            this.pixel_marker_anchor = pixel_marker_anchor;

            this.active_feature = null;
            this.source_scopes = {};

            this.awaiting_click = false;
            this.#map.on("click", (e) => {
                this.last_click = {
                    coords:e.lngLat,
                    point:e.point,
                };
                if (this.click_scope!==null) {
                    this.handle_click();
                }
            });
            const def_click_coords = {lng:tmp_ctr[0], lat:tmp_ctr[1]}
            this.#map.fire("click", {
                lngLat:def_click_coords,
                point:this.#map.project(def_click_coords),
                originalEvent:new MouseEvent("click"),
            });

            this.subscriptions = [];
        });

        this.#ready.then(() => {
            if (!this.pixel_marker_anchor) return;
            // make an empty source for the pixel click location
            this.#map.addSource("pixel-marker", {
                type:"geojson",
                data:{
                    type: "FeatureCollection",
                    features: [],
                },
            });
            let cur_anchor = pixel_marker_anchor;
            pixel_marker_layers.forEach(l => {
                const lname = `pixel-marker_layer-${l.name}`
                this.#map.addLayer({
                    id:lname,
                    type:l.type,
                    source:"pixel-marker",
                    paint:l?.paint ?? {},
                    layout:l?.layout ?? {},
                }, cur_anchor);
                cur_anchor = lname;
            });
        });
    }

    // resolve when map initialized.
    ready() {
        return this.#ready;
    }

    async set_region({
        bbox,
        bounds_buffer,
        raster_width,
        raster_height,
    }) {
        // make sure the map is ready
        await this.#ready;

        // update the map view location
        this.#map.setMaxBounds([
            [bbox[0]-bounds_buffer[1], bbox[1]-bounds_buffer[0]],
            [bbox[2]+bounds_buffer[1], bbox[3]+bounds_buffer[0]],
        ]);
        const tmp_ctr = [(bbox[0]+bbox[2])/2, (bbox[1]+bbox[3])/2]
        this.#map.setCenter(tmp_ctr);
        const def_click_coords = {lng:tmp_ctr[0], lat:tmp_ctr[1]}
        this.#map.fire("click", {
            lngLat:def_click_coords,
            point:this.#map.project(def_click_coords),
            originalEvent:new MouseEvent("click"),
        });

        // update the raster canvas
        this.canvas.width = raster_width;
        this.canvas.height = raster_height;
        this.ctx.imageSmoothingEnabled = false;
        this.ctx.webkitImageSmoothingEnabled = false;
        this.ctx.mozImageSmoothingEnabled = false;
        this.cur_bbox = bbox;

        const src = this.#map.getSource("raster");
        const coords = [
            [this.cur_bbox[0], this.cur_bbox[3]],
            [this.cur_bbox[2], this.cur_bbox[3]],
            [this.cur_bbox[2], this.cur_bbox[1]],
            [this.cur_bbox[0], this.cur_bbox[1]],
        ];
        if (!src) {
            this.#map.addSource("raster", {
                type:"canvas",
                canvas:this.canvas,
                coordinates:coords,
                animate:true,
            });
            this.#map.addLayer({
                id:"raster-layer",
                type:"raster",
                source:"raster",
                paint:{
                    "raster-opacity":1.,
                    "raster-resampling":"nearest",
                },
            }, "raster-anchor");
        } else {
            src.setCoordinates(coords);
        }

        if (this.awaiting_click && this.click_scope==="pixel") {
            this.handle_click();
        }
    }

    async add_geojson({
        name,
        data,
        layers,
        anchor,
        click_scope=null,
        highlight_anchor=null,
        highlight_layers=null,
    }) {
        if (click_scope === "pixel") {
            throw new Error("'pixel' is a reserved click scope");
        }
        await this.#ready;
        return new Promise((resolve, reject) => {
            const map_idle = () => {
                this.#map.off("idle", map_idle);
                resolve(data);
            }

            const map_error = (e) =>  {
                this.#map.off("idle", map_idle);
                this.#map.off("error", map_error);
                reject(e.error ?? e);
            }

            this.#map.once("idle", map_idle);
            this.#map.on("error", map_error);

            this.#map.addSource(name, {
                type:"geojson",
                data:data,
                //promoteId:"UID",
            });
            let cur_anchor = anchor;
            for (const l of layers) {
                this.#map.addLayer({
                    id:`${name}_layer-${l.name}`,
                    type:l.type,
                    source:name,
                    paint:l.paint,
                    layout:l?.layout ?? {},
                }, cur_anchor);
                cur_anchor = `${name}_layer-${l.name}`;
            }

            // if click_scope is defined, then the clicked feat will notify
            // subscribers when click_scope matches the current scope defined
            // by set_click_scope. The UID property must be defined.
            // Also, a clickable source may have highlight layers that are
            // activated for that feature when it is selected.
            if (click_scope) {
                if (!("UID" in data.features[0].properties)) {
                    throw new Error(
                        "'UID' property required for clickable layers not in:",
                        name
                    );
                }
                this.source_scopes[name] = {
                    scope:click_scope,
                    hlayers:[],
                };
                if (highlight_anchor) {
                    cur_anchor = highlight_anchor;
                    for (const l of highlight_layers) {
                        const lname = `${name}_highlight-${l.name}`;
                        this.source_scopes[name].hlayers.push(lname);
                        this.#map.addLayer({
                            id:lname,
                            type:l.type,
                            source:name,
                            paint:l.paint,
                            layout:l?.layout ?? {},
                            filter:["==", ["get", "UID"], null],
                        }, cur_anchor);
                        cur_anchor = lname;
                    }
                }
            }

            if (this.awaiting_click && name.includes(this.click_scope)) {
                this.handle_click();
            }
        });
    }

    handle_click() {
        if (this.click_scope === "pixel") {
            if (this.cur_bbox === null) {
                this.awaiting_click = true;
                return;
            }
            const {lng,lat} = this.last_click.coords;
            const u = (lng-this.cur_bbox[0])
                / (this.cur_bbox[2]-this.cur_bbox[0]);
            const v = (this.cur_bbox[3]-lat)
                / (this.cur_bbox[3]-this.cur_bbox[1]);
            const pxx = Math.floor(u * this.canvas.width)
            const pxy = Math.floor(v * this.canvas.height)
            if (pxx < 0 || pxx >= this.canvas.width) return;
            if (pxy < 0 || pxy >= this.canvas.height) return;
            if (this.active_feature !== null) {
                // clear the activ feature if it's a vector type. If it's
                // a pixel, setting the source data will change its position
                const cur_src = this.active_feature.source;
                if (this.active_feature.type === "vector") {
                    this.source_scopes[cur_src].hlayers.forEach(l => {
                        this.#map.setFilter(
                            l, ["==", ["get", "UID"], null],
                        );
                    });
                } else if (this.active_feature.type === "pixel") {
                    // ignore if this is the same pixel last clicked
                    if (
                        (pxx == this.active_feature.pxx)
                        && (pxy == this.active_feature.pxy)
                    ) {
                        return;
                    }
                }
            }

            this.#map.getSource("pixel-marker").setData({
                type: "FeatureCollection",
                features: [{
                    type:"Feature",
                    properties:{},
                    geometry: {
                        type:"Point",
                        coordinates: [lng, lat],
                    },
                }],
            });

            this.active_feature = {
                type:"pixel",
                lat:lat,
                lon:lng,
                pxy:pxy,
                pxx:pxx,
            };
            this._notify_subscribers({
                scope:"pixel",
                loc:[pxy, pxx],
                coords:[lat, lng],
            });
            this.awaiting_click = false;
            return;
        } else {
            const feats = this.#map.queryRenderedFeatures(
                this.last_click.point
            );
            for (const f of feats) {
                // feature clicked with active scope...
                if (f.source in this.source_scopes) {
                    if (this.click_scope !==
                            this.source_scopes[f.source].scope) {
                        continue;
                    }
                    // disable the currently active highlight layers
                    if (this.active_feature !== null) {
                        if (this.active_feature.type === "vector") {
                            // ignore if the same feature is clicked again
                            if (this.active_feature.id === f.id) {
                                return;
                            }
                            const cur_src = this.active_feature.source;
                            this.source_scopes[cur_src].hlayers.forEach(l => {
                                this.#map.setFilter(
                                    l, ["==", ["get", "UID"], null],
                                );
                            });
                        } else if (this.active_feature.type === "pixel") {
                            this.#map.getSource("pixel-marker").setData({
                                type: "FeatureCollection",
                                features: [],
                            });
                        }
                    }
                    // highlight the selected feature
                    this.source_scopes[f.source].hlayers.forEach(l => {
                        this.#map.setFilter(
                            l, ["==", ["get", "UID"], f.properties.UID]
                        );
                    });

                    this.active_feature = {
                        type:"vector",
                        source:f.source,
                        id:f.id,
                        props:f.properties,
                        UID:f.properties.UID,
                    };
                    this._notify_subscribers({
                        scope:this.click_scope,
                        loc:f.id,
                        props:f.properties,
                        UID:f.properties.UID,
                    });
                    this.awaiting_click = false;
                    return;
                }
            }
            this.awaiting_click = true;
            return;
        }
    }

    async render(image_data) {
        this.ctx.putImageData(image_data, 0, 0);
        this.#map.triggerRepaint();
    }

    async set_vector_visibility({
        substring,
        visible,
    }) {
        await this.#ready;
        const vis = visible ? "visible" : "none";

        for (const l of this.#map.getStyle().layers ?? []) {
            if (l.id.includes(substring)) {
                this.#map.setLayoutProperty(l.id, "visibility", vis);
            }
        }
    }

    set_click_scope(substring) {
        this.click_scope = substring;
        this.handle_click();
    }

    subscribe(callback) {
        if (typeof callback !== "function") {
            throw new Error("Must provide a callback function not "+callback);
        }
        this.subscriptions.push(callback);
    }

    _notify_subscribers(args) {
        this.subscriptions.forEach(f => f(args));
    }
}
