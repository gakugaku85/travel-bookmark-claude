#!/usr/bin/env python3
"""Build Google Maps–friendly exports from a trip spots JSON file.

Usage:
    python3 build_exports.py <spots.json> [--out DIR] [--resolve]

Input JSON schema:
    {
      "destination": "パリ",
      "list_name": "フランス旅行",
      "spots": [
        {
          "name_ja": "エッフェル塔",
          "name_en": "Eiffel Tower",
          "category": "展望台",
          "note": "夜のライトアップが◎",
          "address": "Champ de Mars, 5 Av. Anatole France, 75007 Paris"   # optional
        }
      ]
    }

Outputs (in --out, default: trips/<slug>/):
    spots.json   input enriched with place_id / lat / lng / maps_url
    spots.csv    import into Google My Maps ("インポート" → location column = Address)
    spots.kml    import into Google My Maps / Google Earth (only spots with coordinates)
    README.md    one-click Google Maps links for every spot

--resolve uses the Google Places API (New) Text Search to get place IDs and
coordinates. The API key is read from GOOGLE_MAPS_API_KEY. In a Claude Code
cloud session the key can instead be stored as a network secret for
places.googleapis.com (header X-Goog-Api-Key); the proxy then injects it and
this script sends a placeholder value.
Standard library only.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from xml.sax.saxutils import escape

PLACES_URL = "https://places.googleapis.com/v1/places:searchText"
FIELD_MASK = "places.id,places.displayName,places.formattedAddress,places.location,places.googleMapsUri"


def slugify(text: str) -> str:
    slug = re.sub(r"[^\w\-]+", "-", text.strip().lower(), flags=re.UNICODE).strip("-")
    return slug or "trip"


def maps_url(spot: dict, destination: str) -> str:
    """Universal Google Maps URL (works on web, iOS, Android)."""
    if spot.get("maps_url"):
        return spot["maps_url"]
    query = spot.get("address") or f"{spot.get('name_en') or spot.get('name_ja')} {destination}"
    params = {"api": "1", "query": query}
    if spot.get("place_id"):
        params["query_place_id"] = spot["place_id"]
    return "https://www.google.com/maps/search/?" + urllib.parse.urlencode(params)


def resolve_spot(spot: dict, destination: str, api_key: str) -> None:
    query = f"{spot.get('name_en') or spot.get('name_ja')} {destination}"
    body = json.dumps({"textQuery": query, "languageCode": "ja", "pageSize": 1}).encode()
    req = urllib.request.Request(
        PLACES_URL,
        data=body,
        headers={
            "Content-Type": "application/json",
            "X-Goog-Api-Key": api_key,
            "X-Goog-FieldMask": FIELD_MASK,
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=20) as resp:
        data = json.load(resp)
    places = data.get("places") or []
    if not places:
        spot["resolve_error"] = "not found"
        return
    place = places[0]
    spot["place_id"] = place.get("id")
    spot.setdefault("address", place.get("formattedAddress"))
    loc = place.get("location") or {}
    spot["lat"], spot["lng"] = loc.get("latitude"), loc.get("longitude")
    if place.get("googleMapsUri"):
        spot["maps_url"] = place["googleMapsUri"]


def write_csv(path: Path, spots: list[dict], destination: str) -> None:
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["Name", "Name (EN)", "Category", "Note", "Address", "Latitude", "Longitude", "Google Maps"])
        for s in spots:
            address = s.get("address") or f"{s.get('name_en') or s.get('name_ja')}, {destination}"
            w.writerow([
                s.get("name_ja") or s.get("name_en"),
                s.get("name_en", ""),
                s.get("category", ""),
                s.get("note", ""),
                address,
                s.get("lat") if s.get("lat") is not None else "",
                s.get("lng") if s.get("lng") is not None else "",
                maps_url(s, destination),
            ])


def write_kml(path: Path, spots: list[dict], list_name: str, destination: str) -> int:
    placemarks = []
    for s in spots:
        if s.get("lat") is None or s.get("lng") is None:
            continue
        name = s.get("name_ja") or s.get("name_en")
        desc = " / ".join(x for x in [s.get("name_en"), s.get("category"), s.get("note"), maps_url(s, destination)] if x)
        placemarks.append(
            "    <Placemark>\n"
            f"      <name>{escape(name)}</name>\n"
            f"      <description>{escape(desc)}</description>\n"
            f"      <Point><coordinates>{s['lng']},{s['lat']},0</coordinates></Point>\n"
            "    </Placemark>"
        )
    if not placemarks:
        return 0
    path.write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<kml xmlns="http://www.opengis.net/kml/2.2">\n'
        "  <Document>\n"
        f"    <name>{escape(list_name)}</name>\n" + "\n".join(placemarks) + "\n  </Document>\n</kml>\n",
        encoding="utf-8",
    )
    return len(placemarks)


def write_readme(path: Path, trip: dict, spots: list[dict], has_kml: bool) -> None:
    dest, list_name = trip["destination"], trip["list_name"]
    lines = [f"# {list_name}", "", f"目的地: {dest}", "", "| # | スポット | カテゴリ | メモ | 地図 |", "|---|---|---|---|---|"]
    for i, s in enumerate(spots, 1):
        name = s.get("name_ja") or s.get("name_en")
        if s.get("name_en") and s.get("name_ja"):
            name += f" ({s['name_en']})"
        note = (s.get("note") or "").replace("|", "\\|")
        lines.append(f"| {i} | {name} | {s.get('category', '')} | {note} | [Google Maps]({maps_url(s, dest)}) |")
    lines += [
        "",
        "## Google マップに取り込む",
        "",
        "1. [Google マイマップ](https://www.google.com/mymaps) で「新しい地図を作成」",
        f"2. レイヤの「インポート」から `spots.csv`{' または `spots.kml`' if has_kml else ''} をアップロード",
        "3. 位置の列に `Address`（座標があれば `Latitude` / `Longitude`）、タイトルの列に `Name` を選択",
        "",
        "作成したマイマップは Google マップアプリの「保存済み」→「マップ」から見られます。",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("spots_json", type=Path)
    ap.add_argument("--out", type=Path)
    ap.add_argument("--resolve", action="store_true", help="look up place IDs/coordinates via Places API (New)")
    args = ap.parse_args()

    trip = json.loads(args.spots_json.read_text(encoding="utf-8"))
    trip.setdefault("list_name", f"{trip['destination']}旅行")
    spots = trip.get("spots") or []
    if not spots:
        print("error: no spots in input", file=sys.stderr)
        return 1

    if args.resolve:
        api_key = os.environ.get("GOOGLE_MAPS_API_KEY", "injected-by-proxy")
        for s in spots:
            try:
                resolve_spot(s, trip["destination"], api_key)
            except urllib.error.HTTPError as e:
                s["resolve_error"] = f"HTTP {e.code}"
                detail = e.read().decode("utf-8", "replace")
                if e.code in (401, 403) or "API key" in detail:
                    print(f"error: Places API returned {e.code} (API key missing or not allowed)", file=sys.stderr)
                    return 2
            except urllib.error.URLError as e:
                s["resolve_error"] = str(e.reason)
            status = s.get("resolve_error") or s.get("place_id")
            print(f"  {s.get('name_ja') or s.get('name_en')}: {status}")

    out = args.out or Path("trips") / slugify(trip["list_name"])
    out.mkdir(parents=True, exist_ok=True)
    for s in spots:
        s["maps_url"] = maps_url(s, trip["destination"])
    (out / "spots.json").write_text(json.dumps(trip, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_csv(out / "spots.csv", spots, trip["destination"])
    n_kml = write_kml(out / "spots.kml", spots, trip["list_name"], trip["destination"])
    write_readme(out / "README.md", trip, spots, n_kml > 0)

    print(f"wrote {out}/ (spots.json, spots.csv, README.md{', spots.kml' if n_kml else ''}) — {len(spots)} spots, {n_kml} with coordinates")
    return 0


if __name__ == "__main__":
    sys.exit(main())
