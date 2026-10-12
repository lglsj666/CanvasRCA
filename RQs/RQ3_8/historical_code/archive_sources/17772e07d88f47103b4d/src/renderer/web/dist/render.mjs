// render.tsx
import { renderToStaticMarkup } from "react-dom/server";
import { chromium } from "playwright";
import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { createHash } from "node:crypto";

// dashboard.tsx
import React from "react";

// components/primitives.tsx
import { Fragment, jsx, jsxs } from "react/jsx-runtime";
var relationColors = { calls: "var(--accent)", hosts: "var(--hosts)", owns: "var(--owns)", request_parent: "var(--request-parent)", has_instance: "var(--owns)" };
var n = (v) => v === 0 ? "0" : Math.abs(v) >= 1e5 || Math.abs(v) < 1e-3 ? v.toExponential(3) : String(Number(v.toPrecision(5)));
var field = (key) => ({ "data-binding": key });
function Details({ card }) {
  return /* @__PURE__ */ jsx("div", { className: "details", children: (card.data.details ?? []).map((d, i) => /* @__PURE__ */ jsxs("div", { className: "detail", ...field(`${card.id}.detail.${i}`), children: [
    /* @__PURE__ */ jsx("span", { className: "label", children: d.name }),
    /* @__PURE__ */ jsx("span", { className: "value", children: d.value })
  ] }, i)) });
}
function seriesGeometry(card, domain) {
  const bins = card.data.bins, values = card.kind === "log" ? card.data.counts : card.data.values;
  const valid = values.map((v, i) => ({ v, i })).filter((p) => p.v !== null);
  let lo = Math.min(...valid.map((p) => p.v), 0), hi = Math.max(...valid.map((p) => p.v), 0);
  if (domain === "extent" && valid.length) {
    lo = Math.min(...valid.map((p) => p.v));
    hi = Math.max(...valid.map((p) => p.v));
  }
  const delta = hi - lo || Math.max(Math.abs(hi) * 0.05, 1);
  if (domain === "extent") {
    lo = lo >= 0 ? Math.max(0, lo - delta * 0.08) : lo - delta * 0.08;
    hi += delta * 0.08;
  } else if (hi === lo) {
    hi = lo + delta;
  }
  const left = 70, right = 446, top = 14, bottom = 116, minBin = Math.min(...bins), maxBin = Math.max(...bins);
  const x = (i) => minBin === maxBin ? (left + right) / 2 : left + (bins[i] - minBin) / (maxBin - minBin) * (right - left);
  const y = (v) => bottom - (v - lo) / (hi - lo) * (bottom - top);
  return {
    valid,
    lo,
    hi,
    left,
    right,
    top,
    bottom,
    minBin,
    maxBin,
    x,
    y,
    zero: y(Math.max(lo, Math.min(hi, 0))),
    bar: Math.min(28, (right - left) / Math.max(bins.length, 2) * 0.75)
  };
}
function Axes({ card, p, quantitative = true }) {
  const { left, right, top, bottom, minBin, maxBin, lo, hi } = p;
  return /* @__PURE__ */ jsxs(Fragment, { children: [
    /* @__PURE__ */ jsx("line", { x1: left, y1: bottom, x2: right, y2: bottom, stroke: "var(--axis)" }),
    quantitative && /* @__PURE__ */ jsxs(Fragment, { children: [
      /* @__PURE__ */ jsx("text", { x: left - 8, y: top + 5, textAnchor: "end", children: n(hi) }),
      /* @__PURE__ */ jsx("text", { x: left - 8, y: bottom, textAnchor: "end", children: n(lo) }),
      /* @__PURE__ */ jsx("line", { x1: left, y1: top, x2: left, y2: bottom, stroke: "var(--axis)" }),
      /* @__PURE__ */ jsx("line", { x1: left, y1: (top + bottom) / 2, x2: right, y2: (top + bottom) / 2, stroke: "var(--border)", strokeDasharray: "3 5" })
    ] }),
    /* @__PURE__ */ jsxs("g", { ...field(card.id + ".time"), children: [
      minBin === maxBin ? /* @__PURE__ */ jsx("text", { x: (left + right) / 2, y: "137", textAnchor: "middle", children: minBin }) : /* @__PURE__ */ jsxs(Fragment, { children: [
        /* @__PURE__ */ jsx("text", { x: left, y: "137", children: minBin }),
        /* @__PURE__ */ jsx("text", { x: right, y: "137", textAnchor: "end", children: maxBin })
      ] }),
      /* @__PURE__ */ jsx("text", { x: (left + right) / 2, y: "152", textAnchor: "middle", children: "Relative time bin" })
    ] })
  ] });
}
function graphPositions(nodes, width, height, edges = []) {
  const sorted = [...nodes].sort((a, b) => Number(a.id) - Number(b.id));
  const positions = {};
  if (nodes.length > 30) {
    const neighbours = Object.fromEntries(sorted.map((n2) => [n2.id, /* @__PURE__ */ new Set()]));
    for (const e of edges) {
      neighbours[e.source]?.add(e.target);
      neighbours[e.target]?.add(e.source);
    }
    const order = [], seen = /* @__PURE__ */ new Set();
    for (const start of sorted) {
      if (seen.has(start.id)) continue;
      const queue = [start.id];
      seen.add(start.id);
      for (let q = 0; q < queue.length; q++) {
        const id = queue[q];
        order.push(id);
        for (const next of [...neighbours[id]].sort((a, b) => Number(a) - Number(b)))
          if (!seen.has(next)) {
            seen.add(next);
            queue.push(next);
          }
      }
    }
    const cols = Math.min(8, Math.max(1, Math.floor(width / 160))), rows = Math.ceil(order.length / cols);
    order.forEach((id, i) => {
      positions[id] = {
        x: 90 + i % cols * (width - 180) / Math.max(1, cols - 1),
        y: 48 + Math.floor(i / cols) * (height - 96) / Math.max(1, rows - 1)
      };
    });
    return positions;
  }
  const ringSize = 18;
  sorted.forEach((node, i) => {
    const ring = Math.floor(i / ringSize), start = ring * ringSize, count = Math.min(ringSize, sorted.length - start);
    const angle = 2 * Math.PI * (i - start) / count - Math.PI / 2;
    const fraction = 1 - ring * 0.5;
    positions[node.id] = {
      x: width / 2 + Math.cos(angle) * Math.max(0, width / 2 - 85) * fraction,
      y: height / 2 + Math.sin(angle) * Math.max(0, height / 2 - 46) * fraction
    };
  });
  return positions;
}
function RelationLegend({ edges }) {
  return /* @__PURE__ */ jsx("div", { className: "legend", children: Object.entries(relationColors).filter(([kind]) => edges.some((e) => e.kind === kind)).map(([kind, color]) => /* @__PURE__ */ jsxs("span", { children: [
    /* @__PURE__ */ jsx("i", { className: "swatch", style: { borderColor: color } }),
    kind,
    " \u2192"
  ] }, kind)) });
}

