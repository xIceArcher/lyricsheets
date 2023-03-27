import argparse
import itertools
import typing
from models import Song, SongLine
import pyass

from functools import reduce

from scan import *
from modifier import *
from fonts import *

TITLE_CARD_TAGS = pyass.Tags([
    pyass.FadeTag(200,200),
    pyass.BlurEdgesTag(11),
    pyass.AlignmentTag(pyass.Alignment.TOP_LEFT),
])

LYRICS_TAGS = pyass.Tags([
    pyass.FadeTag(200,200),
    pyass.BlurEdgesTag(11),
    pyass.AlignmentTag(pyass.Alignment.CENTER),
])

ROMAJI_POS_TAG = pyass.PositionTag(960,960)
NO_EN_ROMAJI_POS_TAG = pyass.PositionTag(960,1010)
SECONDARY_ROMAJI_POS_TAG = pyass.PositionTag(960,65)

EN_POS_TAG = pyass.PositionTag(960,1015)
SECONDARY_EN_POS_TAG = pyass.PositionTag(960,120)

DIVIDER_STYLE = pyass.Style(
    name='Song - Divider',
)

TITLE_STYLE = pyass.Style(
    name='Song - Title',
    fontName='Museo Sans 900',
    fontSize=30,
    primaryColor=pyass.Color(r=0xFF, g=0xFF, b=0xFF, a=0x0A),
    secondaryColor=pyass.Color(a=0xF0),
    outlineColor=pyass.Color(a=0x0A),
    backColor=pyass.Color(r=0xD6, g=0x1E, b=0xA8),
    outline=3.0,
    shadow=0.0,
    alignment=pyass.Alignment.BOTTOM_LEFT,
    marginL=29,
    marginR=29,
    marginV=29,
)

ROMAJI_STYLE = pyass.Style(
    name='Song - JP',
    fontName='Proxima Nova Th',
    fontSize=58,
    isBold=True,
    outline=1.5,
    shadow=1.0,
    marginL=246,
    marginR=246,
    marginV=45,
)

EN_STYLE = pyass.Style(
    name='Song - EN',
    fontName='Avenir Next Rounded Pro',
    fontSize=40,
    isBold=True,
    outline=1.5,
    shadow=1.0,
    marginL=113,
    marginR=113,
    marginV=45,
)

def get_title_event_part(song: Song) -> pyass.EventPart:
    s: list[str] = [song.title.romaji]

    if song.title.en:
        s.append(f'({song.title.en})')

    s.append(song.creators.artist)

    if song.creators.composers:
        s.append(f"Composed by: {', '.join(song.creators.composers)}")

    if song.creators.arrangers:
        s.append(f"Arranged by: {', '.join(song.creators.arrangers)}")

    if song.creators.writers:
        s.append(f"Written by: {', '.join(song.creators.writers)}")

    return pyass.EventPart(
        tags=TITLE_CARD_TAGS,
        text=r'\N'.join(s)
    )

def get_fade_transform(lineLength: timedelta, offset: timedelta, switchDuration: timedelta, transitionDuration: timedelta) -> list[pyass.Tag]:
    return [
        pyass.AlphaTag(0xFF),
        pyass.TransformTag(start=offset, end=switchDuration+offset, to=[pyass.AlphaTag(0x00)]),
        pyass.TransformTag(start=lineLength-transitionDuration+switchDuration+offset, end=lineLength-transitionDuration+2*switchDuration+offset, to=[pyass.AlphaTag(0xFF)])
    ]

def get_style_tag(switchTime: timedelta, style: list[pyass.Tag], switchDuration: timedelta) -> list[pyass.Tag]:
    return [pyass.TransformTag(start=switchTime-switchDuration/2, end=switchTime+switchDuration/2, to=style)] if switchTime != timedelta() else style

def get_style_tags(line: SongLine, actorToStyle: typing.Mapping[str, list[pyass.Tag]], switchDuration: timedelta) -> list[pyass.Tag]:
    timedeltaUpToIdx = reduce(lambda a, b: a + [a[-1] + b.length], line.syllables, [timedelta(0)])
    return list(itertools.chain.from_iterable([get_style_tag(timedeltaUpToIdx[breakpoint], actorToStyle[actor], switchDuration) for actor, breakpoint in zip(line.actors, line.breakpoints)]))

