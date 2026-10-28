# Archive collections awaiting file-level review

These sources were supplied for Bootleg Broadcast on 28 October 2026. Their item
titles are **not** a list of playable films. Do not auto-schedule a movie,
episode, or special from a collection name or from a ZIP filename.

| Submitted source | Proposed programming use | Current status |
| --- | --- | --- |
| [LAIKA Studios films](https://archive.org/details/laika-studios-films) | Cartoons Cartoons and Dizzy film nights; darker stop-motion titles for the Halloween rotation | Individual filenames, audio, codec, measured runtime and rights still need verification |
| [Media Preservation Chamber](https://archive.org/details/media-preservation-chamber_626) | Mixed archive material, depending on the **actual contents** | Inspect all direct videos and folder/ZIP listings before assigning a channel |
| [m3dia_l0aner_626 uploads](https://archive.org/details/@m3dia_l0aner_626/uploads) | Additional channel films, series and Christmas specials after per-file inspection | Uploader listing may have many generically named collections and needs per-item inspection |

## Inventory workflow

Run `python tools/scan_archive_inbox.py --inspect-bundles --limit 50` in a
network-enabled working copy to create `archive-review-candidates.json`.
This checks each item's Archive metadata file listing, preserves nested media
paths, extracts measured lengths where supplied, and requests ZIP directory
listings where available. It does **not** download video files or silently
publish media to the broadcast.

Review any ZIP or group still missing file listings manually, since an item
named "Christmas Media" may contain several unrelated files. Uploader discovery
is best-effort: Archive account handles do not always map to its uploader
metadata search field.

## Proposed film programming

If the actual LAIKA collection contains working copies of `Coraline` or
`ParaNorman`, those would fit the October evening family/Halloween film
rotation; `The Boxtrolls`, `Kubo and the Two Strings`, and `Missing Link`
would be suitable candidates for general family film slots if present.
**None of those titles is asserted to be in this collection yet.** Each must
be verified as a distinct file with a playable, measured runtime and appropriate
rebroadcast permissions before entering `source-library.json` and the compiled
programmes. Existing scheduled films and episodes are not replaced automatically.

The new ad/ident continuity system only uses already-listed, measured items
from the existing Bootleg Broadcast catalogue. These external collections are
not mixed into it until reviewed.