// components/MetricLine.tsx
import { jsx as jsx2, jsxs as jsxs2 } from "react/jsx-runtime";
function MetricLine({ card }) {
  const p = seriesGeometry(card, "extent");
  return /* @__PURE__ */ jsxs2("svg", { className: "chart", viewBox: "0 0 470 156", role: "img", "aria-label": card.title, children: [
    /* @__PURE__ */ jsx2(Axes, { card, p, quantitative: p.valid.length > 0 }),
    p.valid.length > 1 && /* @__PURE__ */ jsx2(
      "polyline",
      {
        fill: "none",
        stroke: "var(--accent)",
        strokeWidth: "2.3",
        points: p.valid.map((v) => `${p.x(v.i)},${p.y(v.v)}`).join(" ")
      }
    ),
    p.valid.map((v) => /* @__PURE__ */ jsx2("circle", { ...field(`${card.id}.sample.${v.i}`), cx: p.x(v.i), cy: p.y(v.v), r: "1.9", fill: "var(--accent)" }, v.i))
  ] });
}

// components/MetricReadings.tsx
import { jsx as jsx3, jsxs as jsxs3 } from "react/jsx-runtime";
var exact = (v) => {
  const a = String(v), b = v.toExponential();
  return b.length < a.length ? b : a;
};
function MetricReadings({ card }) {
  return /* @__PURE__ */ jsxs3("div", { style: { fontSize: 12, lineHeight: "17px", display: "grid", gridTemplateColumns: "repeat(4,1fr)", gap: "0 6px" }, children: [
    /* @__PURE__ */ jsx3("div", { ...field(card.id + ".time"), style: { gridColumn: "1/-1" }, children: "time bin : value" }),
    card.data.values.map((v, i) => v === null ? null : /* @__PURE__ */ jsxs3("span", { ...field(`${card.id}.sample.${i}`), children: [
      card.data.bins[i],
      ":",
      exact(v)
    ] }, i))
  ] });
}

// components/MetricTimeBars.tsx
import { jsx as jsx4, jsxs as jsxs4 } from "react/jsx-runtime";
function MetricTimeBars({ card }) {
  const p = seriesGeometry(card, "zero");
  return /* @__PURE__ */ jsxs4("svg", { className: "chart", viewBox: "0 0 470 156", role: "img", "aria-label": card.title, children: [
    /* @__PURE__ */ jsx4(Axes, { card, p, quantitative: p.valid.length > 0 }),
    p.valid.map((v) => /* @__PURE__ */ jsx4(
      "rect",
      {
        ...field(`${card.id}.sample.${v.i}`),
        x: p.x(v.i) - p.bar / 2,
        y: Math.min(p.y(v.v), p.zero),
        width: p.bar,
        height: Math.max(1, Math.abs(p.zero - p.y(v.v))),
        fill: "var(--accent)"
      },
      v.i
    )),
    card.kind === "log" && p.valid.map((v) => /* @__PURE__ */ jsxs4("text", { x: p.x(v.i) + 20, y: Math.max(22, p.y(v.v)), className: "chart-value", children: [
      n(v.v),
      " events"
    ] }, v.i))
  ] });
}

// components/MetricHeatmap.tsx
import { jsx as jsx5, jsxs as jsxs5 } from "react/jsx-runtime";
function MetricHeatmap({ card }) {
  const p = seriesGeometry(card, "zero");
  return /* @__PURE__ */ jsxs5("svg", { className: "chart", viewBox: "0 0 470 156", role: "img", "aria-label": card.title, children: [
    /* @__PURE__ */ jsx5(Axes, { card, p, quantitative: false }),
    p.valid.length > 0 && /* @__PURE__ */ jsxs5("text", { x: p.left, y: "24", children: [
      n(p.lo),
      " \u2192 ",
      n(p.hi)
    ] }),
    p.valid.map((v) => /* @__PURE__ */ jsx5(
      "rect",
      {
        ...field(`${card.id}.sample.${v.i}`),
        x: p.x(v.i) - Math.min(5, p.bar / 2),
        y: "36",
        width: Math.min(10, p.bar),
        height: "48",
        fill: "var(--accent)",
        fillOpacity: 0.2 + 0.8 * (v.v - p.lo) / (p.hi - p.lo)
      },
      v.i
    )),
    /* @__PURE__ */ jsxs5("text", { x: p.left, y: "106", children: [
      "Color intensity \xB7 ",
      card.unit.replaceAll("_", " ")
    ] })
  ] });
}

// components/TracePairedBars.tsx
import { jsx as jsx6, jsxs as jsxs6 } from "react/jsx-runtime";
function TracePairedBars({ card }) {
  const a = card.data.before, b = card.data.after, max = Math.max(a, b, 1), x = (v) => 105 + v / max * 255;
  const rows = [{ v: a, label: "Reference", id: "before", color: "var(--second)" }, { v: b, label: "Current", id: "after", color: "var(--accent)" }];
  return /* @__PURE__ */ jsxs6("svg", { className: "chart", viewBox: "0 0 470 120", role: "img", "aria-label": "Reference and current exclusive latency p95", children: [
    rows.map((r, i) => /* @__PURE__ */ jsxs6("g", { ...field(card.id + "." + r.id), children: [
      /* @__PURE__ */ jsx6("text", { x: "98", y: 33 + i * 39, textAnchor: "end", children: r.label }),
      /* @__PURE__ */ jsx6("rect", { x: "105", y: 18 + i * 39, width: Math.max(1, x(r.v) - 105), height: "21", rx: "3", fill: r.color }),
      /* @__PURE__ */ jsx6("text", { x: x(r.v) + 8, y: 33 + i * 39, className: "chart-value", children: n(r.v) })
    ] }, r.id)),
    /* @__PURE__ */ jsxs6("text", { x: "105", y: "108", children: [
      "Exclusive latency p95 \xB7 ",
      card.unit
    ] })
  ] });
}

