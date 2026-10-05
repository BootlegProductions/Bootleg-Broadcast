#!/usr/bin/env python3
"""Rebuild Bootleg Broadcast schedules without flooding the daily rotation.

The v0.25 source layer is first extracted as a reusable programme library and
removed from active schedules. One rotating library programme is then added per
channel/day outside the October and December special schedules. Trailer Park
Boys is rebuilt separately from verified full-length S1-S7 DVD title files.
"""

from __future__ import annotations

import json
import re
from collections import defaultdict
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[1]
SCHEDULES = ROOT / "schedules"
ADDITION_SOURCE = "Additional Links v0.25"
TPB_SOURCE = "TPB replacement v0.25"
NEW_SOURCE = "Curated rotation v0.27"


def archive_url(identifier: str, filename: str) -> str:
    return f"https://archive.org/download/{identifier}/{quote(filename, safe='/')}"


def episode(season: int, number: int, identifier: str, filename: str) -> dict:
    return {
        "type": "Episode",
        "show": "Trailer Park Boys",
        "season": str(season),
        "episode": number,
        "title": f"S{season:02d}E{number:02d}",
        "url": archive_url(identifier, filename),
        "source": "Verified TPB S1-S7 v0.27",
    }


def special(title: str, identifier: str, filename: str, alternates=None) -> dict:
    item = {
        "type": "Special",
        "show": "Trailer Park Boys",
        "title": title,
        "url": archive_url(identifier, filename),
        "source": "Verified TPB specials v0.27",
    }
    if alternates:
        item["alternates"] = alternates
    return item


TPB_EPISODE_FILES = {
    1: ("trailer-park-boys-s1-s2", [
        "TRAILER_PARK_BOYS_01.mp4", "TRAILER_PARK_BOYS_0111.mp4",
        "TRAILER_PARK_BOYS_015.mp4", "TRAILER_PARK_BOYS_017.mp4",
        "TRAILER_PARK_BOYS_02.mp4", "TRAILER_PARK_BOYS_0211.mp4",
    ]),
    2: ("trailer-park-boys-s1-s2", [
        "TRAILER_PARK_BOYS_027.mp4", "TRAILER_PARK_BOYS_029.mp4",
        "TRAILER_PARK_BOYS_03.mp4", "TRAILER_PARK_BOYS_0311.mp4",
        "TRAILER_PARK_BOYS_0313.mp4", "TRAILER_PARK_BOYS_035.mp4",
        "TRAILER_PARK_BOYS_039.mp4",
    ]),
    3: ("trailer-park-boys-s3", [
        "TRAILER_PARK_BOYS_S3_D15.mp4", "TRAILER_PARK_BOYS_S3_D16.mp4",
        "TRAILER_PARK_BOYS_S3_D17.mp4", "TRAILER_PARK_BOYS_S3_D19.mp4",
        "TRAILER_PARK_BOYS_S3_D26.mp4", "TRAILER_PARK_BOYS_S3_D27.mp4",
        "TRAILER_PARK_BOYS_S3_D28.mp4", "TRAILER_PARK_BOYS_S3_D29.mp4",
    ]),
    4: ("trailer-park-boys-s4", [
        "TRAILER_PARK_BOYS_019.mp4", "TRAILER_PARK_BOYS_0110.mp4",
        "TRAILER_PARK_BOYS_0111.mp4", "TRAILER_PARK_BOYS_0112.mp4",
        "TPB_DISC02.mp4", "TPB_DISC027.mp4", "TPB_DISC028.mp4",
        "TPB_DISC029.mp4",
    ]),
    5: ("trailer-park-boys-s5", [
        "TRAILER_PARK_BOYS_5_DISC_165.mp4", "TRAILER_PARK_BOYS_5_DISC_166.mp4",
        "TRAILER_PARK_BOYS_5_DISC_167.mp4", "TRAILER_PARK_BOYS_5_DISC_168.mp4",
        "TRAILER_PARK_BOYS_5_DISC_169.mp4", "TRAILER_PARK_BOYS_5_DISC_254.mp4",
        "TRAILER_PARK_BOYS_5_DISC_255.mp4", "TRAILER_PARK_BOYS_5_DISC_256.mp4",
        "TRAILER_PARK_BOYS_5_DISC_257.mp4", "TRAILER_PARK_BOYS_5_DISC_258.mp4",
    ]),
    6: ("trailer-park-boys-s6", [
        "TRAILER_PARK_BOYS_SEASON_6_DISC_14.mp4",
        "TRAILER_PARK_BOYS_SEASON_6_DISC_15.mp4",
        "TRAILER_PARK_BOYS_SEASON_6_DISC_16.mp4",
        "TRAILER_PARK_BOYS_SEASON_6_DISC_17.mp4",
        "TRAILER_PARK_BOYS_SEASON_6_DISC24.mp4",
        "TRAILER_PARK_BOYS_SEASON_6_DISC25.mp4",
    ]),
    7: ("trailer-park-boys-s7", [
        "TRAILER_PARK_BOYS_S7_DISC15.mp4", "TRAILER_PARK_BOYS_S7_DISC16.mp4",
        "TRAILER_PARK_BOYS_S7_DISC17.mp4", "TRAILER_PARK_BOYS_S7_DISC18.mp4",
        "TRAILER_PARK_BOYS_S7_DISC19.mp4", "TRAILER_PARK_BOYS_S7_DISC25.mp4",
        "TRAILER_PARK_BOYS_S7_DISC26.mp4", "TRAILER_PARK_BOYS_S7_DISC27.mp4",
        "TRAILER_PARK_BOYS_S7_DISC28.mp4", "TRAILER_PARK_BOYS_S7_DISC29.mp4",
    ]),
}


