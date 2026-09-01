export class TimeSeriesChiclets {
    constructor({container_id, template_id, style_fn}) {
        this.container = typeof container_id === "string"
            ? document.getElementById(container_id)
            : container_id;
        console.log(template_id);
        console.log(document.getElementById(template_id))
        this.template = document.getElementById(template_id).content;
        this.style_fn = style_fn;
        this.children = [];
    }

    set_data(data) {
        const keys = Object.keys(data);
        if (keys.length === 0) {
            this.container.innerHTML = '';
            this.children = [];
            return;
        }

        const step_count = data[keys[0]].length;

        // adjust child nodes to match data length
        while (this.children.length < step_count) {
            //const child = this._init_template();
            const child = this.template.firstElementChild.cloneNode(true);
            this.container.appendChild(child);
            this.children.push(child);
        }

        while (this.children.length > step_count) {
            const child = this.children.pop();
            this.container.removeChild(child);
        }

        // update each child with sliced data for that time step
        for (let i = 0; i < step_count; i++) {
            const step_data = {};
            for (const k of keys) {
                step_data[k] = data[k][i];
            }
            this.style_fn(this.children[i], step_data);
        }
    }

    /*
    _init_template() {
        if (typeof this.template === "string") {
            const wrapper = document.createElement("div");
            wrapper.innerHTML = this.template.trim();
            return wrapper.firstElementChild || wrapper;
        }
        if (typeof this.template === "function") {
            return this.template();
        }
        if (this.template instanceof HTMLElement) {
            return this.template.cloneNode(true);
        }
        return document.createElement("div");
    }
    */
}
