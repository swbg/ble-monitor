// API config
const apiPort = 3000;
const apiHost = "localhost";

var data;
var devices;
var color;

// Layout config
const margin = {
  top: 20,
  right: 20,
  bottom: 30,
  left: 70,
};
const height = 400;
const innerHeight = height - margin.top - margin.bottom;

// Axes config
function getTemp(serviceData) {
  return (256 * serviceData.data[0] + serviceData.data[1]) / 100;
}

function getHum(serviceData) {
  return (256 * serviceData.data[2] + serviceData.data[3]) / 100;
}

const axesConfig = [
  {
    id: "temp",
    yLabel: "Temperature (°C)",
    dataFun: getTemp,
  },
  {
    id: "hum",
    yLabel: "Humidity (%)",
    dataFun: getHum,
  },
];

// Create axes
const axes = axesConfig.map((config) => {
  // Main pane
  const svg = d3.select("#main").append("svg");

  const svgg = svg
    .append("g")
    .attr("transform", `translate(${margin.left},${margin.top})`);

  svgg
    .append("text")
    .attr("class", "axis-label")
    .attr("text-anchor", "end")
    .attr("x", 0)
    .attr("y", 0)
    .attr("dy", -40)
    .attr("transform", "rotate(-90)")
    .text(config.yLabel);

  // x Axis
  const x = d3.scaleTime();
  const xg = svgg.append("g").attr("transform", `translate(0,${innerHeight})`);

  // y Axis
  const y = d3.scaleLinear().range([innerHeight, 0]);
  const yg = svgg.append("g");

  // Graph
  const graphg = svgg
    .append("g")
    .attr("class", "line-graph")
    .attr("clip-path", "url(#clip)");

  // Brush
  const brush = d3
    .brushX()
    .on("end", (e) => e.selection && updatePlot(e.selection));
  const brushg = svgg.append("g").attr("class", "brush");
  svg.on("click", () => updatePlot());

  return { ...config, svg, svgg, x, xg, y, yg, graphg, brush, brushg };
});

// Define clip path
const clip = axes[0].svg
  .append("defs")
  .append("svg:clipPath")
  .attr("id", "clip")
  .append("svg:rect")
  .attr("height", innerHeight)
  .attr("x", 0)
  .attr("y", 0);

// Update functions
function updateDevices() {
  return d3.json(`http://${apiHost}:${apiPort}/devices`).then((res) => {
    devices = res.map((d) => ({
      name: d.name,
      deviceMac: d.mac.data.map((m) => m.toString(16)).join(""),
    }));

    // This won't work if you have a different number of devices
    color = d3
      .scaleOrdinal()
      .domain(devices.map((d) => d.deviceMac))
      .range(["#e41a1c", "#377eb8", "#4daf4a", "#984ea3"]);
  });
}

function updateData() {
  return d3.json(`http://${apiHost}:${apiPort}/data`).then((res) => {
    const tidy = res.map((d) => ({
      deviceMac: d.device_mac.data.map((m) => m.toString(16)).join(""),
      receivedAt: new Date(d.received_at),
      ...axes.reduce(
        (acc, ax) => ({ ...acc, [ax.id]: ax.dataFun(d.service_data) }),
        {}
      ),
    }));
    data = {
      tidy,
      grouped: d3.group(tidy, (d) => d.deviceMac),
    };
  });
}

function updateSize(width) {
  innerWidth = width - margin.left - margin.right;

  for (let ax of axes) {
    ax.svg.attr("width", width).attr("height", height);
    ax.x.range([0, innerWidth]);
    ax.brush.extent([
      [0, 0],
      [innerWidth, innerHeight],
    ]);
    ax.brushg.call(ax.brush);
  }

  clip.attr("width", innerWidth);
}

function updatePlot(extent) {
  if (!data) {
    return;
  }

  axes.forEach((ax) => {
    // Apply brush
    if (!extent) {
      ax.x.domain(d3.extent(data.tidy, (d) => d.receivedAt));
    } else {
      ax.x.domain([ax.x.invert(extent[0]), ax.x.invert(extent[1])]);
      ax.brushg.call(ax.brush.move, null);
    }
    ax.xg.call(d3.axisBottom(ax.x));

    // Adjust y scale
    ax.y.domain(d3.extent(data.tidy, (d) => d[ax.id]));
    ax.yg.call(d3.axisLeft(ax.y));

    // Plot data
    ax.graphg
      .selectAll("path")
      .data(data.grouped)
      .join(
        (enter) => enter.append("path"),
        (update) => update,
        (exit) => exit.remove()
      )
      .attr("fill", "none")
      .attr("stroke-width", 2)
      .attr("stroke", (d) => color(d[0]))
      .attr("d", (d) =>
        d3
          .line()
          .x((d) => ax.x(d.receivedAt))
          .y((d) => ax.y(d[ax.id]))(d[1])
      );
  });
}

const resizeObserver = new ResizeObserver((entries) => {
  for (let entry of entries) {
    const rect = entry.target.getBoundingClientRect();
    updateSize(rect.width);
    updatePlot();
  }
});
resizeObserver.observe(document.getElementById("main"));

updateDevices().then(() => updateData().then(() => updatePlot()));
