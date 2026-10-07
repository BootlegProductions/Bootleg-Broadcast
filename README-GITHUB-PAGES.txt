BOOTLEG BROADCAST — GitHub Pages v0.33

UPDATE
1. In GitHub Desktop select your existing Bootleg-Broadcast repository. Fetch/Pull origin before copying files.
2. Extract this ZIP elsewhere. Copy its CONTENTS into the existing repository root, replacing matching files. index.html belongs directly at the root, not in an extra version folder. Do not upload the ZIP itself.
3. Delete only the exact obsolete paths listed in FILES-TO-DELETE.txt. Keep all other original files unless you have a separate reason to remove them.
4. Commit to your existing Pages branch and Push origin. Check the new Pages deployment in GitHub Actions. After its green tick, refresh the site with Ctrl+F5.

No npm build, backend, server key or API is required. Keep your existing Pages branch/root configuration. This export has not changed the live site.

LOCAL PREVIEW
Serve the extracted folder with VS Code Live Server or another static HTTP server. Opening index.html directly as a file can block JSON loading.

WHERE TO LOOK
sources.html: complete collection, language/evidence filters and exportable local source flags.
schedule-audit.html: current computed UK timetable, series airtime, episode repetition and channel overlap.
VERSION-HISTORY.txt: current and historical release notes; append future version changes here.
release-validation.json: current automated checks.
catalogue-audit.json: language checks, source holds and catalogue/rotation review evidence.

LANGUAGE LIMITS
English audio-track tags are metadata evidence, not full spoken-audio review. Upload titles and collection metadata are labelled as claims. Legacy unverified items remain visibly unverified. Japanese anime needs visibly verified English subtitles for new scheduling; English dubs are preferred. Report wrong-language files from the source catalogue and export your flags for the next repair pass.

FLAGS
Flags stay on the same browser/device. Reload the TV after flagging. They hold playback without changing the shared slot times. Clearing a flag and reloading restores eligibility. Incognito or a different device will not share flags; export to preserve/send them.

BROADCAST
All timetable positions use the viewer device clock in Europe/London. Correct clocks produce the same plan, but no server clock is required. After hours is 02:30–07:00 UK; December fireplace is 03:00–04:00. On-demand selections return to the scheduled broadcast when finished. Central repair/report sharing remains a future backend feature.

Keep Archive evidence and metadata reports for maintenance. A source can disappear or be mislabeled; catalogue membership does not guarantee current playback.
