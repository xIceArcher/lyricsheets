import argparse
import ass
import pytimeparse

from datetime import timedelta
from functools import reduce

from scan import *
from modifier import *
from fonts import *

TITLE_CARD_TAG = r'{\fad(200,200)\be11\an7}'

LYRICS_TAG = r'{\fad(200,200)\be11\an5}'
SECONDARY_LYRICS_TAG = r'{\fad(200,200)\be11\an5}'

ROMAJI_POS_TAG = r'{\pos(960,960)}'
NO_EN_ROMAJI_POS_TAG = r'{\pos(960,1010)}'
SECONDARY_ROMAJI_POS_TAG = r'{\pos(960,65)}'

EN_POS_TAG = r"{\pos(960,1015)}"
SECONDARY_EN_POS_TAG = r"{\pos(960,120)}"

K_IFX_TAG = r'\-'

DIVIDER_STYLE_NAME = 'Song - Divider'
TITLE_STYLE_NAME = 'Song - Title'
ROMAJI_STYLE_NAME = 'Song - JP'
EN_STYLE_NAME = 'Song - EN'

DIVIDER_STYLE = ass.Style(
    name=DIVIDER_STYLE_NAME,
    fontname='Arial',
    fontsize=20.0,
    primary_color=ass.line.Color(r=0xff, g=0xff, b=0xff, a=0x00),
    secondary_color=ass.line.Color(r=0xff, g=0x00, b=0x00, a=0x00),
    outline_color=ass.line.Color(r=0x00, g=0x00, b=0x00, a=0x00),
    back_color=ass.line.Color(r=0x00, g=0x00, b=0x00, a=0x00),
    bold=True,
    italic=False,
    underline=False,
    strike_out=False,
    scale_x=100.0,
    scale_y=100.0,
    spacing=0.0,
    angle=0.0,
    border_style=1,
    outline=2.0,
    shadow=2.0,
    alignment=2,
    margin_l=9,
    margin_r=9,
    margin_v=9,
    encoding=1,
)

TITLE_STYLE = ass.Style(
    name=TITLE_STYLE_NAME,
    fontname='Museo Sans 900',
    fontsize=30.0,
    primary_color=ass.line.Color(r=0xff, g=0xff, b=0xff, a=0x0a),
    secondary_color=ass.line.Color(r=0x00, g=0x00, b=0x00, a=0xf0),
    outline_color=ass.line.Color(r=0x00, g=0x00, b=0x00, a=0x0a),
    back_color=ass.line.Color(r=0xd6, g=0x1e, b=0xa8, a=0x00),
    bold=False,
    italic=False,
    underline=False,
    strike_out=False,
    scale_x=100.0,
    scale_y=100.0,
    spacing=0.0,
    angle=0.0,
    border_style=1,
    outline=3.0,
    shadow=0.0,
    alignment=1,
    margin_l=29,
    margin_r=29,
    margin_v=29,
    encoding=1
)

ROMAJI_STYLE = ass.Style(
    name=ROMAJI_STYLE_NAME,
    fontname='Proxima Nova Th',
    fontsize=58.0,
    primary_color=ass.line.Color(r=0xff, g=0xff, b=0xff, a=0x00),
    secondary_color=ass.line.Color(r=0x00, g=0x00, b=0x00, a=0x00),
    outline_color=ass.line.Color(r=0xa5, g=0x46, b=0x9b, a=0x00),
    back_color=ass.line.Color(r=0x72, g=0x30, b=0x6b, a=0x00),
    bold=True,
    italic=False,
    underline=False,
    strike_out=False,
    scale_x=100.0,
    scale_y=100.0,
    spacing=0.0,
    angle=0.0,
    border_style=1,
    outline=1.5,
    shadow=1.0,
    alignment=2,
    margin_l=246,
    margin_r=246,
    margin_v=45,
    encoding=1
)

EN_STYLE = ass.Style(
    name=EN_STYLE_NAME,
    fontname='Avenir Next Rounded Pro',
    fontsize=40.0,
    primary_color=ass.line.Color(r=0xff, g=0xff, b=0xff, a=0x00),
    secondary_color=ass.line.Color(r=0xff, g=0x00, b=0x00, a=0x00),
    outline_color=ass.line.Color(r=0xa5, g=0x46, b=0x9b, a=0x00),
    back_color=ass.line.Color(r=0x72, g=0x30, b=0x6b, a=0x00),
    bold=True,
    italic=False,
    underline=False,
    strike_out=False,
    scale_x=100.0,
    scale_y=100.0,
    spacing=0.0,
    angle=0.0,
    border_style=1,
    outline=1.5,
    shadow=1.0,
    alignment=2,
    margin_l=113,
    margin_r=113,
    margin_v=45,
    encoding=1
)

