from cli import get_args
from database import Database
from scanner import scan_library
from metadata import read_metadata
from lrclib import search
from downloader import save

from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import as_completed

from tqdm import tqdm

from pathlib import Path
import requests
import sys


STATUS_LABELS = {
    "found": "Lyrics downloaded",
    "not_found": "No synchronized lyrics found",
    "error_metadata": "Metadata read errors",
    "no_metadata": "Files without compatible metadata",
    "error_network": "Network errors",
    "error_write": "File write errors",
    "error_unexpected": "Unexpected errors"
}


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


def show_header(library, total):
    print()
    print("LocalLyricsSync")
    print("=" * 50)
    print(f"Library: {library}")
    print(f"Compatible songs found: {total}")


def show_plan(songs, statuses, force):
    new_count = sum(statuses[song] is None for song in songs)
    cached_count = sum(statuses[song] == "found" for song in songs)
    retry_count = len(songs) - new_count - cached_count

    if force:
        print(f"Force mode: {len(songs)} songs will be processed again.")
        return songs, cached_count

    pending = [song for song in songs if statuses[song] != "found"]

    if not statuses or all(status is None for status in statuses.values()):
        print(f"First run: {len(pending)} songs will be processed.")
        return pending, cached_count

    print(f"Already processed: {cached_count}")
    print(f"New songs: {new_count}")
    if retry_count:
        print(f"Previous searches to retry: {retry_count}")
    print(f"Songs to process now: {len(pending)}")
    return pending, cached_count


def show_summary(results, cached_count):
    print()
    print("Summary")
    print("-" * 50)
    if cached_count:
        print(f"Already up to date: {cached_count}")
    for status, label in STATUS_LABELS.items():
        count = results.get(status, 0)
        if count:
            print(f"{label}: {count}")


def main():
    args = get_args()
    library = Path(args.library).expanduser()

    if not library.exists():
        print(f"Music folder not found: {library}")
        return 1

    if not library.is_dir():
        print(f"The provided path is not a folder: {library}")
        return 1

    db = Database(args.db)
    songs = scan_library(library)
    statuses = {song: db.get_status(song) for song in songs}

    show_header(library.resolve(), len(songs))

    if not songs:
        print("No compatible audio files were found in this folder.")
        return 0

    pending, cached_count = show_plan(songs, statuses, args.force)

    if not pending:
        print()
        print("Your library is up to date. There are no new songs to process.")
        return 0

    results = {}

    print()
    with ThreadPoolExecutor(max_workers=args.threads) as executor:
        futures = {
            executor.submit(process, song, db, args.force): song
            for song in pending
        }

        with tqdm(
            as_completed(futures),
            total=len(futures),
            desc="Searching for lyrics",
            unit="song",
            dynamic_ncols=True
        ) as progress:
            for future in progress:
                song = futures[future]
                try:
                    _, status, error = future.result()
                except Exception as e:
                    status, error = "error_unexpected", str(e)

                results[status] = results.get(status, 0) + 1
                errors = sum(
                    count for result, count in results.items()
                    if result.startswith("error")
                )
                progress.set_postfix(
                    downloaded=results.get("found", 0),
                    not_found=results.get("not_found", 0),
                    errors=errors
                )

                if error:
                    label = STATUS_LABELS.get(status, status)
                    tqdm.write(f"{label} for '{song}': {error}")

    show_summary(results, 0 if args.force else cached_count)
    return 0


if __name__ == "__main__":
    sys.exit(main())
