from argparse import ArgumentParser

def get_args():
    parser = ArgumentParser(
        prog="lyrics-sync",
        description="Download synchronized LRC lyrics."
    )

    parser.add_argument(
        "library",
        help="Music library path"
    )

    parser.add_argument(
        "-t",
        "--threads",
        type=int,
        default=8,
        help="Worker threads (default: 8)"
    )

    parser.add_argument(
        "--db",
        default="lyrics.db",
        help="SQLite database"
    )

    parser.add_argument(
        "--force",
        action="store_true",
        help="Redownload existing lyrics"
    )

    return parser.parse_args()