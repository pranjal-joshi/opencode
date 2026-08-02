# OpenCode Docs Site

Static documentation site for the OpenCode Home Assistant integration, served
by GitHub Pages at **https://pranjal-joshi.github.io/opencode/**.

## How it's deployed

- Source: the `docs/` folder on the `main` branch.
- GitHub Pages: **Settings → Pages → Deploy from a branch** → branch `main`, folder `/docs`.
- Pure static HTML + CSS — no build step required. Edits to `docs/` go live on push.

## Pages

| File | Purpose |
|---|---|
| `index.html` | Landing page |
| `install.html` | HACS + manual installation |
| `configuration.html` | API key, endpoint, and agent setup |
| `usage.html` | Chat, voice, and automation usage |
| `faq.html` | Frequently asked questions |
| `404.html` | Error page |
| `assets/style.css` | Shared dark NeuraMesh theme |

## Theme

Dark theme: background `#0b1326`, primary `#4edea3`, gold `#e9c349`. Fonts:
Space Grotesk (headings), Manrope (body), JetBrains Mono (code).
