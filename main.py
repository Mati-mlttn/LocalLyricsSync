from cli import get_args
from database import Database
from scanner import scan_library
from metadata import read_metadata
from lrclib import search
from downloader import save

from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import as_completed

from tqdm import tqdm

import requests


def process(song, db, force):

    if not force:
        cached = db.get_status(song)
        if cached == "found":
            return song, "cached", None

    try:
        meta = read_metadata(song)
    except Exception as e:
        db.upsert(song, "", "", "", "error_metadata", None)
        return song, "error_metadata", str(e)

    if meta is None:
        db.upsert(song, "", "", "", "no_metadata", None)
        return song, "no_metadata", None

    try:
        lyrics = search(meta)
    except requests.exceptions.RequestException as e:
        db.upsert(song, meta["artist"], meta["title"], meta["album"], "error_network", None)
        return song, "error_network", str(e)

    if lyrics is None:
        db.upsert(song, meta["artist"], meta["title"], meta["album"], "not_found", None)
        return song, "not_found", None

    try:
        saved = save(song, lyrics)
    except OSError as e:
        db.upsert(song, meta["artist"], meta["title"], meta["album"], "error_write", "lrclib")
        return song, "error_write", str(e)

    status = "found" if saved else "not_found"
    db.upsert(song, meta["artist"], meta["title"], meta["album"], status, "lrclib")
    return song, status, None


args = get_args()

db = Database(args.db)

songs = scan_library(args.library)

results = {}

with ThreadPoolExecutor(max_workers=args.threads) as executor:

    futures = {
        executor.submit(process, song, db, args.force): song
        for song in songs
    }

    for future in tqdm(as_completed(futures), total=len(futures)):
        song = futures[future]
        try:
            _, status, error = future.result()
        except Exception as e:
            status, error = "error_unexpected", str(e)

        results[status] = results.get(status, 0) + 1
        if error:
            tqdm.write(f"[{status}] {song}: {error}")

print()
for status, count in sorted(results.items()):
    print(f"{status}: {count}")