# Sleden Vrv (Next Peak)

Static hiking schedule app for three Macedonian mountaineering clubs.

## Production data

The app fetches live data from Google Apps Script:

`https://script.googleusercontent.com/macros/echo?user_content_key=AUkAhnTLtcsEkLOLlMNSXC-TyWq9N7OkPZZHS9DfdMRZliourocwmPAPm0a1i1fxixSLQ3KqhmgY8pjTckkATUL8JnFYdc1f6w0n1sFkP0TT5HOarCbOb4qQpbUwljWV35nRgd3rBkLMyW54OscfLEkdAvHOvOU2di9IRJYuk39Jt4ODk7cJC227eJQvJRp_7PKWMTnnDDtLET89XMQeaZ8ThxNN_uBKZpRqXUqhTyrV8v2ZRqlVPvbGDiDvXqelVcbmKeLpq_fUkamg9xo73o9Ezd_qQ_fGoA&lib=MVMzfW7giOr253XPEZ6bqqgJ2S0OvVxq0`

Expected response shape:

```json
{
  "generatedAt": "2026-08-24T12:46:08Z",
  "hikes": []
}
```

## Deploy

This is a static site. Deploy the repository root as-is.

- `index.html` is the production entrypoint.
- `.nojekyll` is required for GitHub Pages so the `_ds/` asset directory is served.
- No build step is required.