def to_comment(line: ass.line.Dialogue) -> ass.line.Comment:
    return ass.line.Comment(
        layer=line.layer,
        start=line.start,
        end=line.end,
        style=line.style,
        name=line.name,
        margin_l=line.margin_l,
        margin_r=line.margin_r,
        margin_v=line.margin_v,
        effect=line.effect,
        text=line.text,
    )

def get_line_length(line) -> int:
    return int((timedelta(seconds=pytimeparse.parse(line['end'])) - timedelta(seconds=pytimeparse.parse(line['start']))).total_seconds() * 1000)

def get_title_event_text(song) -> str:
    s = TITLE_CARD_TAG
    s += rf"{song['title']['romaji']}\N"
    s += rf"({song['title']['en']})\N" if 'en' in song['title'] else ''
    s += rf"{song['artist']}\N"
    s += rf"Composed by: {', '.join(song['composers'])}\N" if 'composers' in song else ''
    s += rf"Arranged by: {', '.join(song['arrangers'])}\N" if 'arrangers' in song else ''
    s += rf"Written by: {', '.join(song['writers'])}" if 'writers' in song else ''

    return s

def to_tag(contents: str) -> str:
    return '{' + contents + '}'

def get_karaoke_tag(duration: int, ifx: str='') -> str:
    return to_tag(rf'\kf{duration}' + (rf'\-{ifx}' if ifx else ''))

def get_transformation(startTime: int, endTime: int, finalState: str) -> str:
    return r'\t(' + f'{startTime},{endTime},{finalState}' + ')'

def get_transform_tag(startState: str, transitions: list[tuple[int, int, str]]) -> str:
    return to_tag(startState + ''.join([get_transformation(startTime, endTime, finalState) for startTime, endTime, finalState in transitions]))

def get_fade_tag(lineLength: int, offset: int, switchDuration: int, transitionDuration: int) -> str:
    return get_transform_tag(
        r'\alpha&HFF&',
        [
            (offset, switchDuration+offset, r'\alpha&H00&'),
            (lineLength-transitionDuration+switchDuration+offset, lineLength-transitionDuration+2*switchDuration+offset, r'\alpha&HFF&'),
        ]
    )

