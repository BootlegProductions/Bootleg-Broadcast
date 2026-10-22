BOOTLEG BROADCAST — GitHub Pages v0.37.0

UPDATE
1. In GitHub Desktop select your existing Bootleg-Broadcast repository. Fetch/Pull origin before copying files.
2. Extract this ZIP elsewhere. Copy its CONTENTS into the existing repository root, replacing matching files. index.html belongs directly at the root, not in an extra version folder. Do not upload the ZIP itself.
3. Delete only the exact obsolete paths listed in FILES-TO-DELETE.txt. Keep all other original files unless you have a separate reason to remove them.
4. Commit to your existing Pages branch and Push origin. Check the new Pages deployment in GitHub Actions. After its green tick, refresh the site with Ctrl+F5.

No npm build, backend, server key or API is required. Keep your existing Pages branch/root configuration. GitHub Pages publishes this repository after a successful Pages deployment. Direct commits no longer require copying a ZIP.

DIRECT GITHUB UPDATES
Changes can now be committed directly to the existing Pages branch. Check the Pages workflow result before assuming the live site has changed. Preserve the Google Search Console verification file and meta tag.

LOCAL PREVIEW
Serve the extracted folder with VS Code Live Server or another static HTTP server. Opening index.html directly as a file can block JSON loading.

WHERE TO LOOK
sources.html: complete collection, language/evidence filters and exportable local source flags.
schedule-audit.html: current written UK timetable, series airtime, episode repetition and channel overlap.
VERSION-HISTORY.txt: current and historical release notes; append future version changes here.
release-validation.json: current full-year timing checks.
seasonal-validation.json: dated winter appointments, fireplace hours and local-link checks.
seasonal-source-review.json: exact originals, codec probes, sample decode checks and unresolved branded fireplaces.
SITE-REVIEW.txt: current changes, audit results and remaining source limits.
editorial-review.json: measured series availability and named fallback review.
playback-validation.json: clock expansion and source-recovery checks.
CHANNEL-LINEUP.txt: simple per-channel list and counts of programmes actually scheduled.
channel-lineup.json: machine-readable version of that roster.
addition-validation.json: new weekly pilot/feature placement checks.
addition-file-probes.json: sampled direct-file availability checks, not full playback/audio reviews.
BROADCAST-LINEUP-GUIDE.txt: channel blocks, source limits and three sample days.

LANGUAGE LIMITS
English audio-track tags are metadata evidence, not full spoken-audio review. Upload titles and collection metadata are labelled as claims. Legacy unverified items remain visibly unverified. The original Japanime collections are accepted as English dubbed or English subtitled following your confirmation; English dubs are preferred. New sources still require language evidence. Report wrong-language files from the source catalogue and export your flags for the next repair pass.

FLAGS
Flags stay on the same browser/device. Reload the TV after flagging. They hold playback without changing the shared slot times. Clearing a flag and reloading restores eligibility. Incognito or a different device will not share flags; export to preserve/send them.

BROADCAST
All timetable positions use the viewer device clock in Europe/London. Correct clocks produce the same plan, but no server clock is required. After hours is 02:30–07:00 UK; December fireplace is 04:00–05:00. On-demand selections return to the scheduled broadcast when finished. Central repair/report sharing remains a future backend feature.

Keep Archive evidence and metadata reports for maintenance. A source can disappear or be mislabeled; catalogue membership does not guarantee current playback.

EDITING THE WRITTEN SCHEDULE
1. Edit named appointments in editorial-lineups.json and series mappings in editorial-series.json.
2. Python 3.9+ with Europe/London timezone data: python tools/refresh_runtimes.py (only when adding sources).
3. Edit editorial-film-calendar.json for specific film choices. When changing film inventory/windows, first regenerate it with python tools/write_film_calendar.py.
   python tools/build_broadcast.py 2026
4. python tools/refresh_replacement_placements.py
   python tools/verify_broadcast.py
