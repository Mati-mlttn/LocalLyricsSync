import requests

GET_URL = "https://lrclib.net/api/get"
SEARCH_URL = "https://lrclib.net/api/search"

DURATION_TOLERANCE = 2


def search(track):

    lyrics = _search_get(track)

    if lyrics is not None:
        return lyrics

    return _search_fallback(track)


def _search_get(track):

    params = {
        "artist_name": track["artist"],
        "track_name": track["title"],
        "album_name": track["album"],
        "duration": track["duration"]
    }

    r = requests.get(GET_URL, params=params, timeout=20)

    if r.status_code != 200:
        return None

    data = r.json()

    return data.get("syncedLyrics")


def _search_fallback(track):

    params = _build_search_params(track)

    r = requests.get(SEARCH_URL, params=params, timeout=20)

    if r.status_code != 200:
        return None

    results = r.json()

    best_lyrics = None
    best_diff = None

    for result in results:

        synced = result.get("syncedLyrics")

        if not synced:
            continue

        duration = result.get("duration")

        if duration is None:
            continue

        diff = abs(duration - track["duration"])

        if diff > DURATION_TOLERANCE:
            continue

        if best_diff is None or diff < best_diff:
            best_lyrics = synced
            best_diff = diff

    return best_lyrics


def _build_search_params(track):

    params = {"track_name": track["title"]}

    if track["artist"]:
        params["artist_name"] = track["artist"]

    if track["album"]:
        params["album_name"] = track["album"]

    return params