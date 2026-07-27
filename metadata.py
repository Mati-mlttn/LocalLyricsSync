from mutagen import File

def read_metadata(path):

    audio = File(path, easy=True)

    if audio is None:
        return None

    return {
        "artist": audio.get("artist", [""])[0],
        "title": audio.get("title", [""])[0],
        "album": audio.get("album", [""])[0],
        "duration": int(audio.info.length)
    }