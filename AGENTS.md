# QnA Explorer — Project Context

## What this project is
A Hebrew Q&A archive pulled from **https://dtz.sbms.io/qas** and published as a static PWA on GitHub Pages:

https://theitalis-cpu.github.io/qna-explorer/

The web app is intentionally disconnected from `Full QnA.xlsm`. The site data source is `qna_data.json`.

## Key files

| File | Purpose |
|------|---------|
| `gen_html.py` | Generates `QnA Explorer.html` from the HTML template and `cats_clean.json` |
| `qna_data.json` | The app's Q&A data source, deployed next to `index.html` |
| `fetch_qna.py` | Scrapes current public Q&A cards from `dtz.sbms.io/qas` and merges them into `qna_data.json` |
| `qna_pipeline.py` | Shared JSON normalization, filtering, merging, and HTML parsing helpers |
| `build_pwa.py` | Creates PWA assets and deploys `index.html`, `qna_data.json`, manifest, service worker, and icons |
| `cats_clean.json` | Deduplicated category tree embedded in the HTML |
| `QnA Explorer.html` | Generated app file, deployed as `index.html`; do not edit directly |

## Deployment

- GitHub username: `theitalis-cpu`
- Repo: `qna-explorer`
- Token handling: never hardcode tokens. Set `GITHUB_TOKEN` in the shell before running deploy.

PowerShell example:

```powershell
$env:GITHUB_TOKEN = '<fine-grained token with Contents: read/write and Pages: read/write>'
python build_pwa.py
```

## Workflow — update app

1. Edit the template or logic inside `gen_html.py`.
2. Run `python gen_html.py`.
3. Run tests.
4. Run `python build_pwa.py` with `GITHUB_TOKEN` set.

## Workflow — update Q&A data

1. Run `python fetch_qna.py`.
2. Run `python build_pwa.py` with `GITHUB_TOKEN` set.

## App architecture

- Single generated HTML file with inline CSS/JS.
- Category tree is embedded from `cats_clean.json`.
- Q&A rows are loaded at runtime from `qna_data.json`.
- Search, pagination, and category filtering run locally in the browser.
- PWA assets are `manifest.json`, `sw.js`, `icon-192.png`, and `icon-512.png`.

## Known gotchas

- The old Meilisearch index `qa` no longer exists.
- The original site moved to Blazor Server; there is no known stable public JSON API equivalent to the old Next.js API.
- `Full QnA.xlsm` may remain as an archive, but production site data must come from `qna_data.json`.