5. With Node installed: node tools/verify_playback.cjs
6. Commit the updated monthly JSON, channel-breaks.json and catalogue. No Python or Node runs on GitHub Pages.

This release contains the 2026 calendar. Rebuild with the required year before using a later calendar year; holiday dates and UK clock changes depend on that year. The verification script uses each monthly file’s year.
The current playback verification script checks the 2026 release and needs its test calendar updated when preparing another year.

NEW IN v0.36.4
Expanded Star Spangled educational mornings, eight additional cartoon/anime series in named weekly slots, partial Futurama recovery and AAA Pilot & Oddities Night at 22:00 Fridays. First Sundays at 20:00 have an occasional animation feature. Sources are assigned explicitly in editorial-lineups.json. CHANNEL-LINEUP.txt lists every programme actually scheduled this year.
After rebuilding, run tools/write_channel_roster.py to refresh both this roster and source-library actual date filters. Run tools/verify_additions.py for the new appointments.

NEW IN v0.36.4
Original markdown series restored to authored successor runs. A block completes the available ordered episodes, then moves to its next named series. It repeats only after the whole authored chain finishes. Core 90s Toons breakfast and Cartoons Cartoons classic mornings remain.
series-run-calendar.json: actual series handover dates for each authored block.
RESTORATION-STATUS.txt: restored series, measured episode counts and sources held for mapping/replacement.
restoration-validation.json: succession, restored airtime and original collection preservation checks.
The VHS candle is lower; two desktop candles follow the CRT frame. The tuning noise is a quiet 120 ms burst, capped at 140 ms, with mute/power-off cancellation.
Browser-rendered visual inspection could not be completed in this environment. Please check the extra candle positions on your desktop preview; mobile scene rules hide the added candles. Automated checks do not replace a full viewing/audio review of Archive sources.

FILMS IN v0.36.4
Full-length weekly film appointments now appear on all ten channels. Japanime cinema is Saturday 20:00; Pokémon alternates with other anime outside October/December. October prioritises horror/spooky films; December prioritises Christmas/winter films. Films have a 28-day repeat gap per channel. The explicit editorial-film-calendar.json selects exact source copies; FILM-CALENDAR.txt lists every actual film with date, channel and UK start time. Known unmeasured/held sources remain in the library. Run tools/verify_films.py after rebuilding.

NEW IN v0.36.4
Fixed repeated live-slot reloads near clip endings and bounded recovery attempts. An unavailable or early-ending programme plays its station ident once, then shows a labelled interval with the next actual programme and start time. Channels with no measured adverts no longer repeat their ident throughout scheduled gaps. Star Spangled fills blocks with additional ordered episodes when they fit; sub-ten-minute DVD fragments are excluded from its regular episode profiles. The remaining intervals need suitable short adverts/programmes to fill them with video. This is a player/schedule repair, not a new external source review.

NEW IN v0.36.4
23 fully decoded original American adverts fill previously empty break pools. See AMERICAN-ADVERTS.txt for every title and exact MP4/source URL, and advert-source-review.json for accepted/held evidence. Uploaders declare English; full independent spoken-audio review was not performed. HEVC, MPEG-4 Part 2, corrupt, inaccessible and unknown-language candidates are held. Curated product adverts are in nostalgic-american-adverts.json; no station bumper has been reassigned. Rebuild the calendar after editing this pool. Whole adverts fit into available gaps; tiny remaining tails can still show an ident/labelled interval.

NEW IN v0.36.4
Channel-specific UK adverts, Disney idents and Nickelodeon idents are in channel-interstitials.json. CHANNEL-ADVERTS-AND-IDENTS.txt lists exact links and runtimes. All compiled advert/trailer/bumper clips now have a hard 60-second cap. Shorter idents play at their original duration. Original Bootleg channel idents remain. Rebuild all months after editing interstitials; full clips fit within each break. Held originals and reasons remain in channel-interstitial-source-review.json. English is uploader-declared, not a full independent listening review.
