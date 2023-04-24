import argparse
from collections.abc import Mapping, Sequence
from datetime import timedelta
import functools
import json
import pyass
import subprocess

from src.ass import REQUIRED_STYLES, to_events
from src.cache import MemoryCache
from src.service import SongService, SongServiceByDB
from src.models import Modifiers

SONG_STYLE_NAME = "Song"

EVENT_EFFECT_TEMPLATE = "template"
EVENT_EFFECT_CODE = "code"


def populate_styles(styles: Sequence[pyass.Style]) -> Sequence[pyass.Style]:
    ret = list(styles)

    currStyles = {style.name: style for style in styles}
    for requiredStyle in REQUIRED_STYLES:
        if requiredStyle.name not in currStyles:
            ret.append(requiredStyle)

    return ret


def filter_old_song_lines(events: Sequence[pyass.Event]) -> Sequence[pyass.Event]:
    return [
        event
        for event in events
        if event.style == SONG_STYLE_NAME
        or not event.style.startswith(SONG_STYLE_NAME)
        or EVENT_EFFECT_TEMPLATE in event.effect
        or EVENT_EFFECT_CODE in event.effect
    ]


def populate_song(
    songService: SongService,
    inEvent: pyass.Event,
    actorToStyle: Mapping[str, Sequence[pyass.Tag]],
    shouldPrintTitle: bool,
) -> Sequence[pyass.Event]:
    outEvents = []

    inEvent.format = pyass.EventFormat.COMMENT
    outEvents.append(inEvent)

    modifierTags = [
        tag.text.removeprefix("\\lyricsmodify(").removesuffix(")")
        for tag in functools.reduce(lambda ls, x: ls + x.tags, inEvent.parts, [])
        if isinstance(tag, pyass.tag.UnknownTag)
        and tag.text.startswith("\\lyricsmodify")
    ]
    allModifiers = functools.reduce(
        lambda ls, x: ls + Modifiers.parse(x), modifierTags, []
    )

    songName = inEvent.parts[0].text
    print(f"Populating {songName}")

    song = songService.get_song(songName).modify(Modifiers(allModifiers))


    songEvents = to_events(song, actorToStyle, shouldPrintTitle)
    songOffset = inEvent.start - song.start

    for event in songEvents:
        event.start += songOffset
        event.end += songOffset

        event.start = max(timedelta(0), event.start)
        event.end = max(timedelta(0), event.end)

    outEvents.extend(songEvents)

    return outEvents


def populate_songs(
    songService: SongService, inEvents: Sequence[pyass.Event], shouldPrintTitle: bool
) -> Sequence[pyass.Event]:
    outEvents = []

    actorToStyle = {
        k: pyass.Tags.parse(v) for k, v in songService.get_format_tags().items()
    }

    for inEvent in inEvents:
        if inEvent.style == SONG_STYLE_NAME:
            outEvents.extend(
                populate_song(songService, inEvent, actorToStyle, shouldPrintTitle)
            )
        else:
            outEvents.append(inEvent)

    return outEvents


def main():
    parser = argparse.ArgumentParser(description="Populate lyrics in an .ass file")
    parser.add_argument("fname", help="Path to input file")
    parser.add_argument(
        "--title",
        help="Whether to print the title",
        action=argparse.BooleanOptionalAction,
        default=True,
    )
    parser.add_argument("--config", help="Path to config file", default="./config.json")

    args = parser.parse_args()

    with open(args.config) as f:
        config = json.load(f)

    songService = SongServiceByDB(
        config["google_credentials"],
        config["spreadsheet_id"],
        MemoryCache(),
    )

    with open(args.fname, encoding="utf_8_sig") as inputFile:
        inputAss = pyass.load(inputFile)

        inputAss.styles = populate_styles(inputAss.styles)

        inputAss.events = filter_old_song_lines(inputAss.events)
        inputAss.events = populate_songs(songService, inputAss.events, args.title)

        with open(args.fname, "w+", encoding="utf_8_sig") as outFile:
            pyass.dump(inputAss, outFile)

    try:
        subprocess.run(
            [
                "aegisub-cli",
                "--automation",
                "kara-templater.lua",
                args.fname,
                args.fname,
                "Apply karaoke template",
            ]
        )
    except FileNotFoundError:
        pass


if __name__ == "__main__":
    main()
