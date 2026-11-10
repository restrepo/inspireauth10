"""Write the board as one self-contained HTML file.

The page (board/index.html), its datasets and d3 are inlined, with a small
implementation of the `dash` API the page uses, so the file opens in any browser
with no network.

Usage: python reproduce/standalone.py dash/ board.html --set DATE=2026-11-08
--set KEY=VALUE (repeatable) fills @@KEY@@ in the page; DATE is the download date.
"""
import html
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from board_datasets import DATASETS

HERE = Path(__file__).resolve().parent
D3 = HERE / 'board/vendor/d3.v7.9.0.min.js'

TOKENS = """
:root {
  color-scheme: light dark;
  --color-fg: #1f1e1d; --color-fg-muted: #6b6966; --color-bg: #faf9f5; --color-panel: #ffffff;
  --color-border-line: #e3e0d8; --color-ok: #2e7d4f; --color-warn: #a86a10; --color-bad: #b3362f;
  --font-anthropic-sans: system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
  --font-anthropic-serif: Georgia, "Times New Roman", serif;
  --cds-border: #e3e0d8; --cds-text-secondary: #6b6966;
  --cds-chart-axis: #8a8781; --cds-chart-grid: #ebe8e1; --cds-chart-muted: #d9d5cc; --cds-chart-reference: #8a8781;
  --cds-surface-popover: #ffffff; --cds-shadow-popover: 0 4px 16px rgba(0,0,0,.12);
  --cds-font-size-caption: 12px; --cds-font-size-body: 14px; --cds-font-size-heading: 17px; --cds-font-size-title: 28px;
  --cds-font-weight-medium: 550; --cds-radius: 10px; --cds-dur-slow: 300ms;
  --cds-gap-xs: 4px; --cds-gap-sm: 8px; --cds-gap-md: 12px; --cds-gap-lg: 20px;
  --cds-pad-xs: 4px; --cds-pad-sm: 8px; --cds-pad-md: 12px; --cds-pad-lg: 20px;
}
@media (prefers-color-scheme: dark) {
  :root {
    --color-fg: #ecebe7; --color-fg-muted: #a6a39c; --color-bg: #1c1b19; --color-panel: #262523;
    --color-border-line: #3a3936; --color-ok: #5cb880; --color-warn: #d9a441; --color-bad: #e06c63;
    --cds-border: #3a3936; --cds-text-secondary: #a6a39c;
    --cds-chart-axis: #8f8c86; --cds-chart-grid: #34332f; --cds-chart-muted: #4a4844; --cds-chart-reference: #8f8c86;
    --cds-surface-popover: #2f2e2b; --cds-shadow-popover: 0 4px 16px rgba(0,0,0,.5);
  }
}
html { background: var(--color-bg); }
.sa-body { margin: 0; background: var(--color-bg); color: var(--color-fg);
  font-family: var(--font-anthropic-sans); font-size: var(--cds-font-size-body); }
#dash-root { padding: 24px 16px 48px; }
#dash-root [hidden] { display: none !important; }
.sa-sources { max-width: 84rem; margin: 32px auto 0; color: var(--color-fg-muted); font-size: 13px; line-height: 1.5; }
.sa-sources h2 { font-size: var(--cds-font-size-heading); color: var(--color-fg); font-weight: 500; }
.sa-sources a { color: inherit; }
.sa-sources li { margin-bottom: 4px; }
"""