def build_tpb_rotation() -> list[dict]:
    items = []
    for season, (identifier, filenames) in TPB_EPISODE_FILES.items():
        items.extend(episode(season, i, identifier, name)
                     for i, name in enumerate(filenames, 1))

    xmas_alt = archive_url(
        "trailer-park-boys-xmas-special-d_l", "TPB_-_DEAR_SANTA_V2.mp4"
    )
    items.extend([
        special("Dear Santa Claus, Go Fuck Yourself",
                "trailer-park-boys-xmas-special", "TPB_XMAS_SPECIAL.mp4",
                [xmas_alt]),
        special("Trailer Park Boys: The Movie", "trailer-park-boys-the-movie",
                "TRAILER_PARK_BOYS_THE_MOVIE.mp4"),
        special("Say Goodnight to the Bad Guys",
                "trailer-park-boys-say-goodnight-to-the-bad-guys",
                "SAY_GOODNIGHT_TO_THE_BAD_GUYS.mp4"),
        special("Countdown to Liquor Day",
                "trailer-park-boys-count-down-to-liquor-day",
                "TPB_COUNT_DOWN_TO_LIQUOR_DAY.mp4"),
        special("Don't Legalize It", "trailer-park-boys-dont-legalize-it",
                "TRAILER_PARK_BOYS.mp4", [
                    archive_url("trailer-park-boys-dont-legalize-it",
                                "TRAILER_PARK_BOYS1.mp4"),
                    archive_url("trailer-park-boys-dont-legalize-it",
                                "TRAILER_PARK_BOYS19.mp4"),
                ]),
    ])
    return items


def natural_key(value: str):
    return [int(part) if part.isdigit() else part.casefold()
            for part in re.split(r"(\d+)", value or "")]


def compact_library(raw_by_channel: dict[str, list[dict]]) -> dict[str, list[dict]]:
    compact = {}
    for channel, items in raw_by_channel.items():
        seen = set()
        kept = []
        for item in items:
            url = item.get("url")
            if not url or url in seen or "trailer park boys" in (
                (item.get("show") or "") + " " + (item.get("title") or "")
            ).casefold():
                continue
            seen.add(url)
            clean = {k: v for k, v in item.items() if k != "source"}
            clean["source"] = NEW_SOURCE
            kept.append(clean)
        compact[channel] = kept
    return compact


def choose_rotation(library: dict[str, list[dict]]):
    """Yield episodes show-by-show, advancing each show in sequence."""
    state = {}
    for channel, items in library.items():
        shows = defaultdict(list)
        for item in items:
            shows[item.get("show") or item.get("title") or "Unsorted"].append(item)
        names = sorted(shows, key=natural_key)
        for name in names:
            shows[name].sort(key=lambda item: natural_key(item.get("title", "")))
        state[channel] = {"shows": shows, "names": names,
                          "show_index": 0, "episode_index": defaultdict(int)}

    def next_item(channel: str):
        info = state.get(channel)
        if not info or not info["names"]:
            return None
        name = info["names"][info["show_index"] % len(info["names"])]
        info["show_index"] += 1
        episodes = info["shows"][name]
        pos = info["episode_index"][name] % len(episodes)
        info["episode_index"][name] += 1
        return dict(episodes[pos])

    return next_item


