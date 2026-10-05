BOOTLEG BROADCAST — GitHub Pages v0.32

This is the completed static v0.32 GitHub Pages export. Creating it has not updated either live site.

DEPLOY
1. Extract the ZIP. Copy its CONTENTS into your existing repository root, replacing matching files. index.html belongs at the repository root. Do not upload the ZIP itself as the website.
2. Commit and push using GitHub Desktop, or upload the extracted files with GitHub. Keep your existing GitHub Pages branch/root settings. Include .nojekyll where your file picker supports it.
3. Wait for GitHub Pages to finish deploying, then hard-refresh the site (Ctrl+F5 on Windows). No npm install, build step, server, API key or backend is required.

LOCAL REVIEW
Extract the ZIP and serve its folder with VS Code Live Server or another local static web server. Opening index.html as a file may block JSON loading.

THIS UPDATE
81 new catalogue entries, plus 23 checked alternate/replacement sources. Christmas is expanded across the channels, including British comedy and Nickelodeon specials. The source database shows annual holiday placement. Dedicated Valentine, St Patrick, Easter, Thanksgiving and New Year specials follow their actual dates. Existing Halloween additions, CRT room artwork, VHS lettering, remote and responsive layouts are included.

CALENDAR
Valentine's Day: 14 February. St Patrick's Day: 17 March. Western Easter Sunday is recalculated annually (5 April 2026; 28 March 2027). US Thanksgiving is the fourth Thursday of November (26 November 2026; 25 November 2027). New Year programmes run on 31 December and 1 January. Christmas rotates throughout December, with additional spotlights on 24–26 December. Christmas, winter and spring-themed material can retain wider seasonal windows. Date previews use the current UK year, and the timed engine recalculates movable dates without a yearly code update. The JSON month rotations are a 2026 snapshot; holiday eligibility comes from the annual rules, not the snapshot's weekday labels.

PLAYBACK WITHOUT A BACKEND
Scheduled positions use the viewer's device clock in Europe/London, including UK daylight saving. Viewers with accurate clocks join the same calculated programme; this is not server-clock synchronization. Channel controls, the full guide, searchable catalogue, selected-programme playback, retries and return to broadcast work on GitHub Pages. After hours is 02:30–07:00 UK; the December fireplace remains 03:00–04:00. Courage remains eligible 18:00–07:00 year-round with an October double bill starting at 18:00 daily.

Unavailable sources are held for the current TV visit, with retries/alternates and manual skip controls. On the timed broadcast, a failed slot retains its scheduled duration instead of shifting other viewers' clocks. Selected programmes can return to the current broadcast afterwards. Shared failure reports and central repair controls require a backend; the reports page explains this and hides its server controls. hosting-config.js keeps backend services off, so the static edition never calls absent /api routes.

SOURCE EVIDENCE
Holiday-source-review.md and holiday-review-v032.json list new sources, exact URLs, durations, codec checks, corrections and held candidates. Header/metadata checks do not constitute complete watch-throughs or language/subtitle verification. Unconfirmed codecs, edited clips, unclear compilations and subtitle/encoding issues are kept off the new broadcast additions. Previous source records remain included; this is not a fresh full-watch review of every legacy source. Halloween-source-review.md covers the preceding Halloween additions.

VALIDATION
3650 complete 2026 channel-day plans checked for contiguous boundaries, correct holiday eligibility, mature dayparts and airtime for every new catalogue entry. Future Easter dates, including the 2027 UK daylight-saving transition, are checked. Static playback controls, source filters, mobile layout calculations, all month files and local asset paths passed their checks. The separate clock check passes, including December Japanime mornings. Every October and December kids anime morning is covered. Two legacy Ben 10 originals with AC3 audio are held from TV playback and marked in the catalogue. Fresh rendered browser visual QA was unavailable; the existing room artwork/layout was preserved.
