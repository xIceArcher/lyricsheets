import argparse
import json

from src.cache import MemoryCache
from src.service import SongServiceByDB


def main():
    parser = argparse.ArgumentParser(
        description="Prints the romaji lines of a song to be used as input into the karaoke timing app"
    )
    parser.add_argument("song_name")
    parser.add_argument("--line-nums", nargs="*", type=int)
    parser.add_argument("--config", help="Path to config file", default="./config.json")

    args = parser.parse_args()

    with open(args.config) as f:
        config = json.load(f)

    songService = SongServiceByDB(
        config["google_credentials"],
        config["spreadsheets"],
        config["spreadsheet_id"],
        MemoryCache(),
    )

    song = songService.get_song(args.song_name)
    for i, line in enumerate(song.lyrics):
        if not args.line_nums or i + 1 in args.line_nums:
            print("|".join([syllable.text for syllable in line.syllables]))


if __name__ == "__main__":
    main()
