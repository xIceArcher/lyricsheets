import argparse
import pyass
import re
import subprocess

from ass import REQUIRED_STYLES

from .consts import *


def populate_styles(styles: list[pyass.Style]) -> list[pyass.Style]:
    currStyles = {style.name: style for style in styles}
    for requiredStyle in REQUIRED_STYLES:
        if requiredStyle.name not in currStyles:
            styles.append(requiredStyle)

    return styles


def remove_old_song_lines(events: list[pyass.Event]) -> list[pyass.Event]:
    return [
        event
        for event in events
        if event.style == SONG_STYLE_NAME
        or not event.style.startswith(SONG_STYLE_NAME)
        or EVENT_EFFECT_TEMPLATE in event.effect
        or EVENT_EFFECT_CODE in event.effect
    ]


def populate_songs(
    spreadsheetId, inEvents: list[pyass.Event], shouldPrintTitle: bool
) -> list[pyass.Event]:
    outEvents = []

    for inEvent in inEvents:
        if inEvent.style == SONG_STYLE_NAME:
            inEvent.format = pyass.EventFormat.COMMENT
            outEvents.append(inEvent)

            allModifiers: list[Modifier] = []
            for match in re.findall(LYRICS_MODIFIER_TAG_REGEX, inEvent.text):
                allModifiers.extend(Modifiers.parse(match))

            songName = re.sub(TAGS_REGEX, "", inEvent.text)
            actualSongName = get_full_song_name(spreadsheetId, songName)
            if actualSongName is not None:
                print(f"Populating {actualSongName}")

                actorToStyle = get_format_string_map(spreadsheetId)
                actorToStyle = {k: pyass.Tags.parse(v) for k, v in actorToStyle.items()}

                switchDuration = timedelta(milliseconds=200)
                songEvents = get_song_events(
                    spreadsheetId,
                    actualSongName,
                    actorToStyle,
                    shouldPrintTitle,
                    switchDuration,
                    allModifiers,
                )

                firstLine = songEvents[3]
                if firstLine.effect == "karaoke":
                    # Karaoke effect lines have no switch duration
                    songOffset = inEvent.start - firstLine.start
                else:
                    songOffset = inEvent.start - firstLine.start - switchDuration

                for event in songEvents:
                    event.start += songOffset
                    event.end += songOffset

                    event.start = max(timedelta(0), event.start)
                    event.end = max(timedelta(0), event.end)

                outEvents.extend(songEvents)
            else:
                print(f"Could not find song {inEvent.text}")
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
    parser.add_argument("--source", help="Song source")

    args = parser.parse_args()

    with open(args.fname, encoding="utf_8_sig") as inputFile:
        inputAss = pyass.load(inputFile)

        inputAss.styles = populate_styles(inputAss.styles)

        inputAss.events = remove_old_song_lines(inputAss.events)
        inputAss.events = populate_songs(spreadsheetId, inputAss.events, args.title)

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
