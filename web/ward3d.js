// Schematic 3D view of Ward 9 drawn in SVG (isometric). Not surveyed geometry.
// Columns: each drain gateway, height = its drain state. Water plane: the engine's P(cascade) (a belief, not a measured depth).
(function () {
  const COLOR = { calm: "#3fb97a", elevated: "#fab219", high: "#d03b3b", UNKNOWN: "#6b6a63", "no reading": "#4a4944" };
  const LABEL = { calm: "calm", elevated: "rising", high: "high", UNKNOWN: "silent", "no reading": "no data" };
  const HEIGHT = { calm: 14, elevated: 34, high: 58, UNKNOWN: 2, "no reading": 6 };
  // Footprints on a 10 x 10 ward grid: [x0, x1, y0, y1]
  const FOOT = { G1: [1, 4.2, 1, 5], G2: [5.8, 9, 1, 5], G3: [1, 9, 7, 8.6] };
  const WATER_MAX = 52;
  const S = 24;
  const OX = 320, OY = 120;

  const project = (x, y, z) => [OX + (x - y) * S * 0.866, OY + (x + y) * S * 0.5 - z];
  const poly = (corners) => corners.map((c) => project(c[0], c[1], c[2]).map((v) => v.toFixed(1)).join(",")).join(" ");

  function shade(hex, f) {
    const n = parseInt(hex.slice(1), 16);
    const ch = [(n >> 16) & 255, (n >> 8) & 255, n & 255].map((v) => Math.max(0, Math.min(255, Math.round(v * f))));
    return "#" + ch.map((v) => v.toString(16).padStart(2, "0")).join("");
  }

  function column(name, state) {
    const [x0, x1, y0, y1] = FOOT[name];
    const h = HEIGHT[state] ?? HEIGHT["no reading"];
    const base = COLOR[state] ?? COLOR["no reading"];
    const dashed = state === "UNKNOWN" ? ' stroke-dasharray="5 4"' : "";
    const top = [[x0, y0, h], [x1, y0, h], [x1, y1, h], [x0, y1, h]];
    const right = [[x1, y0, 0], [x1, y1, 0], [x1, y1, h], [x1, y0, h]];
    const left = [[x0, y1, 0], [x1, y1, 0], [x1, y1, h], [x0, y1, h]];
    const lx = project((x0 + x1) / 2, (y0 + y1) / 2, h)[0];
    const ly = project((x0 + x1) / 2, (y0 + y1) / 2, h)[1] - 12;
    return `
      <g>
        <polygon points="${poly(left)}" fill="${shade(base, 0.6)}" fill-opacity=".92" stroke="${shade(base, 0.45)}"${dashed}/>
        <polygon points="${poly(right)}" fill="${shade(base, 0.82)}" fill-opacity=".92" stroke="${shade(base, 0.45)}"${dashed}/>
        <polygon points="${poly(top)}" fill="${base}" fill-opacity=".95" stroke="${shade(base, 0.5)}"${dashed}/>
        <text x="${lx.toFixed(1)}" y="${ly.toFixed(1)}" text-anchor="middle" fill="#f0efec" font-size="13" font-weight="600">${name} · ${LABEL[state] ?? "no data"}</text>
      </g>`;
  }

  function sortKey(name) {
    const [x0, x1, y0, y1] = FOOT[name];
    return x0 + x1 + y0 + y1;
  }

  window.renderWard3D = function renderWard3D(svg, opts) {
    const states = opts.states || {};
    const silent = new Set(opts.silent || []);
    const pc = Math.max(0, Math.min(1, opts.pc ?? 0));
    const waterZ = pc * WATER_MAX;
    const ground = [[0, 0, 0], [10, 0, 0], [10, 10, 0], [0, 10, 0]];

    const grid = [];
    for (let i = 0; i <= 10; i++) {
      grid.push(`<line x1="${project(i, 0, 0)[0]}" y1="${project(i, 0, 0)[1]}" x2="${project(i, 10, 0)[0]}" y2="${project(i, 10, 0)[1]}" stroke="#34332f" stroke-width="1"/>`);
      grid.push(`<line x1="${project(0, i, 0)[0]}" y1="${project(0, i, 0)[1]}" x2="${project(10, i, 0)[0]}" y2="${project(10, i, 0)[1]}" stroke="#34332f" stroke-width="1"/>`);
    }

    const names = Object.keys(FOOT).sort((a, b) => sortKey(a) - sortKey(b));
    const columns = names.map((n) => {
      const st = silent.has(n) ? "UNKNOWN" : (states[n] || "no reading");
      return column(n, st);
    });

    const pin = project(5, 6.4, 0);
    const pinTop = project(5, 6.4, 46);

    svg.setAttribute("viewBox", "0 0 640 330");
    svg.innerHTML = `
      <defs>
        <linearGradient id="g-ground" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stop-color="#2a2a27"/><stop offset="1" stop-color="#1c1c1a"/>
        </linearGradient>
      </defs>
      <polygon points="${poly(ground)}" fill="url(#g-ground)" stroke="#45443f" stroke-width="1.5"/>
      ${grid.join("")}
      ${columns.join("")}
      <polygon points="${poly([[0, 0, waterZ], [10, 0, waterZ], [10, 10, waterZ], [0, 10, waterZ]])}"
        fill="#3987e5" fill-opacity="${(0.12 + 0.22 * pc).toFixed(2)}" stroke="#5ea0f0" stroke-opacity=".55" stroke-width="1"/>
      <line x1="${pin[0]}" y1="${pin[1]}" x2="${pinTop[0]}" y2="${pinTop[1]}" stroke="#f0efec" stroke-width="2"/>
      <circle cx="${pinTop[0]}" cy="${pinTop[1]}" r="5" fill="#f0efec"/>
      <text x="${pinTop[0] + 10}" y="${pinTop[1] + 4}" fill="#c3c2b7" font-size="12">Ambazari underpass (fictional)</text>
      <text x="16" y="312" fill="#c3c2b7" font-size="12">Columns: drain state per gateway · Blue water: engine P(cascade) = ${(pc * 100).toFixed(1)}%</text>
      <text x="16" y="328" fill="#8c8b82" font-size="11">Schematic layout, not to scale. Water is a belief, not a measured depth.</text>`;
  };
})();