// components/TraceDumbbell.tsx
import { Fragment as Fragment2, jsx as jsx7, jsxs as jsxs7 } from "react/jsx-runtime";
function TraceDumbbell({ card }) {
  const a = card.data.before, b = card.data.after, max = Math.max(a, b, 1), x = (v) => 105 + v / max * 255;
  return /* @__PURE__ */ jsxs7(Fragment2, { children: [
    /* @__PURE__ */ jsxs7("svg", { className: "chart", viewBox: "0 0 470 120", role: "img", "aria-label": "Reference and current exclusive latency p95", children: [
      /* @__PURE__ */ jsx7("line", { x1: x(a), x2: x(b), y1: "53", y2: "53", stroke: "var(--axis)", strokeWidth: "3" }),
      /* @__PURE__ */ jsxs7("g", { ...field(card.id + ".before"), children: [
        /* @__PURE__ */ jsx7("circle", { cx: x(a), cy: "53", r: "6", fill: "var(--second)" }),
        /* @__PURE__ */ jsx7("text", { x: x(a), y: "26", textAnchor: "middle", children: n(a) })
      ] }),
      /* @__PURE__ */ jsxs7("g", { ...field(card.id + ".after"), children: [
        /* @__PURE__ */ jsx7("circle", { cx: x(b), cy: "53", r: "6", fill: "var(--accent)" }),
        /* @__PURE__ */ jsx7("text", { x: x(b), y: "82", textAnchor: "middle", children: n(b) })
      ] }),
      /* @__PURE__ */ jsxs7("text", { x: "105", y: "108", children: [
        "Exclusive latency p95 \xB7 ",
        card.unit
      ] })
    ] }),
    /* @__PURE__ */ jsxs7("div", { className: "legend", children: [
      /* @__PURE__ */ jsxs7("span", { children: [
        /* @__PURE__ */ jsx7("i", { className: "swatch secondary" }),
        "Reference"
      ] }),
      /* @__PURE__ */ jsxs7("span", { children: [
        /* @__PURE__ */ jsx7("i", { className: "swatch" }),
        "Current"
      ] })
    ] })
  ] });
}

// components/TraceTable.tsx
import { jsx as jsx8, jsxs as jsxs8 } from "react/jsx-runtime";
function TraceTable({ card }) {
  return /* @__PURE__ */ jsxs8("table", { children: [
    /* @__PURE__ */ jsx8("thead", { children: /* @__PURE__ */ jsxs8("tr", { children: [
      /* @__PURE__ */ jsx8("th", { children: "Exclusive p95" }),
      /* @__PURE__ */ jsx8("th", { children: card.unit })
    ] }) }),
    /* @__PURE__ */ jsxs8("tbody", { children: [
      /* @__PURE__ */ jsxs8("tr", { ...field(card.id + ".before"), children: [
        /* @__PURE__ */ jsx8("td", { children: "Reference" }),
        /* @__PURE__ */ jsx8("td", { children: card.data.before })
      ] }),
      /* @__PURE__ */ jsxs8("tr", { ...field(card.id + ".after"), children: [
        /* @__PURE__ */ jsx8("td", { children: "Current" }),
        /* @__PURE__ */ jsx8("td", { children: card.data.after })
      ] })
    ] })
  ] });
}

// components/LogTimeline.tsx
import { Fragment as Fragment3, jsx as jsx9, jsxs as jsxs9 } from "react/jsx-runtime";
function LogTimeline({ card }) {
  return /* @__PURE__ */ jsxs9(Fragment3, { children: [
    /* @__PURE__ */ jsx9("div", { className: "template", "data-binding": card.id + ".template", children: card.data.template }),
    /* @__PURE__ */ jsx9(MetricTimeBars, { card })
  ] });
}

// components/LogTable.tsx
import { Fragment as Fragment4, jsx as jsx10, jsxs as jsxs10 } from "react/jsx-runtime";
function LogTable({ card }) {
  return /* @__PURE__ */ jsxs10(Fragment4, { children: [
    /* @__PURE__ */ jsx10("div", { className: "template", "data-binding": card.id + ".template", children: card.data.template }),
    /* @__PURE__ */ jsxs10("table", { children: [
      /* @__PURE__ */ jsx10("thead", { children: /* @__PURE__ */ jsxs10("tr", { children: [
        /* @__PURE__ */ jsx10("th", { children: "Relative time bin" }),
        /* @__PURE__ */ jsx10("th", { children: "Events" })
      ] }) }),
      /* @__PURE__ */ jsx10("tbody", { children: card.data.bins.map((b, i) => /* @__PURE__ */ jsxs10("tr", { children: [
        /* @__PURE__ */ jsx10("td", { "data-binding": i === 0 ? card.id + ".time" : void 0, children: b }),
        /* @__PURE__ */ jsx10("td", { "data-binding": `${card.id}.sample.${i}`, children: card.data.counts[i] })
      ] }, i)) })
    ] })
  ] });
}