def get_romaji_event_parts(line: SongLine, actorToStyle: typing.Mapping[str, list[pyass.Tag]], switchDuration: timedelta, transitionDuration: timedelta, withK: bool=True) -> list[pyass.EventPart]:
    if line.karaokeEffect:
        # Since the line has a karaoke effect we don't need to include any additional tags other than the karaoke ones and IFX to identify actors
        currBreakpointIdx = 0

        eventParts: list[pyass.EventPart] = []
        for syllableIdx, syllable in enumerate(line.syllables):
            eventPart = pyass.EventPart(
                tags=[pyass.KaraokeTag(duration=syllable.length)],
                text=syllable.text,
            )

            # Add IFX actor if this syllable is a breakpoint and this is the first character of the syllable
            if currBreakpointIdx < len(line.breakpoints) and syllableIdx == line.breakpoints[currBreakpointIdx]:
                eventPart.tags.append(pyass.IFXTag(line.actors[currBreakpointIdx]))
                currBreakpointIdx += 1

            eventParts.append(eventPart)

        return eventParts

    eventPart = pyass.EventPart(tags=LYRICS_TAGS)

    if line.isSecondary:
        eventPart.tags.append(SECONDARY_ROMAJI_POS_TAG)
    elif line.romaji == line.en:
        eventPart.tags.append(NO_EN_ROMAJI_POS_TAG)
    else:
        eventPart.tags.append(ROMAJI_POS_TAG)

    eventPart.tags.extend(get_style_tags(line, actorToStyle, switchDuration))

    if not withK:
        eventPart.text = line.romaji
        return [eventPart]

    eventParts: list[pyass.EventPart] = [eventPart]

    # Make sure the syllable finishes before the line starts fading
    line.syllables[-1].length = max(line.syllables[-1].length - switchDuration, switchDuration / 2)

    lineCharProportions = get_char_proportions_by_font_width(line.romaji, './Proxima Nova Extrabold.otf', ROMAJI_STYLE.fontSize)
    lineCharTimes = scale_and_round_unit_vector_preserving_sum(pyass.timedelta(transitionDuration).total_milliseconds(), lineCharProportions)

    lineCharIdx = 0
    charOffsetFromLineStart = timedelta()

    currBreakpointIdx = 0

    # Leading switch duration
    eventParts.append(pyass.EventPart(tags=[pyass.KaraokeTag(switchDuration)]))

    for syllableIdx, syllable in enumerate(line.syllables):
        # Split up the length of the current syllable to each of its characters
        # TODO: Allow custom fonts
        syllableCharProportions = get_char_proportions_by_font_width(syllable.text, './Proxima Nova Extrabold.otf', ROMAJI_STYLE.fontSize)
        syllableCharLengths = scale_and_round_unit_vector_preserving_sum(pyass.timedelta(syllable.length).total_centiseconds(), syllableCharProportions)

        for syllableCharIdx, c in enumerate(syllable.text):
            eventPart = pyass.EventPart(
                tags=get_fade_transform(line.length, charOffsetFromLineStart, switchDuration, transitionDuration),
                text=c
            )

            eventPart.tags.append(pyass.KaraokeTag(syllableCharLengths[syllableCharIdx]))

            charOffsetFromLineStart += timedelta(milliseconds=lineCharTimes[lineCharIdx])
            lineCharIdx += 1

            eventParts.append(eventPart)

    # Trailing switch duration
    eventParts.append(pyass.EventPart(tags=[pyass.KaraokeTag(switchDuration)]))

    return eventParts

def get_en_event_parts(line: SongLine, switchDuration: timedelta, transitionDuration: timedelta) -> list[pyass.EventPart]:
    lineCharProportions = get_char_proportions_by_font_width(line.en, './AVENIRNEXTROUNDEDPRO-DEMI.OTF', EN_STYLE.fontSize)
    lineCharTimes = scale_and_round_unit_vector_preserving_sum(pyass.timedelta(transitionDuration).total_milliseconds(), lineCharProportions)

    eventParts: list[pyass.EventPart] = []
    charOffsetFromLineStart = timedelta()
    for i, c in enumerate(line.en):
        eventParts.append(
            pyass.EventPart(
                tags=get_fade_transform(line.length, charOffsetFromLineStart, switchDuration, transitionDuration),
                text=c
            )
        )

        charOffsetFromLineStart += timedelta(milliseconds=lineCharTimes[i])

    return eventParts


