# Recover the upstream hike digest

## Confirmed failure on September 26, 2026

The **Upcoming Hikes Digest** ChatGPT task reported that the September 26 Apify
source was available and valid JSON was generated, but its Drive uploader could
not access the generated container file. It reported the same upload failure on
September 25 and reported disabling the recurring task. The actual scheduler
state has not been independently verified.

GitHub run `36166203526` then received `generatedAt=2026-09-23T07:00:21Z` with
`today=2026-09-25`. Both remote `hikes.json` and the public website still held the
September 23 snapshot when inspected on September 26. The Node 20 warning did
not cause that failure. Successful data commits have corresponding Pages runs;
publication has not been established as the cause of these missing hikes.

The local changes harden the downstream workflow. They do not repair ChatGPT's
file-transfer runtime, create a new Drive digest, or re-enable a cloud task.
Do not recreate the JSON from the chat summary: it omits full captions and other
required fields.

## Repair and verification procedure

1. Open the existing **Upcoming Hikes Digest** task and inspect its saved prompt,
   current enabled state, schedule, connected Drive account and recent upload
   error. Preserve the existing extraction schema, club mapping, verbatim
   captions/images and create-only rules.
2. Run the digest against the latest complete `apify-instagram-hikes` source in
   `Apify Uploads`. Use today's date in Europe/Skopje for the output filename and
   UTC for `generatedAt`. Do not change the source files.
3. Validate the complete JSON and upload it into `hikes-clean` using a file
   reference supported by the uploader in that runtime. A local path that exists
   only in another tool's container is not evidence the uploader can read it.
   Do not invent a file reference, upload an empty placeholder, or substitute a
   Google Doc for a JSON file.
4. If file transfer still fails, retain the generated JSON as a downloadable
   artifact and report the exact failing tool/error. Repair the connector/runtime
   access, or manually upload that exact artifact to `hikes-clean` under an unused
   `hikes-YYYY-MM-DD.json` (or numbered suffix) filename. A manual upload is a
   recovery for one run, not a fix to the recurring integration.
5. Read the created Drive file back and compare parsed JSON, generation time,
   expected hike IDs, full captions and images with the validated artifact.
   Only claim success after verifying the destination file ID and contents.
6. Verify the saved schedule and re-enable the existing task if it is disabled,
   after the upload path works. One completed daily run is not completion of the
   recurring task. Do not change the cadence or create a duplicate task/watchdog.
7. After the local workflow changes are pushed, manually run `sync-hikes` on
   `main`. Confirm its source snapshot is today's digest, its public-data
   verification succeeds, and the website shows those same hike IDs. Reopen an
   existing browser/PWA session and confirm it refreshes too.

## Suggested addition to the existing scheduled prompt

Keep the current extraction instructions and schema. Add this to the write step:

> Treat writing and verifying the Drive JSON as part of completion. Use only a
> file-transfer mechanism supported by the current connected Drive tool and its
> runtime. Verify the upload tool can access the generated file reference; do not
> repeatedly submit a path from an inaccessible container. Create only a new JSON
> file in hikes-clean, using the existing unique-filename rule. After creation,
> read the destination file back and compare its parsed contents with the validated
> source artifact. Report the Drive file ID and filename only after verification.
> If transfer is unavailable, preserve a downloadable JSON artifact, report the
> failing stage and error, and ask for the access/runtime repair needed. Do not
> claim publication or modify existing files. This is an ongoing daily task:
> neither one successful run nor one transient failure ends its recurring purpose.
> Preserve its configured schedule; if the platform pauses it, report that state
> and the action needed to restore it.

This prompt improves verification and failure reporting. It cannot by itself
repair a platform file-access error. Test the actual upload before treating the
recurring task as repaired.