def get_style_tag(switchTime: int, style: str, switchDuration: int) -> str:
    return get_transformation(switchTime-switchDuration//2, switchTime+switchDuration//2, style) if switchTime != 0 else style

def get_style_tags(line, actorToStyle: dict, switchDuration: int) -> str:
    csUpToIdx = reduce(lambda a, b: a + [a[-1] + b['len']], line['syllables'], [0])
    return to_tag(''.join([get_style_tag(csUpToIdx[breakpoint] * 10, actorToStyle[actor], switchDuration) for actor, breakpoint in zip(line['actors'], line['breakpoints'])]))

def get_romaji_event_text(line, actorToStyle, switchDuration, transitionDuration, withK=True) -> str:
    s = get_style_tags(line, actorToStyle, switchDuration)

    lineCharProportions = get_char_proportions_by_font_width(line['romaji'], './Proxima Nova Extrabold.otf', int(ROMAJI_STYLE.fontsize))
    lineCharTimes = scale_and_round_unit_vector_preserving_sum(transitionDuration, lineCharProportions)

    lineCharIdx = 0
    charOffsetFromLineStart = 0

    if not withK:
        s += line['romaji']
    else:
        # Make sure the syllable finishes before the line starts fading
        line['syllables'][-1]['len'] = max(line['syllables'][-1]['len'] - switchDuration // 10, 10)

        currBreakpointIdx = 0

        # Leading switch duration
        s += get_karaoke_tag(switchDuration // 10)

        for syllableIdx, syllable in enumerate(line['syllables']):
            # Split up the length of the current syllable to each of its characters
            # TODO: Allow custom fonts
            syllableCharProportions = get_char_proportions_by_font_width(syllable['text'], './Proxima Nova Extrabold.otf', int(ROMAJI_STYLE.fontsize))
            syllableCharLengths = scale_and_round_unit_vector_preserving_sum(syllable['len'], syllableCharProportions)

            for syllableCharIdx, c in enumerate(syllable['text']):
                s += get_fade_tag(get_line_length(line), charOffsetFromLineStart, switchDuration, transitionDuration)

                # Add IFX actor if this syllable is a breakpoint and this is the first character of the syllable
                if currBreakpointIdx < len(line['breakpoints']) and syllableIdx == line['breakpoints'][currBreakpointIdx] and syllableCharIdx == 0:
                    s += get_karaoke_tag(syllableCharLengths[syllableCharIdx], line['actors'][currBreakpointIdx])
                else:
                    s += get_karaoke_tag(syllableCharLengths[syllableCharIdx])

                s += c

                charOffsetFromLineStart += lineCharTimes[lineCharIdx]
                lineCharIdx += 1

        # Trailing switch duration
        s += get_karaoke_tag(switchDuration // 10)

    if line['secondary']:
        return SECONDARY_LYRICS_TAG + SECONDARY_ROMAJI_POS_TAG + s
    elif line['romaji'] == line['en']:
        return LYRICS_TAG + NO_EN_ROMAJI_POS_TAG + s
    else:
        return LYRICS_TAG + ROMAJI_POS_TAG + s

def get_en_event_text(line, actorToStyle, switchDuration, transitionDuration) -> str:
    lineCharProportions = get_char_proportions_by_font_width(line['en'], './AVENIRNEXTROUNDEDPRO-DEMI.OTF', int(EN_STYLE.fontsize))
    lineCharTimes = scale_and_round_unit_vector_preserving_sum(transitionDuration, lineCharProportions)

    s = get_style_tags(line, actorToStyle, switchDuration)

    charOffsetFromLineStart = 0
    for i, c in enumerate(line['en']):
        s += get_fade_tag(get_line_length(line), charOffsetFromLineStart, switchDuration, transitionDuration)

        s += c
        charOffsetFromLineStart += lineCharTimes[i]

    return SECONDARY_LYRICS_TAG + SECONDARY_EN_POS_TAG + s if line['secondary'] else LYRICS_TAG + EN_POS_TAG + s

def get_song_json_events(songJson, actorToStyle, shouldPrintTitle, switchDuration=200, transitionDuration=500):
    romajiEvents = []
    enEvents = []

    for line in songJson['lyrics']['detailed']:
        start = timedelta(seconds=pytimeparse.parse(line['start'])) - timedelta(milliseconds=switchDuration)
        end = timedelta(seconds=pytimeparse.parse(line['end'])) + timedelta(milliseconds=switchDuration)

        if line['karaoke']:
            romajiEvent = ass.line.Comment(
                style=f"Song - {songJson['title']['romaji']} {line['karaoke']}",
                start=start,
                end=end,
                text=get_romaji_event_text(line, actorToStyle, switchDuration, transitionDuration),
                effect='karaoke'
            )
        else:
            romajiEvent = ass.line.Dialogue(
                style=ROMAJI_STYLE_NAME,
                start=start,
                end=end,
                text=get_romaji_event_text(line, actorToStyle, switchDuration, transitionDuration),
            )

        romajiEvents.append(romajiEvent)

        enLine = ass.line.Dialogue(
            style=EN_STYLE_NAME,
            start=start,
            end=end,
            text=get_en_event_text(line, actorToStyle, switchDuration, transitionDuration),
        )

        if line['romaji'] != line['en']:
            enEvents.append(enLine)
        else:
            enEvents.append(to_comment(enLine))

    title = ass.line.Dialogue(
        style=TITLE_STYLE_NAME,
        text=get_title_event_text(songJson),
        end=timedelta(seconds=5),
    )

    if not shouldPrintTitle:
        title = to_comment(title)

    return [
        ass.line.Comment(
            style=DIVIDER_STYLE_NAME,
            text=songJson['title']['romaji'],
            end=romajiEvents[-1].end,
        ),
        title,
        ass.line.Comment(
            style=DIVIDER_STYLE_NAME,
            text='Romaji',
            end=romajiEvents[-1].end,
        ),
        *romajiEvents,
        ass.line.Comment(
            style=DIVIDER_STYLE_NAME,
            text='English',
            end=romajiEvents[-1].end,
        ),
        *enEvents,
    ]

def get_song_events(spreadsheetId, songName, actorToStyle, shouldPrintTitle, modifiers: list[Modifier]=[]):
    songJson = scan_song(spreadsheetId, songName)
    songJson = modify_song(songJson, modifiers)

    return get_song_json_events(songJson, actorToStyle, shouldPrintTitle)

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

    modifiers = parse_modifiers(args.modifiers)

    with open(args.template, encoding='utf_8_sig') as templateFile:
        template = ass.parse(templateFile)
        template.events = get_song_events(spreadsheetId, args.title, actorToStyle, shouldPrintTitle=True, modifiers=modifiers)

        with open(args.output_fname, 'w+', encoding='utf_8_sig') as outFile:
            template.dump_file(outFile)

if __name__ == '__main__':
    main()
