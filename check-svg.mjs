// SVG self-audit: every <text> must sit inside its canvas and no two may
// overlap by more than 2px. Renders each figure in headless Chrome and reads
// getBBox() from the live layout engine — no hand-estimated metrics.
import { readFileSync, readdirSync, writeFileSync, unlinkSync } from "node:fs";
import { execFileSync } from "node:child_process";
import { join, resolve } from "node:path";
import { tmpdir } from "node:os";

const ASSETS = resolve("docs/assets");
const CHROME = process.env.CHROME_PATH ||
  "C:/Program Files/Google/Chrome/Application/chrome.exe";

const figures = readdirSync(ASSETS).filter((f) => f.endsWith(".svg")).sort();
if (figures.length === 0) {
  console.error("no SVGs found in docs/assets");
  process.exit(1);
}

const payload = figures.map((name) => ({
  name,
  svg: readFileSync(join(ASSETS, name), "utf8").replace(/<\?xml[^>]*\?>/g, ""),
}));

const html = `<!doctype html><html><body style="margin:0;background:#000">
<div id="stage"></div><pre id="result">PENDING</pre>
<script>
const figures = ${JSON.stringify(payload)};
const out = [];
for (const fig of figures) {
  const holder = document.createElement("div");
  holder.innerHTML = fig.svg;
  document.getElementById("stage").appendChild(holder);
  const svg = holder.querySelector("svg");
  const w = parseFloat(svg.getAttribute("width"));
  const h = parseFloat(svg.getAttribute("height"));
  const boxes = [...svg.querySelectorAll("text")].map((t) => {
    const b = t.getBBox();
    return { label: t.textContent, x: +b.x.toFixed(1), y: +b.y.toFixed(1),
             w: +b.width.toFixed(1), h: +b.height.toFixed(1) };
  });
  out.push({ name: fig.name, width: w, height: h, boxes });
}
document.getElementById("result").textContent = "RESULT:" + JSON.stringify(out);
</script></body></html>`;

const page = join(tmpdir(), "svg-audit.html");
writeFileSync(page, html, "utf8");

const dom = execFileSync(CHROME, [
  "--headless=new", "--disable-gpu", "--no-sandbox", "--allow-file-access-from-files",
  "--virtual-time-budget=6000", "--dump-dom", "file:///" + page.replace(/\\/g, "/"),
], { encoding: "utf8", maxBuffer: 64 * 1024 * 1024 });

const match = dom.match(/RESULT:(\[[\s\S]*?\])<\/pre>/);
if (!match) {
  console.error("audit page did not produce results");
  process.exit(1);
}

const results = JSON.parse(match[1].replace(/&quot;/g, '"').replace(/&amp;/g, "&"));
let issues = 0;
let totalText = 0;

for (const fig of results) {
  const problems = [];
  for (const b of fig.boxes) {
    totalText += 1;
    if (b.x < -0.5 || b.y < -0.5 || b.x + b.w > fig.width + 0.5 || b.y + b.h > fig.height + 0.5) {
      problems.push(`OUTSIDE ${JSON.stringify(b.label)} at (${b.x},${b.y}) ${b.w}x${b.h}`);
    }
  }
  for (let i = 0; i < fig.boxes.length; i += 1) {
    for (let j = i + 1; j < fig.boxes.length; j += 1) {
      const a = fig.boxes[i];
      const c = fig.boxes[j];
      const ox = Math.min(a.x + a.w, c.x + c.w) - Math.max(a.x, c.x);
      const oy = Math.min(a.y + a.h, c.y + c.h) - Math.max(a.y, c.y);
      if (ox > 2 && oy > 2) {
        problems.push(`OVERLAP ${JSON.stringify(a.label)} <> ${JSON.stringify(c.label)} (${ox.toFixed(1)}x${oy.toFixed(1)})`);
      }
    }
  }
  issues += problems.length;
  console.log(`${fig.name.padEnd(18)} ${String(fig.boxes.length).padStart(3)} text nodes  ${problems.length} issues`);
  for (const p of problems.slice(0, 12)) console.log("   " + p);
}

try { unlinkSync(page); } catch {}
console.log(`\ntotal: ${totalText} text nodes, ${issues} issues across ${results.length} figures`);
process.exit(issues === 0 ? 0 : 1);
