/* Estilos para el reporte ejecutivo standalone HTML.
   Se inyecta vía: pandoc report.md -o report.html --standalone --self-contained --css=report.html-style.css.tpl */

:root {
  --color-bg: #ffffff;
  --color-fg: #1f2937;
  --color-muted: #6b7280;
  --color-border: #e5e7eb;
  --color-code-bg: #f3f4f6;
  --color-green-bg: #d1fae5;
  --color-green-fg: #065f46;
  --color-yellow-bg: #fef3c7;
  --color-yellow-fg: #92400e;
  --color-red-bg: #fee2e2;
  --color-red-fg: #991b1b;
  --color-link: #2563eb;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
  color: var(--color-fg);
  background: var(--color-bg);
  max-width: 960px;
  margin: 40px auto;
  padding: 0 24px;
  line-height: 1.55;
}

h1, h2, h3 {
  color: var(--color-fg);
  border-bottom: 1px solid var(--color-border);
  padding-bottom: 6px;
}

h1 { font-size: 28px; margin-top: 0; }
h2 { font-size: 22px; margin-top: 36px; }
h3 { font-size: 18px; }

a { color: var(--color-link); text-decoration: none; }
a:hover { text-decoration: underline; }

table {
  border-collapse: collapse;
  width: 100%;
  margin: 16px 0 24px 0;
  font-size: 14px;
}

th, td {
  border: 1px solid var(--color-border);
  padding: 8px 12px;
  text-align: left;
  vertical-align: top;
}

th {
  background: var(--color-code-bg);
  font-weight: 600;
}

tbody tr:nth-child(odd) { background: #fafafa; }

code, pre {
  font-family: "SFMono-Regular", Menlo, Monaco, Consolas, monospace;
  font-size: 13px;
}

code {
  background: var(--color-code-bg);
  padding: 1px 6px;
  border-radius: 3px;
}

pre {
  background: var(--color-code-bg);
  padding: 12px 16px;
  border-radius: 6px;
  overflow-x: auto;
}

pre code {
  background: transparent;
  padding: 0;
}

.badge {
  display: inline-block;
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 13px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.badge-green {
  background: var(--color-green-bg);
  color: var(--color-green-fg);
}

.badge-yellow {
  background: var(--color-yellow-bg);
  color: var(--color-yellow-fg);
}

.badge-red {
  background: var(--color-red-bg);
  color: var(--color-red-fg);
}

td.cell-ok {
  background: var(--color-green-bg);
  color: var(--color-green-fg);
  font-weight: 600;
}

td.cell-fail {
  background: var(--color-red-bg);
  color: var(--color-red-fg);
  font-weight: 600;
}

blockquote {
  border-left: 4px solid var(--color-link);
  padding: 4px 16px;
  color: var(--color-muted);
  margin: 16px 0;
}

hr {
  border: 0;
  border-top: 1px solid var(--color-border);
  margin: 32px 0;
}

footer, .footer {
  color: var(--color-muted);
  font-size: 13px;
  margin-top: 40px;
}