def insert_before_end_ident(playlist: list[dict], item: dict):
    index = len(playlist)
    for i in range(len(playlist) - 1, -1, -1):
        if playlist[i].get("type") == "Ident":
            index = i
        else:
            break
    if index and playlist[index - 1].get("type") != "AdBreak":
        playlist.insert(index, {
            "type": "AdBreak", "show": "Commercial Break",
            "title": "Curated rotation break", "count": 5,
            "source": NEW_SOURCE,
        })
        index += 1
    playlist.insert(index, item)


def main():
    files = sorted(SCHEDULES.glob("*.json"))
    documents = {path: json.loads(path.read_text(encoding="utf-8")) for path in files}
    raw_by_channel = defaultdict(list)
    existing_library_path = ROOT / "programme-library.json"
    existing_library = None
    if existing_library_path.exists():
        existing_library = json.loads(
            existing_library_path.read_text(encoding="utf-8")
        ).get("channels")

    # Extract the failed bulk layer once, then remove it and its generated breaks.
    for document in documents.values():
        for week in document.get("weeks", []):
            for day in week.get("week", []):
                for channel in day.get("channels", []):
                    cleaned = []
                    for item in channel.get("playlist", []):
                        if item.get("source") in {ADDITION_SOURCE, NEW_SOURCE}:
                            if item.get("type") != "AdBreak":
                                if item.get("source") == ADDITION_SOURCE:
                                    raw_by_channel[channel["name"]].append(item)
                            continue
                        cleaned.append(item)
                    channel["playlist"] = cleaned

    library = compact_library(raw_by_channel) if raw_by_channel else existing_library
    if not library:
        raise RuntimeError("No programme library is available for schedule rebuilding")
    (ROOT / "programme-library.json").write_text(
        json.dumps({"channels": library}, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    next_library_item = choose_rotation(library)
    tpb = build_tpb_rotation()
    tpb_index = 0
    additions_scheduled = defaultdict(int)
    tpb_replaced = 0

    for path in files:
        month = path.stem.casefold()
        document = documents[path]
        for week in document.get("weeks", []):
            for day in week.get("week", []):
                for channel in day.get("channels", []):
                    playlist = channel.get("playlist", [])
                    rebuilt = []
                    for item in playlist:
                        text = ((item.get("show") or "") + " " +
                                (item.get("title") or "")).casefold()
                        if item.get("source") == TPB_SOURCE or "trailer park boys" in text:
                            if channel.get("name") == "Star Spangled TV":
                                rebuilt.append(dict(tpb[tpb_index % len(tpb)]))
                                tpb_index += 1
                                tpb_replaced += 1
                            continue
                        rebuilt.append(item)
                    channel["playlist"] = rebuilt

                    # October and December retain their dedicated scheduling.
                    if month not in {"october", "december"}:
                        selected = next_library_item(channel.get("name", ""))
                        if selected:
                            insert_before_end_ident(channel["playlist"], selected)
                            additions_scheduled[channel["name"]] += 1

        path.write_text(json.dumps(document, indent=2, ensure_ascii=False) + "\n",
                        encoding="utf-8")

    report = {
        "version": "0.27",
        "policy": "One show-balanced library item per channel/day; October and December preserved.",
        "library_items": {key: len(value) for key, value in library.items()},
        "curated_items_scheduled": dict(additions_scheduled),
        "tpb_verified_episode_count": sum(len(v[1]) for v in TPB_EPISODE_FILES.values()),
        "tpb_verified_special_count": len(tpb) - sum(len(v[1]) for v in TPB_EPISODE_FILES.values()),
        "tpb_schedule_slots_rebuilt": tpb_replaced,
        "tpb_active_seasons": [1, 2, 3, 4, 5, 6, 7],
    }
    (ROOT / "SCHEDULE_VALIDATION_V0.27.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
