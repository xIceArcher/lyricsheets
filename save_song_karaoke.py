import argparse
import json
import os
import pyass

from src.ass import read_karaoke
from src.models import Song, SongTitle
from src.service import SongServiceByDB


def main():
    parser = argparse.ArgumentParser(
        description="Reads karaoke timing from an .ass file and uploads it to Google Sheets"
    )

    parser.add_argument("input_fname", help="Path to input file")
    parser.add_argument("title", help="Title of the song")
    parser.add_argument("--config", help="Path to config file", default="./config.json")

    args = parser.parse_args()
    if not os.path.isfile(args.input_fname):
        raise Exception(f"{args.input_fname} is not a file")

    with open(args.config) as f:
        config = json.load(f)

    with open(args.input_fname, encoding="utf_8_sig") as f:
        rawFile = pyass.load(f)

        song = Song(
            title=SongTitle(romaji=args.title),
            lyrics=read_karaoke(rawFile.events),
        )

    songService = SongServiceByDB(
        config["google_credentials"],
        config["spreadsheet_id"],
    )

    songService.save_song(song)


if __name__ == "__main__":
    main()
