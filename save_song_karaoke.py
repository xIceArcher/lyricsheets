import argparse
from datetime import timedelta
import functools
import json
import os
import pyass

from src.models import Song, SongLine, SongLineSyllable, SongTitle
from src.service import SongServiceByDB


def read_karaoke(filePath: str) -> list[SongLine]:
    with open(filePath, encoding="utf_8_sig") as f:
        rawSong = pyass.load(f)
        events = [event for event in rawSong.events if event.text != ""]

        ret = []
        for event in events:
            syllables: list[SongLineSyllable] = []

            for part in event.parts:
                karaokeTags = [
                    tag for tag in part.tags if isinstance(tag, pyass.KaraokeTag)
                ]
                if len(karaokeTags) != 1:
                    continue

                syllables.append(
                    SongLineSyllable(length=karaokeTags[0].duration, text=part.text)
                )

            kTimeSum = functools.reduce(
                lambda a, b: a + b.length, syllables, timedelta()
            )

            if len(syllables) > 0:
                syllables[-1].length -= kTimeSum - event.length

            ret.append(
                SongLine(
                    syllables=syllables,
                    start=event.start,
                    end=event.end,
                )
            )

        return ret


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

    song = Song(
        title=SongTitle(romaji=args.title),
        lyrics=read_karaoke(args.input_fname),
    )

    songService = SongServiceByDB(
        config["google_credentials"],
        config["spreadsheet_id"],
    )

    songService.save_song(song)


if __name__ == "__main__":
    main()