// components/RelationshipGraph.tsx
import { Fragment as Fragment5, jsx as jsx11, jsxs as jsxs11 } from "react/jsx-runtime";
function RelationshipGraph({ card, rect }) {
  const nodes = card.data.nodes, edges = card.data.edges, w = rect.width - 34, h = rect.height - 110;
  const positions = graphPositions(nodes, w, h, edges);
  if (!nodes.length) return /* @__PURE__ */ jsx11("div", { className: "empty-graph", children: "No observed relationships in this window" });
  return /* @__PURE__ */ jsxs11(Fragment5, { children: [
    /* @__PURE__ */ jsxs11("svg", { className: "chart", viewBox: `0 0 ${w} ${h}`, role: "img", "aria-label": "Directed system relationship graph", children: [
      /* @__PURE__ */ jsx11("defs", { children: Object.entries(relationColors).map(([k, color]) => /* @__PURE__ */ jsx11("marker", { id: `${card.id}_${k}`, markerWidth: "7", markerHeight: "7", refX: "6", refY: "3.5", orient: "auto", children: /* @__PURE__ */ jsx11("path", { d: "M0,0 L7,3.5 L0,7 Z", fill: color }) }, k)) }),
      edges.map((e, i) => {
        const a = positions[e.source], b = positions[e.target];
        let d;
        if (e.source === e.target) d = `M${a.x + 60},${a.y - 12} C${a.x + 105},${a.y - 52} ${a.x + 105},${a.y + 52} ${a.x + 62},${a.y + 12}`;
        else if (nodes.length > 30) {
          const side = b.x >= a.x ? 1 : -1, port = (i % 5 - 2) * 3;
          const sx = a.x + side * 62, tx = b.x - side * 62;
          const laneA = a.x + side * 78, laneB = b.x - side * 78;
          const laneY = b.y + (a.y > b.y ? 38 : -38) + (i % 3 - 1) * 2;
          d = `M${sx},${a.y + port} L${laneA},${a.y + port} L${laneA},${laneY} L${laneB},${laneY} L${laneB},${b.y + port} L${tx},${b.y + port}`;
        } else {
          const dx = b.x - a.x, dy = b.y - a.y, len = Math.hypot(dx, dy) || 1;
          const bend = 12 + Object.keys(relationColors).indexOf(e.kind) * 11;
          const cx = (a.x + b.x) / 2 - dy / len * bend, cy = (a.y + b.y) / 2 + dx / len * bend;
          const boundary = (p) => {
            const vx = cx - p.x, vy = cy - p.y;
            const k = Math.min(62 / Math.max(Math.abs(vx), 1e-3), 30 / Math.max(Math.abs(vy), 1e-3));
            return { x: p.x + vx * k, y: p.y + vy * k };
          };
          const start = boundary(a), end = boundary(b);
          d = `M${start.x},${start.y} Q${cx},${cy} ${end.x},${end.y}`;
        }
        return /* @__PURE__ */ jsx11(
          "path",
          {
            ...field(`${card.id}.edge.${e.id}`),
            d,
            className: "graph-edge",
            stroke: relationColors[e.kind],
            strokeDasharray: e.kind === "calls" ? void 0 : e.kind === "hosts" ? "6 3" : "2 3",
            markerEnd: `url(#${card.id}_${e.kind})`
          },
          e.id
        );
      }),
      nodes.map((node) => {
        const { x, y } = positions[node.id];
        return /* @__PURE__ */ jsxs11(
          "g",
          {
            className: "node",
            transform: `translate(${x},${y})`,
            ...field(`${card.id}.node.${node.id}`),
            "data-entity-node": `${card.id}.${node.id}`,
            children: [
              /* @__PURE__ */ jsx11("rect", { x: "-60", y: "-28", width: "120", height: "56", rx: node.type === "node" ? 3 : node.type === "pod" ? 9 : 18 }),
              /* @__PURE__ */ jsxs11("text", { y: node.role ? -12 : -3, textAnchor: "middle", children: [
                node.type,
                " ",
                node.id
              ] }),
              node.role && /* @__PURE__ */ jsx11("text", { y: "10", textAnchor: "middle", children: node.role })
            ]
          },
          node.id
        );
      })
    ] }),
    /* @__PURE__ */ jsx11(RelationLegend, { edges })
  ] });
}

// components/RelationshipMatrix.tsx
import { Fragment as Fragment6, jsx as jsx12, jsxs as jsxs12 } from "react/jsx-runtime";
function RelationshipMatrix({ card, rect }) {
  const nodes = card.data.nodes, edges = card.data.edges, w = rect.width - 34, h = rect.height - 110;
  const size = Math.min(28, (h - 100) / Math.max(1, nodes.length), (w - 230) / Math.max(1, nodes.length));
  const ox = Math.max(220, (w - size * nodes.length) / 2), oy = 58, types = Object.keys(relationColors);
  const subdivisions = edges.some((e) => e.kind === "has_instance") ? 3 : 2;
  if (!nodes.length) return /* @__PURE__ */ jsx12("div", { className: "empty-graph", children: "No observed relationships in this window" });
  return /* @__PURE__ */ jsxs12(Fragment6, { children: [
    /* @__PURE__ */ jsxs12("svg", { className: "chart", viewBox: `0 0 ${w} ${h}`, children: [
      /* @__PURE__ */ jsx12("text", { x: "12", y: "17", children: "Row source \u2192 column target" }),
      nodes.map((node, i) => /* @__PURE__ */ jsxs12("g", { children: [
        /* @__PURE__ */ jsxs12("text", { x: ox - 8, y: oy + i * size + size * 0.75, textAnchor: "end", ...field(`${card.id}.node.${node.id}`), children: [
          node.type,
          " ",
          node.id,
          node.role ? " \xB7 " + node.role : ""
        ] }),
        /* @__PURE__ */ jsx12("text", { transform: `translate(${ox + i * size + size * 0.5} ${oy - 7}) rotate(-50)`, children: node.id }),
        /* @__PURE__ */ jsx12("line", { x1: ox, x2: ox + size * nodes.length, y1: oy + i * size, y2: oy + i * size, stroke: "var(--border)" }),
        /* @__PURE__ */ jsx12("line", { x1: ox + i * size, x2: ox + i * size, y1: oy, y2: oy + size * nodes.length, stroke: "var(--border)" })
      ] }, node.id)),
      edges.map((e) => {
        const r = nodes.findIndex((n2) => n2.id === e.source), c = nodes.findIndex((n2) => n2.id === e.target), k = types.indexOf(e.kind);
        return /* @__PURE__ */ jsx12(
          "rect",
          {
            ...field(`${card.id}.edge.${e.id}`),
            x: ox + c * size + 1 + k % subdivisions * size / subdivisions,
            y: oy + r * size + 1 + Math.floor(k / subdivisions) * size / subdivisions,
            width: Math.max(1, size / subdivisions - 2),
            height: Math.max(1, size / subdivisions - 2),
            fill: relationColors[e.kind]
          },
          e.id
        );
      })
    ] }),
    /* @__PURE__ */ jsx12(RelationLegend, { edges })
  ] });
}

// components/AnomalyOnset.tsx
import { jsx as jsx13, jsxs as jsxs13 } from "react/jsx-runtime";
function AnomalyOnset({ card, rect }) {
  const events = card.data.events, w = rect.width - 34, h = rect.height - 140;
  if (!events.length) return /* @__PURE__ */ jsx13("div", { className: "empty-graph", children: "No observed onset readings" });
  const left = 170, right = w - 230, top = 40, bottom = h - 42;
  const lo = Math.min(0, ...events.map((e) => e.minute)), hi = Math.max(lo + 1, ...events.map((e) => e.minute));
  const x = (t) => left + (t - lo) / (hi - lo) * (right - left);
  return /* @__PURE__ */ jsxs13("svg", { className: "chart", viewBox: `0 0 ${w} ${h}`, role: "img", "aria-label": "Observed anomaly onset times", children: [
    /* @__PURE__ */ jsx13("text", { x: "12", y: "18", children: "Entity" }),
    /* @__PURE__ */ jsx13("text", { x: right + 22, y: "18", children: "Onset \xB7 z \xB7 source" }),
    [0, 0.25, 0.5, 0.75, 1].map((t) => {
      const value = lo + t * (hi - lo);
      return /* @__PURE__ */ jsxs13("g", { children: [
        /* @__PURE__ */ jsx13("line", { x1: x(value), x2: x(value), y1: top - 8, y2: bottom + 12, stroke: "var(--border)" }),
        /* @__PURE__ */ jsxs13("text", { x: x(value), y: h - 10, textAnchor: "middle", children: [
          n(value),
          " min"
        ] })
      ] }, t);
    }),
    events.map((e, i) => {
      const y = top + (i + 0.5) * (bottom - top) / events.length;
      const type = { 3: "service", 4: "node", 5: "pod", 6: "external" }[e.entity.length];
      return /* @__PURE__ */ jsxs13("g", { ...field(`${card.id}.event.${i}`), children: [
        /* @__PURE__ */ jsxs13("text", { x: "12", y: y + 4, children: [
          type,
          " ",
          e.entity
        ] }),
        /* @__PURE__ */ jsx13("line", { x1: left, x2: right, y1: y, y2: y, stroke: "var(--border)", strokeDasharray: "2 5" }),
        /* @__PURE__ */ jsx13("circle", { cx: x(e.minute), cy: y, r: "5", fill: "var(--accent)" }),
        /* @__PURE__ */ jsxs13("text", { x: right + 22, y: y + 4, children: [
          n(e.minute),
          "m \xB7 ",
          e.severity,
          " \xB7 ",
          e.source
        ] })
      ] }, i);
    })
  ] });
}

