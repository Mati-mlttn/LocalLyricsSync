from pathlib import Path

def save(song, lyrics):

    if lyrics is None:
        return False

    lrc = Path(song).with_suffix(".lrc")

    with open(lrc, "w", encoding="utf8") as f:
        f.write(lyrics)

    return True