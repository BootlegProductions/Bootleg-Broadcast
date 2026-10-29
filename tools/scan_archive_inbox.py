"""Inspect Internet Archive item files and nested bundles before adding broadcasts.

Run: python tools/scan_archive_inbox.py --limit 50
Writes archive-review-candidates.json. This NEVER adds unverified media to channels.
Python standard library only; requires network access to archive.org.
"""
import argparse
import html.parser
import json
import pathlib
import re
import urllib.error
import urllib.parse
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]
VIDEO = re.compile(r"\.(mp4|m4v|webm|mkv|avi|mov|mpg|mpeg)$", re.I)
BUNDLE = re.compile(r"\.(zip|7z|rar|tar|gz)$", re.I)
USER_AGENT = "BootlegBroadcast-ArchiveReview/1.0 (metadata only)"
BASE = "https://archive.org"


def request(url, timeout=22):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=timeout) as res:
        return res.read()


def read_json(url):
    return json.loads(request(url).decode("utf-8"))


def direct_link(identifier, filename):
    return BASE + "/download/" + urllib.parse.quote(identifier, safe="") + "/" + urllib.parse.quote(filename, safe="/")


def runtime(file_info):
    try:
        duration = float(file_info.get("length") or file_info.get("duration") or 0)
        return round(duration, 3) if duration > 0 else None
    except (ValueError, TypeError):
        return None


def suggested_channel(text):
    title = text.lower()
    if any(x in title for x in ("coraline", "paranorman", "boxtrolls", "kubo and the two", "missing link")):
        return ["Cartoons Cartoons", "Dizzy"], "LAIKA film candidate; possibly Halloween"
    if any(x in title for x in ("anime", "studio ghibli", "pokemon", "dragon ball")):
        return ["Japanime"], "Anime candidate; confirm episode or film"
    if any(x in title for x in ("cartoon", "animation", "nickelodeon", "looney tunes")):
        return ["Cartoons Cartoons"], "Animation candidate"
    return [], "Manual content review required"


