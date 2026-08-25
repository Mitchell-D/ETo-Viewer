import init, { RasterStore } from "/wasm/wasm_raster.js";

let wasm_ready = false;
let store = null;
async function ensure_wasm_init() {
    if (!wasm_ready) {
        await init();
        wasm_ready = true;
    }
    if (!store) store = new RasterStore();
}


self.onmessage = async (a) => {
    const {type, id, args} = a.data;
    //console.log(type, id, args);
    await ensure_wasm_init();
    ///*
    try {
        if (type === "load-array") {
            const {key, buffer, width, height, ntimes} = args;
            const x = new Uint16Array(buffer);
            console.log("loading", key);
            store.add(key, x, ntimes, height, width);
            self.postMessage({
                id:id,
                ok:true,
                result:null,
                error:null,
            });
        } else if (type === "delete-array") {
            console.log("deleting", args.key);
            store.del(args.key);
            self.postMessage({
                id:id,
                ok:true,
                result:null,
                error:null,
            });
        } else if (type === "get-rgb") {
            const {
                key, time_index, cmap, resolution, mask_val, norm, cmap_bounds,
            } = args;
            //console.log("getting rgb of ", key, time_index);
            const rgb = store.generate_rgb(
                key,
                time_index,
                cmap,
                mask_val,
                resolution,
                norm.min,
                norm.max,
                cmap_bounds.min,
                cmap_bounds.max,
            );
            self.postMessage({
                id:id,
                ok:true,
                result:rgb,
                error:null,
            });
        } else {
            console.error("unrecognized type:", type);
        }
    } catch (error) {
        self.postMessage({id, ok:false, error:error.toString()});
    }
    //*/
}