// components/RelationshipPairs.tsx
import { jsx as jsx14, jsxs as jsxs14 } from "react/jsx-runtime";
function RelationshipPairs({ card, rect }) {
  const layout = rect.pair_layout;
  if (!layout) throw new Error("Pair component requires compiled capacity/geometry");
  const { columns, cell_width: cw, cell_height: ch, gap } = layout;
  const w = rect.width - 34, h = rect.height - 110, scale = ch / 100;
  const byId = new Map(card.data.nodes.map((n2) => [n2.id, n2]));
  const edges = [...card.data.edges].sort((a, b) => Number(a.source) - Number(b.source) || Number(a.target) - Number(b.target) || a.kind.localeCompare(b.kind, "en") || a.id.localeCompare(b.id, "en"));
  const connected = new Set(edges.flatMap((e) => [e.source, e.target]));
  const isolates = card.data.nodes.filter((n2) => !connected.has(n2.id)).sort((a, b) => Number(a.id) - Number(b.id));
  const seen = /* @__PURE__ */ new Set();
  const endpoint = (id, x, y) => {
    const node = byId.get(id);
    const key = `${card.id}.node.${id}`, first = !seen.has(id);
    seen.add(id);
    const attributes = first ? field(key) : { "data-binding-ref": key };
    return /* @__PURE__ */ jsxs14("g", { className: "node", "data-pair-node": id, transform: `translate(${x},${y})`, ...attributes, children: [
      /* @__PURE__ */ jsx14("rect", { x: -54 * scale, y: -29 * scale, width: 108 * scale, height: 58 * scale, rx: node.type === "node" ? 3 : 9 }),
      /* @__PURE__ */ jsx14("text", { y: -12 * scale, textAnchor: "middle", children: node.type }),
      /* @__PURE__ */ jsx14("text", { y: 4 * scale, textAnchor: "middle", children: node.id }),
      node.role && /* @__PURE__ */ jsx14("text", { y: 20 * scale, textAnchor: "middle", children: node.role })
    ] });
  };
  if (!edges.length && !isolates.length) return /* @__PURE__ */ jsx14("div", { className: "empty-graph", children: "No observed relationships in this window" });
  const origin = (i) => ({ x: i % columns * (cw + gap), y: Math.floor(i / columns) * (ch + gap) });
  return /* @__PURE__ */ jsxs14("svg", { className: "chart", viewBox: `0 0 ${w} ${h}`, role: "img", "aria-label": "Pairwise directed relationships", children: [
    /* @__PURE__ */ jsx14("defs", { children: Object.entries(relationColors).map(([kind, color]) => /* @__PURE__ */ jsx14(
      "marker",
      {
        id: `${card.id}_pair_${kind}`,
        markerWidth: "7",
        markerHeight: "7",
        refX: "6",
        refY: "3.5",
        orient: "auto",
        children: /* @__PURE__ */ jsx14("path", { d: "M0,0 L7,3.5 L0,7 Z", fill: color })
      },
      kind
    )) }),
    edges.map((edge, i) => {
      const { x, y } = origin(i), mid = ch * 0.6;
      const left = 64 * scale, right = cw - 64 * scale;
      return /* @__PURE__ */ jsxs14(
        "g",
        {
          "data-pair-edge": edge.id,
          "data-source": edge.source,
          "data-target": edge.target,
          "data-relation": edge.kind,
          transform: `translate(${x},${y})`,
          children: [
            /* @__PURE__ */ jsx14("rect", { x: ".5", y: ".5", width: cw - 1, height: ch - 1, rx: "6", fill: "none", stroke: "var(--border)" }),
            endpoint(edge.source, left, mid),
            endpoint(edge.target, right, mid),
            /* @__PURE__ */ jsxs14("g", { ...field(`${card.id}.edge.${edge.id}`), children: [
              /* @__PURE__ */ jsx14("text", { x: cw / 2, y: 18 * scale, textAnchor: "middle", children: edge.kind }),
              /* @__PURE__ */ jsx14(
                "path",
                {
                  d: `M${left + 56 * scale},${mid} L${right - 56 * scale},${mid}`,
                  fill: "none",
                  stroke: relationColors[edge.kind],
                  strokeWidth: "1.6",
                  strokeDasharray: edge.kind === "calls" ? void 0 : "5 3",
                  markerEnd: `url(#${card.id}_pair_${edge.kind})`
                }
              )
            ] })
          ]
        },
        edge.id
      );
    }),
    isolates.map((node, i) => {
      const { x, y } = origin(edges.length + i);
      return /* @__PURE__ */ jsx14(
        "g",
        {
          transform: `translate(${x},${y})`,
          children: endpoint(node.id, cw / 2, ch / 2)
        },
        node.id
      );
    })
  ] });
}