# Stand-in for the dashboard type's `dash` API, over the inlined datasets.
SHIM = """
(() => {
  const DATA = JSON.parse(document.getElementById('sa-data').textContent);
  const calcs = {}, drawers = {}, sizes = new WeakMap();
  const colorsLight = ['#3266ad', '#d97a2b', '#3a9a5b', '#c2414b', '#7b5ea7', '#8c6d46', '#c35d9b', '#5f7384'];
  const colorsDark = ['#6f9be0', '#f0a05c', '#64c287', '#e57980', '#a68bd4', '#bf9a6e', '#e38cc0', '#93a6b6'];
  const dark = window.matchMedia && matchMedia('(prefers-color-scheme: dark)').matches;
  const rowsOf = (id) => {
    if (id in DATA) return DATA[id];
    if (id in calcs) {
      const c = calcs[id];
      if (!('value' in c)) c.value = c.fn(...c.inputs.map(rowsOf));
      return c.value;
    }
    return undefined;
  };
  const run = (name, el) => {
    try { drawers[name](el); } catch (e) { console.error(name, e); }
    sizes.set(el, el.clientWidth);
  };
  const ro = new ResizeObserver((entries) => {
    for (const en of entries) {
      const el = en.target;
      if (sizes.get(el) !== el.clientWidth && drawers[el.dataset.draw]) run(el.dataset.draw, el);
    }
  });
  window.dash = {
    colors: dark ? colorsDark : colorsLight,
    data(id) {
      const d = rowsOf(id);
      if (d === undefined) return { status: 'missing', data: [], rows: [], columns: [], refreshing: false, meta: [] };
      const columns = Array.isArray(d) && d.length ? Object.keys(d[0]) : [];
      return { status: 'ok', data: d, rows: d, columns, value: d, refreshing: false, meta: [] };
    },
    calc(id, spec) { calcs[id] = { inputs: spec.inputs || [], fn: spec.fn }; },
    loader() {},
    draw(name, fn) {
      if (fn) drawers[name] = fn;
      if (!drawers[name]) return;
      document.querySelectorAll(`[data-draw="${CSS.escape(name)}"]`).forEach((el) => {
        run(name, el);
        if (fn) ro.observe(el);
      });
    },
    onData(fn) { fn(); },
    refresh() {},
    params: () => ({}), setParams() {}, resetParams() {},
    setLink(name) { history.replaceState(null, '', '#' + name); },
  };
})();
"""


# placeholders of the worldwide board; a regional board sets them (reproduce/regional_boards.py)
DEFAULTS = {'SCOPE': 'worldwide', 'SCOPE_NOTE': '', 'TOTAL': 'World', 'TITLE': 'Worldwide'}


def script_json(obj):
    return json.dumps(obj, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/')


def main(dash_dir, out_path, values=None):
    page = (HERE / 'board/index.html').read_text(encoding='utf-8')
    page = page.replace('<meta name="dash-one-writer">\n', '')
    values = {**DEFAULTS, **(values or {})}
    title = values['TITLE']
    for key, value in values.items():
        page = page.replace(f'@@{key}@@', value)
    if '@@' in page:
        raise SystemExit('unfilled placeholder in the page: pass --set DATE=YYYY-MM-DD')
    data = {k: json.load(open(Path(dash_dir) / f'{k}.json', encoding='utf-8')) for k in DATASETS}
    built = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    sources = ''.join(
        f'<li><b>{html.escape(t)}</b> ({len(data[k])} rows): {html.escape(d)} '
        f'<a href="#" data-sa-download="{k}">Download JSON</a></li>'
        for k, (t, d) in DATASETS.items())
    doc = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>HECAP {html.escape(title)}</title>
<style>{TOKENS}</style>
</head>
<body class="sa-body">
<script>{D3.read_text(encoding='utf-8')}</script>
<script type="application/json" id="sa-data">{script_json(data)}</script>
<script>{SHIM}</script>
<div id="dash-root">
{page}
<section class="sa-sources">
<h2>Sources</h2>
<p>Computed by <code>reproduce/indicators.py</code> of restrepo/inspireauth10 from the tables in <code>data/</code>
(INSPIRE-HEP, CC0), with genders from genderize-offline 0.1.0 (World Gender Name Dictionary 2.0). Built {built}.
Self-contained page; d3 v7.9.0 (ISC licence) is included.</p>
<ul>{sources}</ul>
</section>
</div>
<script>
document.querySelectorAll('[data-sa-download]').forEach((a) => a.addEventListener('click', (e) => {{
  e.preventDefault();
  const k = a.dataset.saDownload;
  const blob = new Blob([JSON.stringify(dash.data(k).data, null, 1)], {{ type: 'application/json' }});
  const u = URL.createObjectURL(blob), t = document.createElement('a');
  t.href = u; t.download = k + '.json'; t.click(); setTimeout(() => URL.revokeObjectURL(u), 1000);
}}));
</script>
</body>
</html>
"""
    Path(out_path).write_text(doc, encoding='utf-8')
    print(f'wrote {out_path} ({len(doc.encode()) / 1e3:.0f} kB)')


if __name__ == '__main__':
    argv = sys.argv[1:]
    values = {}
    while '--set' in argv:
        i = argv.index('--set')
        k, v = argv[i + 1].split('=', 1)
        values[k] = v
        del argv[i:i + 2]
    main(*argv[:2], values)
