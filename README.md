# Sleden Vrv (Next Peak)

Static hiking schedule app for three Macedonian mountaineering clubs.

## Production data

The app reads `hikes.json` from the repository root. The scheduled
`sync-hikes` GitHub Action refreshes that file from the configured repository
secret after the upstream data is written.

Expected response shape:

```json
{
  "generatedAt": "2026-08-24T12:46:08Z",
  "today": "2026-09-07",
  "count": 4,
  "totalCount": 37,
  "hikes": []
}
```

`today` is the server date in Europe/Skopje and is used to distinguish past
from upcoming hikes. Each hike includes a `past` boolean.

## Deploy

This is a static site. Deploy the repository root as-is.

- `index.html` is the production entrypoint.
- `.nojekyll` is required for GitHub Pages so the `_ds/` asset directory is served.
- No build step is required.

## PWA / iPhone

The deployed site is installable as a standalone web app. It includes an iPhone Home Screen icon, safe-area handling for the Dynamic Island and Home Indicator, a portrait-first manifest, and an offline app shell with the last successfully fetched schedule available when the network is unavailable.

Service workers require HTTPS (or `localhost` during development), so opening `index.html` with a `file://` URL intentionally does not activate offline support or installation. On iPhone, open the deployed HTTPS site in Safari and use **Share → Add to Home Screen**.