class DirectoryLinks(html.parser.HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []

    def handle_starttag(self, tag, attrs):
        if tag != "a":
            return
        href = dict(attrs).get("href", "")
        if href and not href.startswith(("#", "?", "javascript:", "../")):
            self.links.append(href)


def list_bundle(identifier, filename):
    """Best-effort directory listing: no ZIP archive is downloaded or unpacked."""
    url = direct_link(identifier, filename) + "/"
    try:
        parser = DirectoryLinks()
        parser.feed(request(url, timeout=15).decode("utf-8", "replace"))
        entries = []
        for href in parser.links:
            path = urllib.parse.unquote(urllib.parse.urlsplit(href).path)
            if VIDEO.search(path) and path not in entries:
                entries.append(path)
        return entries[:200], None
    except Exception as exc:
        return [], "Archive did not expose bundle index: " + str(exc)[:160]


def inspect_item(identifier, inspect_bundles=False):
    info = read_json(BASE + "/metadata/" + urllib.parse.quote(identifier, safe=""))
    metadata = info.get("metadata") or {}
    files = info.get("files") or []
    videos, bundles = [], []
    originals = {f.get("name", "") for f in files if VIDEO.search(f.get("name", "")) and not f.get("name", "").endswith(".ia.mp4")}
    for f in files:
        name = f.get("name", "")
        if not isinstance(name, str):
            continue
        if VIDEO.search(name):
            if name.endswith(".ia.mp4") and name[:-7] + ".mp4" in originals:
                continue
            channel, note = suggested_channel(name)
            videos.append({
                "filename": name,
                "direct_url": direct_link(identifier, name),
                "length_seconds": runtime(f),
                "size_bytes": int(f.get("size") or 0),
                "format": f.get("format"),
                "proposed_channels": channel,
                "notes": note,
                "review_status": "pending_playback_audio_rights_verification",
            })
        elif BUNDLE.search(name):
            entry = {"filename": name, "archive_url": direct_link(identifier, name), "nested_video_paths": [], "note": "Inspect bundle contents; title alone is not sufficient"}
            if inspect_bundles:
                entry["nested_video_paths"], error = list_bundle(identifier, name)
                if error:
                    entry["error"] = error
                # These are leads, not verified streams. Inspect individual nested
                # filenames; the generic ZIP or item title tells us very little.
                entry["nested_video_candidates"] = []
                seen_nested = set()
                for nested in entry["nested_video_paths"]:
                    basename = urllib.parse.unquote(urllib.parse.urlsplit(nested).path).rsplit("/", 1)[-1]
                    if not VIDEO.search(basename) or nested in seen_nested:
                        continue
                    seen_nested.add(nested)
                    channels, note = suggested_channel(basename)
                    entry["nested_video_candidates"].append({
                        "filename": basename,
                        "directory_path": nested,
                        "proposed_channels": channels,
                        "notes": note,
                        "review_status": "requires_individual_video_runtime_audio_rights_check"
                    })
            bundles.append(entry)
    return {
        "identifier": identifier,
        "item_url": BASE + "/details/" + urllib.parse.quote(identifier),
        "title": metadata.get("title", identifier),
        "license_url": metadata.get("licenseurl"),
        "video_count": len(videos),
        "bundle_count": len(bundles),
        "nested_candidate_count": sum(len(b.get("nested_video_candidates", [])) for b in bundles),
        "video_files": videos,
        "bundles": bundles,
    }


def uploader_items(username, limit):
    # The Archive's uploader field is sometimes an email, not a public handle.
    # Therefore treat this query as best effort, never a complete inventory.
    q = "uploader:" + username + " OR creator:" + username
    params = [("q", q), ("fl[]", "identifier"), ("fl[]", "title"),
              ("rows", str(limit)), ("page", "1"), ("output", "json")]
    url = BASE + "/advancedsearch.php?" + urllib.parse.urlencode(params)
    docs = read_json(url).get("response", {}).get("docs", [])
    return [d["identifier"] for d in docs if isinstance(d.get("identifier"), str) and not d["identifier"].startswith("__")]


def run(limit, inspect_bundles):
    inbox = json.loads((ROOT / "archive-source-inbox.json").read_text(encoding="utf-8"))
    output = {"version": inbox["version"], "status": "review_only_not_broadcast",
              "items": [], "uploader_discoveries": [], "errors": [],
              "note": "Measured metadata is not proof of playback, available audio, ownership or rebroadcast permission."}
    for entry in inbox["sources"]:
        if entry["kind"] == "item":
            try:
                output["items"].append(inspect_item(entry["identifier"], inspect_bundles))
            except Exception as exc:
                output["errors"].append({"source": entry["identifier"], "reason": str(exc)[:250]})
        elif entry["kind"] == "uploader":
            try:
                ids = uploader_items(entry["username"], limit)
                output["uploader_discoveries"].append({"username": entry["username"], "ids": ids,
                     "warning": "Account uploads may not be fully indexed by the uploader/creator fields."})
                for identifier in ids:
                    try:
                        output["items"].append(inspect_item(identifier, inspect_bundles))
                    except Exception as exc:
                        output["errors"].append({"source": identifier, "reason": str(exc)[:250]})
            except Exception as exc:
                output["errors"].append({"source": entry["username"], "reason": str(exc)[:250]})
    path = ROOT / "archive-review-candidates.json"
    path.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"written": str(path), "items": len(output["items"]),
        "videos": sum(i["video_count"] for i in output["items"]),
        "nested_video_candidates": sum(i["nested_candidate_count"] for i in output["items"]),
        "bundles": sum(i["bundle_count"] for i in output["items"]),
        "errors": output["errors"][:8]}, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=50)
    parser.add_argument("--inspect-bundles", action="store_true")
    args = parser.parse_args()
    run(max(1, min(args.limit, 200)), args.inspect_bundles)
