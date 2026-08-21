export class Map {
    #ready;
    #map;
    constructor({
        map_container,
        map_anchors,
        glyphs_url,
        click_scope,
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

            this.active_feature = null;

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
    }) {
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
                promoteId:"UID",
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
                this.#map.setFeatureState(
                    {
                        source:this.active_feature.source,
                        id:this.active_feature.id,
                    },
                    {selected:false},
                );
                this.active_feature = null;
            }
            this._notify_subscribers({
                scope:"pixel",
                loc:[pxy, pxx],
            });
            this.awaiting_click = false;
            return;
        } else {
            const feats = this.#map.queryRenderedFeatures(
                this.last_click.point
            );
            for (const f of feats) {
                if (f.source.includes(this.click_scope)) {
                    if (this.active_feature !== null) {
                        this.#map.setFeatureState(
                            {
                                source:this.active_feature.source,
                                id:this.active_feature.id,
                            },
                            {selected:false},
                        );
                    }
                    this.#map.setFeatureState(
                        {
                            source:f.source,
                            id:f.id,
                        },
                        {selected:true},
                    );
                    this.active_feature = {source:f.source, id:f.id};
                    this._notify_subscribers({
                        scope:this.click_scope,
                        loc:f.id,
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