// components/DeploymentGroups.tsx
import { Fragment as Fragment7, jsx as jsx15, jsxs as jsxs15 } from "react/jsx-runtime";
function DeploymentGroups({ card, rect }) {
  const layout = rect.deployment_layout;
  if (!layout) throw new Error("Deployment groups require compiled geometry");
  const { groups, cell_width: cw, member_columns: cols, scale: s } = layout;
  const nodes = new Map(card.data.nodes.map((n2) => [n2.id, n2]));
  const edges = new Map(card.data.edges.map((e) => [e.id, e]));
  const seen = /* @__PURE__ */ new Set();
  const node = (id, x, y) => {
    const n2 = nodes.get(id);
    const key = `${card.id}.node.${id}`, first = !seen.has(id);
    seen.add(id);
    return /* @__PURE__ */ jsxs15(
      "g",
      {
        className: "node",
        "data-membership-node": id,
        transform: `translate(${x},${y})`,
        ...first ? field(key) : { "data-binding-ref": key },
        children: [
          /* @__PURE__ */ jsx15("rect", { width: 126 * s, height: 46 * s, rx: n2.type === "node" ? 3 : 8 }),
          /* @__PURE__ */ jsxs15("text", { x: 63 * s, y: (n2.role ? 19 : 28) * s, textAnchor: "middle", children: [
            n2.type,
            " ",
            id
          ] }),
          n2.role && /* @__PURE__ */ jsx15("text", { x: 63 * s, y: 35 * s, textAnchor: "middle", children: n2.role })
        ]
      }
    );
  };
  const brace = (x, y, h, flip) => /* @__PURE__ */ jsx15(
    "path",
    {
      d: `M12,0 Q3,0 3,10 L3,${h / 2 - 9} Q3,${h / 2} -3,${h / 2} Q3,${h / 2} 3,${h / 2 + 9} L3,${h - 10} Q3,${h} 12,${h}`,
      transform: `translate(${x},${y}) scale(${flip ? -s : s},1)`,
      stroke: "var(--axis)",
      strokeWidth: "1.8",
      fill: "none"
    }
  );
  if (!groups.length) return /* @__PURE__ */ jsx15("div", { className: "empty-graph", children: "No observed deployment relationships in this window" });
  return /* @__PURE__ */ jsx15("svg", { className: "chart", viewBox: `0 0 ${rect.width - 34} ${rect.height - 110}`, role: "img", "aria-label": "Grouped deployment and service instances", children: groups.map((group, i) => {
    const { source, kind, height: h } = group;
    return /* @__PURE__ */ jsxs15("g", { "data-membership-group": source, "data-relation": kind, transform: `translate(${group.x},${group.y})`, children: [
      /* @__PURE__ */ jsx15("rect", { x: ".5", y: ".5", width: cw - 1, height: h - 1, rx: "7", fill: "none", stroke: "var(--border)" }),
      node(source, 12 * s, (h - 46 * s) / 2),
      kind && /* @__PURE__ */ jsxs15(Fragment7, { children: [
        /* @__PURE__ */ jsx15("text", { x: 75 * s, y: (h + 46 * s) / 2 + 13 * s, textAnchor: "middle", style: { fill: relationColors[kind], fontSize: "calc(var(--font)*.625)" }, children: kind === "has_instance" ? "instances" : kind }),
        /* @__PURE__ */ jsx15("text", { x: 147 * s, y: h / 2 + 4 * s, children: ":" }),
        brace(171 * s, 10 * s, h - 20 * s, false),
        brace(cw - 16 * s, 10 * s, h - 20 * s, true)
      ] }),
      group.edges.map((eid, j) => {
        const edge = edges.get(eid);
        if (edge.source !== source || edge.kind !== kind) throw new Error("Membership geometry differs from evidence");
        return /* @__PURE__ */ jsx15(
          "g",
          {
            ...field(`${card.id}.edge.${eid}`),
            "data-membership-edge": eid,
            "data-source": edge.source,
            "data-target": edge.target,
            "data-relation": kind,
            children: node(edge.target, 190 * s + j % cols * 142 * s, 14 * s + Math.floor(j / cols) * 58 * s)
          },
          eid
        );
      })
    ] }, i);
  }) });
}

// components/index.ts
var components = {
  "metric.line": MetricLine,
  "metric.readings": MetricReadings,
  "metric.time_bars": MetricTimeBars,
  "metric.heatmap": MetricHeatmap,
  "trace.paired_bars": TracePairedBars,
  "trace.dumbbell": TraceDumbbell,
  "trace.table": TraceTable,
  "log.timeline": LogTimeline,
  "log.table": LogTable,
  "graph.node_link": RelationshipGraph,
  "graph.matrix": RelationshipMatrix,
  "events.onset": AnomalyOnset,
  "graph.edge_pairs": RelationshipPairs,
  "graph.deployment_groups": DeploymentGroups
};

// dashboard.tsx
import { jsx as jsx16, jsxs as jsxs16 } from "react/jsx-runtime";
function Panel({ card, rect, design: design2 }) {
  const Component = components[rect.component];
  if (!Component) throw new Error("Unregistered dashboard component: " + rect.component);
  const entityType = card.entity ? { 3: "service", 4: "node", 5: "pod", 6: "external" }[card.entity.length] : null;
  let displayed = card;
  if (card.kind === "graph" && !design2.graph?.show_isolates) {
    const connected = new Set(card.data.edges.flatMap((e) => [e.source, e.target]));
    displayed = { ...card, data: { ...card.data, nodes: card.data.nodes.filter((n2) => connected.has(n2.id)) } };
  }
  return /* @__PURE__ */ jsxs16(
    "section",
    {
      className: "panel",
      "data-card": card.id,
      "data-index": rect.index,
      "data-component": rect.component,
      style: { left: rect.x, top: rect.y, width: rect.width, height: rect.height },
      children: [
        /* @__PURE__ */ jsxs16("div", { className: "card-head", children: [
          design2.indexing.visible && /* @__PURE__ */ jsx16("span", { className: "index", children: String(rect.index).padStart(2, "0") }),
          /* @__PURE__ */ jsx16("div", { className: "title", "data-binding": card.id + ".title", children: card.title.split(/(?<=[_.])/).map((part, i) => /* @__PURE__ */ jsxs16(React.Fragment, { children: [
            part,
            /* @__PURE__ */ jsx16("wbr", {})
          ] }, i)) }),
          card.entity && /* @__PURE__ */ jsxs16("span", { className: "identity", "data-binding": card.id + ".entity", children: [
            entityType,
            " ",
            card.entity
          ] })
        ] }),
        card.unit && /* @__PURE__ */ jsx16("div", { className: "unit", "data-binding": card.id + ".unit", children: card.unit.replaceAll("_", " ") }),
        /* @__PURE__ */ jsx16(Component, { card: displayed, rect }),
        !["graph", "events"].includes(card.kind) && /* @__PURE__ */ jsx16(Details, { card })
      ]
    }
  );
}
function Dashboard({ cards, design: design2, scene: scene2 }) {
  return /* @__PURE__ */ jsxs16("main", { style: { position: "relative", width: scene2.width, height: scene2.height }, children: [
    /* @__PURE__ */ jsxs16("header", { children: [
      /* @__PURE__ */ jsx16("strong", { children: "Telemetry / Incident overview" }),
      /* @__PURE__ */ jsx16("span", { children: "METRICS \xB7 TRACES \xB7 LOGS \xB7 RELATIONSHIPS" })
    ] }),
    scene2.rectangles.map((rect) => /* @__PURE__ */ jsx16(Panel, { card: cards.find((c) => c.id === rect.card), rect, design: design2 }, rect.card))
  ] });
}

