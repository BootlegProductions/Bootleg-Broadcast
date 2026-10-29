"""Summarise real Internet Archive filenames for manual scheduling review.

This does not infer media from collection titles or add untested videos to TV.
"""
import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[1]
inventory = json.loads((ROOT / "archive-review-candidates.json").read_text())
catalogue = json.loads((ROOT / "source-library.json").read_text())
existing_urls = {p.get("url") for p in catalogue.get("programmes", [])}
def key(value):
    name = str(value or "").rsplit("/", 1)[-1]
    name = re.sub(r"\\.(mp4|m4v|webm|mkv)$", "", name, flags=re.I)
    return re.sub(r"[^a-z0-9]+", "", name.lower())
catalogue_titles = {}
for programme in catalogue.get("programmes", []):
    for field in ("title", "filename"):
        title = programme.get(field)
        k = key(title)
        if k and len(k) >= 7 and k not in catalogue_titles:
            catalogue_titles[k] = programme.get("title", "")

holiday = re.compile(r"christmas|xmas|santa|snow|winter|holiday|grinch|rudolph|frosty|elf|jingle|nutcracker|north.pole|scrooge|yule|noel|polar.express|charlie.brown|miser.brothers|jack.frost", re.I)
laika = re.compile(r"coraline|paranorman|boxtrolls|kubo|missing.link|laika", re.I)
seen = set()
records = []
for item in inventory.get("items", []):
    identifier = item["identifier"]
    for video in item.get("video_files", []):
        url = video["direct_url"]
        if url in seen:
            continue
        seen.add(url)
        name = video["filename"]
        bucket = ("christmas" if holiday.search(name) else
                  "laika" if laika.search(name) or identifier == "laika-studios-films" else "other")
        records.append({
            "category": bucket,
            "item": identifier,
            "collection_title": item.get("title"),
            "filename": name,
            "url": url,
            "seconds": video.get("length_seconds"),
            "format": video.get("format"),
            "existing_url": url in existing_urls,
            "existing_title": catalogue_titles.get(key(name)),
            "proposed_channels": video.get("proposed_channels", []),
            "needs_manual_review": True,
        })
    for bundle in item.get("bundles", []):
        for nested in bundle.get("nested_video_candidates", []):
            key = identifier + "/" + nested.get("directory_path", "")
            if key in seen:
                continue
            seen.add(key)
            name = nested["filename"]
            records.append({
                "category": "christmas" if holiday.search(name) else "other",
                "item": identifier,
                "collection_title": item.get("title"),
                "filename": name,
                "bundle": bundle["filename"],
                "nested_path": nested.get("directory_path"),
                "seconds": None,
                "proposed_channels": nested.get("proposed_channels", []),
                "needs_manual_review": True,
                "note": "Bundle candidate: full video URL, duration and codec must be verified",
            })

rank = {"christmas": 0, "laika": 1, "other": 2}
records.sort(key=lambda p: (rank[p["category"]], p["item"], p["filename"]))
output = {
    "status": "discovered_files_pending_playback_and_rights_verification",
    "collections_checked": [i["identifier"] for i in inventory.get("items", [])],
    "uploader_discoveries": inventory.get("uploader_discoveries", []),
    "scan_errors": inventory.get("errors", []),
    "counts": {bucket: sum(x["category"] == bucket for x in records)
               for bucket in ["christmas", "laika", "other"]},
    "total_found": len(records),
    "candidates": records[:350],
    "truncated": len(records) > 350,
}
out = ROOT / "archive-christmas-candidates.json"
out.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"items_checked": len(output["collections_checked"]),
                  "counts": output["counts"], "errors": len(output["scan_errors"]),
                  "shortlist": len(output["candidates"])}, indent=2))
