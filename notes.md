# configuration

# preprocessing

# api

# javascript

## TimeSeries.js

This javascript module exports a `TimeSeries` class that manages a
d3js time series figure with a legend. It has internal classes
for rendering interactive legends (`LegendRenderer`), applying
new data to an existing figure (`LineRenderer`), and rendering
SVG paths based on new data (`PathBuilder`).

### future plans

-

### init arguments

- `container_id`: HTML ID of element to place the svg inside
- `layout`: layout configuration, see below.
- `legends`: legend configuration, see below
- `elements`: elements configuration, see below
- `time_template`: datetime-like string format of provided dates

### configuration

Each plot is configured with layout, legend, and element information.

#### layout

specifies general plot geometry including padding, margins,
legend item sizes, labels, etc.

If `y_range` is not specified, it defaults to the min/max data range.
If it is provided, it sets the global default y axis scale *until*
`set_y_bounds` is called on the object.

- `y_label`
- `x_label`
- `margin`: {top, right, bottom, left} svg margins around the plot
- `y_range`: optional default global vertical axis value range
- `x_padding`: horizontal space in the figure before and after lines
- `y_padding`: vertical space in the figure before and after lines

#### legends

Ordered list of legends to plot with interactive buttons that
toggle the corresponding line's visibility. A `legend_key` must
be provided.

- `title`
- `legend_key` (always required) unique string id for this legend
- `x_offset`: horizontal position of legend
- `y_offset`: vertical position of legend
- `item_height`: height of each text entry
- `item_width`: width of each text entry

#### elements

Ordered list from bottom to top of plot entries. Each must have a
`element_key` uniquely identifying it, a `plot_type` specifying the
plot style, and a `data` dictionary indicating which time series
variables to display.

Plot types require one or more different entries in the `data`
dictionary:

##### plot types and requirements

**line**: `"\<var1\>"`

A single variable to plot as a line

**box**: `{"lower":"\<var1\>", "upper":"\<var2\>"}`

A range of values to plot as a vertical box

**surround**: `{"center":"\<var1\>", "spread":"\<var2\>"}`

Range defined by a center line with a spread value extending in
both directions (such that the full width is 2 \* spread).

**field**: `{"lower":"\<var1\>", "upper":"\<var2\>"}`

Range defined by upper and lower bounds values.

**whisker**: `{"origin":"\<var1\>", "extent":"\<var2\>"}`

Vertical line segment from origin to extent, with a horizontal
cap at the extent.

##### element modifiers

- `name`
- `plot_type` (always required)
- `element_key` (always required) unique string id for this element
- `legend`: string legend key to place this plot element in
- `show`: indicates whether this element is plotted by default
- `color`: fill of both the line and the area described by a plot
- `opacity`: opacity of the plot's line/border
- `fill_opacity`: opacity of the area described by a closed plot
- `width`: plot's line width
- `cap_width`: size of end caps of whiskers
- `box_width`: horizontal extent of box plots

## PathBuilder

Given functions that convert dates to x coordinates and data
values to y coordinates, generates an SVG path associated with
one of the available plot types. See the `TimeSeries` element
configuration for plot options.

Each of the `PathBuilder`'s public methods is named after a plot
type it provides, and the first positional argument for each is
the x-axis data value. subsequent arguments are the

Note that the parent `TimeSeries` object can update the underlying
scale function without calling an update funtion on the pathbuilder,
as long as the parent object does not overwrite the provided object.

## LineRenderer

Binds new data to an SVG plot

# rust + web assembly