def get_song_json_events(song: Song, actorToStyle: typing.Mapping[str, list[pyass.Tag]], shouldPrintTitle: bool, switchDuration: timedelta = timedelta(milliseconds=200), transitionDuration: timedelta = timedelta(milliseconds=500)):
    romajiEvents: list[pyass.Event] = []
    enEvents: list[pyass.Event] = []

    for line in song.lyrics:
        start = line.start if line.karaokeEffect else line.start - switchDuration
        end = line.end if line.karaokeEffect else line.end + switchDuration

        romajiEvents.append(pyass.Event(
            style=f'Song - {song.title.romaji} {line.karaokeEffect}' if line.karaokeEffect else ROMAJI_STYLE.name,
            start=start,
            end=end,
            parts=get_romaji_event_parts(line, actorToStyle, switchDuration, transitionDuration),
            effect='karaoke' if line.karaokeEffect else ''
        ))

        enEvents.append(pyass.Event(
            format=pyass.EventFormat.COMMENT if line.romaji == line.en else pyass.EventFormat.DIALOGUE,
            # style=f'Song - {song.title.romaji} {line.karaokeEffect} EN' if line.karaokeEffect else EN_STYLE.name,
            style=EN_STYLE.name,
            start=line.start - switchDuration,
            end=line.end + switchDuration,
            parts=[
                pyass.EventPart(tags=[*LYRICS_TAGS, SECONDARY_EN_POS_TAG if line.isSecondary else EN_POS_TAG]),
                pyass.EventPart(tags=get_style_tags(line, actorToStyle, switchDuration)),
                *get_en_event_parts(line, switchDuration, transitionDuration)
            ],
            effect='karaoke' if line.karaokeEffect else ''
        ))

    return [
        pyass.Event(
            format=pyass.EventFormat.COMMENT,
            style=DIVIDER_STYLE.name,
            end=romajiEvents[-1].end,
            text=song.title.romaji,
        ),
        pyass.Event(
            format=pyass.EventFormat.DIALOGUE if shouldPrintTitle else pyass.EventFormat.COMMENT,
            style=TITLE_STYLE.name,
            end=timedelta(seconds=5),
            parts=[get_title_event_part(song)]
        ),
        pyass.Event(
            format=pyass.EventFormat.COMMENT,
            style=DIVIDER_STYLE.name,
            end=romajiEvents[-1].end,
            text='Romaji',
        ),
        *romajiEvents,
        pyass.Event(
            format=pyass.EventFormat.COMMENT,
            style=DIVIDER_STYLE.name,
            end=romajiEvents[-1].end,
            text='English',
        ),
        *enEvents,
    ]

def get_song_events(spreadsheetId, songName: str, actorToStyle: typing.Mapping[str, list[pyass.Tag]], shouldPrintTitle: bool, switchDuration: timedelta = timedelta(milliseconds=200), modifiers: list[Modifier]=[]) -> pyass.EventsSection:
    song = scan_song(spreadsheetId, songName)
    song = modify_song(song, modifiers)

    return pyass.EventsSection(get_song_json_events(song, actorToStyle, shouldPrintTitle, switchDuration))

def main():
    parser = argparse.ArgumentParser(
        description='Generates an .ass file for a single song'
    )
    parser.add_argument('title', help='Title of the song')
    parser.add_argument('output_fname', help='Path to output file')
    parser.add_argument('--template', help='Path to template file', default='template.ass')
    parser.add_argument('--modifiers', help='Modifiers string', default='')

    args = parser.parse_args()

    actorToStyle = get_format_string_map(spreadsheetId)

    modifiers = Modifiers.parse(args.modifiers)

    with open(args.template, encoding='utf_8_sig') as templateFile:
        template = pyass.load(templateFile)
        template.events = get_song_events(spreadsheetId, args.title, actorToStyle, shouldPrintTitle=True, modifiers=modifiers)

        with open(args.output_fname, 'w+', encoding='utf_8_sig') as outFile:
            pyass.dump(template, outFile)

if __name__ == '__main__':
    main()
