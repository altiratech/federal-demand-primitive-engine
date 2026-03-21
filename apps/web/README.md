# Web App

Intended responsibilities:
- kernel explorer
- evidence viewer
- taxonomy or cluster navigation

Do not start with a broad market dashboard.

Current local review surface:
- `index.html`
- `styles.css`
- `app.js`

Run locally from the repo root so the app can fetch the committed artifact:

```bash
python3 -m http.server 4173
```

Then open:
- `http://127.0.0.1:4173/apps/web/index.html`