// render.tsx
import { jsx as jsx17 } from "react/jsx-runtime";
var sha = (buffer) => createHash("sha256").update(buffer).digest("hex");
var out = path.resolve(process.argv[2]);
var web = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
var json = async (name) => JSON.parse(await fs.readFile(path.join(out, name), "utf8"));
var evidence = await json("evidence.json");
var design = await json("design.json");
var scene = await json("geometry.json");
var css = await fs.readFile(path.join(web, "style.css"), "utf8");
var font = await fs.readFile(path.join(web, "assets/DejaVuSans.ttf"));
var style = `@font-face{font-family:DashboardSans;src:url(data:font/ttf;base64,${font.toString("base64")})} :root{--font:${design.font_size}px} ${css}`;
var markup = renderToStaticMarkup(/* @__PURE__ */ jsx17(Dashboard, { cards: evidence.cards, design, scene }));
var html = '<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Telemetry dashboard</title><style>' + style + '</style></head><body class="' + design.theme + '">' + markup + "</body></html>";
await fs.writeFile(path.join(out, "dashboard.html"), html);
var started = performance.now();
var browser = await chromium.launch({ headless: true, args: ["--disable-gpu", "--disable-dev-shm-usage", "--no-sandbox", "--num-raster-threads=1"] });
try {
  const context = await browser.newContext({ viewport: { width: scene.width, height: scene.height }, deviceScaleFactor: design.scale, locale: "en-US", timezoneId: "UTC", reducedMotion: "reduce", colorScheme: design.theme === "dark" ? "dark" : "light" });
  await context.route("**/*", (route) => route.abort());
  const page = await context.newPage();
  const errors = [];
  page.on("pageerror", (error) => errors.push(String(error)));
  await page.setContent(html, { waitUntil: "load" });
  await page.evaluate(() => document.fonts.ready);
  const overlay = await page.evaluate((links) => {
    const ns = "http://www.w3.org/2000/svg", svg = document.createElementNS(ns, "svg");
    svg.setAttribute("id", "ownership-overlay");
    svg.style.cssText = "position:absolute;left:0;top:0;width:100%;height:100%;pointer-events:none";
    const report = [];
    for (const b of links) {
      const card = document.querySelector(`[data-card="${b.card}"]`), node = document.querySelector(`[data-entity-node="${b.graph}.${b.entity}"]`);
      if (!node) throw new Error("Ownership overlay requires node-link graph and visible owner");
      const a = card.getBoundingClientRect(), z = node.getBoundingClientRect();
      const x1 = a.right, y1 = a.top + 18, x2 = z.x + z.width / 2, y2 = z.y;
      const g = document.querySelector(`[data-card="${b.graph}"]`).getBoundingClientRect();
      const points = b.route === "gutter" ? [
        [a.right - 12, a.top],
        [a.right - 12, a.top - 7],
        [g.left - 7, a.top - 7],
        [g.left - 7, y2],
        [x2, y2]
      ] : [[x1, y1], [x2, y2]];
      const crosses = (r, s, t) => {
        let enter = 0, leave = 1;
        for (const [origin, delta, low, high] of [[s[0], t[0] - s[0], r.left, r.right], [s[1], t[1] - s[1], r.top, r.bottom]]) {
          if (Math.abs(delta) < 1e-9) {
            if (origin <= low || origin >= high) return false;
          } else {
            let lo = (low - origin) / delta, hi = (high - origin) / delta;
            if (lo > hi) [lo, hi] = [hi, lo];
            enter = Math.max(enter, lo);
            leave = Math.min(leave, hi);
          }
        }
        return enter < leave;
      };
      for (const p of document.querySelectorAll("[data-card]")) {
        if (![b.card, b.graph].includes(p.getAttribute("data-card")) && points.slice(1).some((t, i) => crosses(p.getBoundingClientRect(), points[i], t)))
          throw new Error("Ownership connector crosses an unrelated component; revise the layout");
      }
      const line = document.createElementNS(ns, "path");
      line.setAttribute("class", "ownership");
      line.setAttribute("data-ownership", b.card);
      line.setAttribute("d", points.map((p, i) => `${i ? "L" : "M"}${p[0]},${p[1]}`).join(" "));
      svg.append(line);
      if (b.route !== "gutter") {
        const label = document.createElementNS(ns, "text");
        label.textContent = "observation of";
        label.setAttribute("x", String((x1 + x2) / 2));
        label.setAttribute("y", String((y1 + y2) / 2 - 4));
        svg.append(label);
      }
      report.push({ card: b.card, entity: b.entity, graph: b.graph, route: b.route || "direct", points, x1, y1, x2, y2 });
    }
    if (links.length) document.querySelector("main").append(svg);
    return report;
  }, design.bindings);
  const audit = await page.evaluate((expected) => {
    const box = (e) => {
      const b = e.getBoundingClientRect();
      return { x: b.x, y: b.y, width: b.width, height: b.height };
    };
    const panels = [...document.querySelectorAll("[data-card]")].map((e) => ({ card: e.getAttribute("data-card"), ...box(e) }));
    const issues = [];
    const bindings = [...document.querySelectorAll("[data-binding]")].map((e) => {
      const b = box(e), key = e.getAttribute("data-binding"), p = e.closest("[data-card]"), pb = box(p), style2 = getComputedStyle(e);
      if (!b.width || !b.height || style2.display === "none" || style2.visibility === "hidden" || Number(style2.opacity) === 0) issues.push("invisible binding " + key);
      if (b.x < pb.x - 1 || b.y < pb.y - 1 || b.x + b.width > pb.x + pb.width + 1 || b.y + b.height > pb.y + pb.height + 1) issues.push("binding outside panel " + key);
      return { key, card: p.getAttribute("data-card"), tag: e.tagName, ...b };
    });
    for (const key of expected) if (bindings.filter((b) => b.key === key).length !== 1) issues.push("missing/duplicate binding " + key);
    const references = [...document.querySelectorAll("[data-binding-ref]")].map((e) => {
      const key = e.getAttribute("data-binding-ref"), b = box(e), p = box(e.closest("[data-card]"));
      const style2 = getComputedStyle(e);
      if (!expected.includes(key) || !key.includes(".node.")) issues.push("unknown repeated node " + key);
      if (!b.width || !b.height || style2.display === "none" || style2.visibility === "hidden" || Number(style2.opacity) === 0)
        issues.push("invisible repeated node " + key);
      if (b.x < p.x - 1 || b.y < p.y - 1 || b.x + b.width > p.x + p.width + 1 || b.y + b.height > p.y + p.height + 1)
        issues.push("repeated node outside panel " + key);
      return { key, ...b };
    });
    const pairs = [...document.querySelectorAll("[data-pair-edge]")].map((e) => ({
      card: e.closest("[data-card]").getAttribute("data-card"),
      id: e.getAttribute("data-pair-edge"),
      source: e.getAttribute("data-source"),
      target: e.getAttribute("data-target"),
      kind: e.getAttribute("data-relation"),
      endpoints: [...e.querySelectorAll("[data-pair-node]")].map((n2) => n2.getAttribute("data-pair-node"))
    }));
    for (const pair of pairs) if (pair.endpoints.join("|") !== [pair.source, pair.target].join("|")) issues.push("pair endpoint mismatch " + pair.id);
    const memberships = [...document.querySelectorAll("[data-membership-edge]")].map((e) => {
      const group = e.closest("[data-membership-group]");
      const item = {
        card: e.closest("[data-card]").getAttribute("data-card"),
        id: e.getAttribute("data-membership-edge"),
        source: e.getAttribute("data-source"),
        target: e.getAttribute("data-target"),
        kind: e.getAttribute("data-relation")
      };
      const owner = group.querySelector(":scope > [data-membership-node]")?.getAttribute("data-membership-node");
      const members = [...e.querySelectorAll("[data-membership-node]")].map((n2) => n2.getAttribute("data-membership-node"));
      if (owner !== item.source || group.getAttribute("data-relation") !== item.kind || members.join("|") !== item.target)
        issues.push("membership endpoint mismatch " + item.id);
      return item;
    });
    for (const e of document.querySelectorAll(".panel,.title,.template,.detail,.unit")) {
      if (e.scrollWidth > e.clientWidth + 2 || e.scrollHeight > e.clientHeight + 2) issues.push("overflow " + e.closest("[data-card]")?.getAttribute("data-card") + " " + e.className);
    }
    for (let i = 0; i < panels.length; i++) {
      const a = panels[i];
      if (a.x < 0 || a.y < 0 || a.x + a.width > innerWidth + 0.5 || a.y + a.height > innerHeight + 0.5) issues.push("out of viewport " + a.card);
      for (let j = i + 1; j < panels.length; j++) {
        const b = panels[j];
        if (a.x < b.x + b.width && b.x < a.x + a.width && a.y < b.y + b.height && b.y < a.y + a.height) issues.push("panel overlap " + a.card + " " + b.card);
      }
    }
    for (const el of document.querySelectorAll(".panel svg text")) {
      const b = box(el), p = box(el.closest("[data-card]"));
      if (b.x < p.x - 1 || b.y < p.y - 1 || b.x + b.width > p.x + p.width + 1 || b.y + b.height > p.y + p.height + 1) issues.push("SVG text outside " + el.textContent);
    }
    for (const panel of document.querySelectorAll("[data-card]")) {
      const nodes = [...panel.querySelectorAll("[data-entity-node],[data-pair-node],[data-membership-node]")].map((e) => ({ id: e.getAttribute("data-entity-node") ?? e.getAttribute("data-pair-node") ?? e.getAttribute("data-membership-node"), ...box(e) }));
      for (let i = 0; i < nodes.length; i++) for (let j = i + 1; j < nodes.length; j++) {
        const a = nodes[i], b = nodes[j];
        if (a.x < b.x + b.width && b.x < a.x + a.width && a.y < b.y + b.height && b.y < a.y + a.height) issues.push("graph node overlap " + a.id + " " + b.id);
      }
    }
    return { panels, bindings, references, pairs, memberships, issues };
  }, scene.expected_bindings);
  for (const rect of scene.rectangles.filter((r) => r.component === "graph.edge_pairs")) {
    const expected = evidence.cards.find((c) => c.id === rect.card).data.edges;
    const actual = audit.pairs.filter((p) => p.card === rect.card);
    if (actual.length !== expected.length) audit.issues.push("pair edge count mismatch " + rect.card);
    for (const e of expected) if (actual.filter((a) => a.id === e.id && a.source === e.source && a.target === e.target && a.kind === e.kind).length !== 1)
      audit.issues.push("missing/changed pair edge " + rect.card + "." + e.id);
  }
  for (const rect of scene.rectangles.filter((r) => r.component === "graph.deployment_groups")) {
    const expected = evidence.cards.find((c) => c.id === rect.card).data.edges;
    const actual = audit.memberships.filter((p) => p.card === rect.card);
    if (actual.length !== expected.length) audit.issues.push("membership count mismatch " + rect.card);
    for (const e of expected) if (actual.filter((a) => a.id === e.id && a.source === e.source && a.target === e.target && a.kind === e.kind).length !== 1)
      audit.issues.push("missing/changed membership " + rect.card + "." + e.id);
  }
  audit.issues.push(...errors);
  const completeHtml = await page.content();
  await fs.writeFile(path.join(out, "dashboard.html"), completeHtml);
  const png = await page.screenshot({ path: path.join(out, "dashboard.png"), fullPage: false, animations: "disabled" });
  const manifest = {
    schema: "RenderManifestV1",
    status: audit.issues.length ? "failed" : "passed",
    ...scene,
    card_count: evidence.cards.length,
    binding_count: audit.bindings.length,
    renderer_seconds: (performance.now() - started) / 1e3,
    browser_version: browser.version(),
    gpu_disabled: true,
    font_sha256: sha(font),
    bundle_sha256: sha(await fs.readFile(fileURLToPath(import.meta.url))),
    css_sha256: sha(css),
    dependency_lock_sha256: sha(await fs.readFile(path.join(web, "package-lock.json"))),
    html_sha256: sha(completeHtml),
    png_sha256: sha(png),
    scale: design.scale,
    source_png: { width: Math.round(scene.width * design.scale), height: Math.round(scene.height * design.scale) },
    evidence_scope: "Only projected CanvasEvidenceV1 fields. Not a whole historical RCA prompt.",
    overlay,
    audit
  };
  await fs.writeFile(path.join(out, "manifest.json"), JSON.stringify(manifest, null, 2) + "\n");
  if (audit.issues.length) throw new Error("Render audit failed: " + audit.issues.join("; "));
  console.log(`rendered ${evidence.cards.length} cards / ${audit.bindings.length} field bindings`);
} finally {
  await browser.close();
}
