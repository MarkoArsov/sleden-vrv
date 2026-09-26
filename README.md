# Sleden Vrv (Next Peak)

Static hiking schedule app for three Macedonian mountaineering clubs.

## Production data

The app reads `hikes.json` from the repository root. Data travels through
Apify → Google Drive (`Apify Uploads`) → the ChatGPT task **Upcoming Hikes Digest**
→ Google Drive (`hikes-clean`) → Apps Script → `sync-hikes` → GitHub Pages.
The action cannot publish a digest that was generated in chat but never saved to Drive.

Expected response shape:

```json
{
  "generatedAt": "2026-09-26T07:00:00Z",
  "today": "2026-09-26",
  "count": 0,
  "totalCount": 0,
  "hikes": []
}
```

`today` is the server date in Europe/Skopje and is used to distinguish past
from upcoming hikes. Each hike includes a `past` boolean.

The action runs at 06:23, 09:23, 12:23 and 15:23 UTC (GitHub can delay scheduled
runs), or manually from `main`. `HIKES_EXEC_URL` remains the only endpoint secret.
It makes up to six requests, 30 seconds apart after failures, with a 60-second
request timeout. HTTP failures, malformed JSON and stale successful responses
all retry. Each attempt uses a new cache-busting URL and preserves existing
endpoint query parameters.

The generated timestamp must have a timezone, be on the actual current
Europe/Skopje day, and not be more than five minutes in the future. The response's
`today` must match that day too. Data older than the committed snapshot is rejected.
Counts, hike identities/dates and `past` flags must agree; a nonzero `filesSkipped`
is treated as incomplete input. An empty feed with zero counts is valid. These
checks cannot detect a hike silently omitted by the generator: that requires
comparing the digest to the source posts.

Changes to hike content are accepted even if the exporter reuses `generatedAt`.
Changes only to `servedAt` or array order do not create commits. Exhausted retries
leave the committed snapshot intact and fail the run with a reason.

The action explicitly requests a Pages build using `pages: write`, even for an
unchanged snapshot, then polls the public `hikes.json` until it matches the
committed content. This also recovers a previous failed publication. A green run
means the public JSON matched; browser offline caches may still show their last
saved snapshot until connectivity returns. The app refreshes when brought back
to the foreground or reconnected.

## Validation and recovery

Run locally (Python 3.9+ and Node.js):

```sh
python3 -m unittest discover -s tests -p 'test_*.py' -v
node --test tests/hike-refresh.test.cjs
```

After pushing, run `sync-hikes` on `main` and inspect the fetch, publication and
verification steps. An upload failure in **Upcoming Hikes Digest** must be repaired
first; rerunning GitHub cannot create the missing Drive file. See
[the upstream recovery notes](docs/hike-digest-recovery.md).

## Deploy

This is a static site. Deploy the repository root as-is.

- `index.html` is the production entrypoint.
- `.nojekyll` is required for GitHub Pages so the `_ds/` asset directory is served.
- No build step is required.

## PWA / iPhone

The deployed site is installable as a standalone web app. It includes an iPhone Home Screen icon, safe-area handling for the Dynamic Island and Home Indicator, a portrait-first manifest, and an offline app shell with the last successfully fetched schedule available when the network is unavailable.

Service workers require HTTPS (or `localhost` during development), so opening `index.html` with a `file://` URL intentionally does not activate offline support or installation. On iPhone, open the deployed HTTPS site in Safari and use **Share → Add to Home Screen**.
