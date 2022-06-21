import argparse
import ass
import pytimeparse

from datetime import timedelta
from functools import reduce

from scan import *
from modifier import *

TITLE_CARD_TAG = r'{\fad(200,200)\be11\an7}'

LYRICS_TAG = r'{\fad(200,200)\be11\an5}'
SECONDARY_LYRICS_TAG = r'{\fad(200,200)\be11\an5}'

ROMAJI_POS_TAG = r'{\pos(960,960)}'
NO_EN_ROMAJI_POS_TAG = r'{\pos(960,1010)}'
SECONDARY_ROMAJI_POS_TAG = r'{\pos(960,65)}'

EN_POS_TAG = r"{\pos(960,1015)}"
SECONDARY_EN_POS_TAG = r"{\pos(960,120)}"

DIVIDER_STYLE_NAME = '-- DIVIDER --'
TITLE_STYLE_NAME = 'Title'
ROMAJI_STYLE_NAME = 'JP'
EN_STYLE_NAME = 'EN'

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

def get_style_tag(switchTime: int, style: str, switchDuration: int=200) -> str:
    return rf'{{\t({switchTime-switchDuration//2},{switchTime+switchDuration//2},{style})}}' if switchTime != 0 else rf'{{{style}}}'

def get_style_tags(line, actorToStyle: dict, switchDuration: int=200) -> str:
    csUpToIdx = reduce(lambda a, b: a + [a[-1] + b['len']], line['syllables'], [0])
    return ''.join([get_style_tag(csUpToIdx[breakpoint] * 10, actorToStyle[actor], switchDuration) for actor, breakpoint in zip(line['actors'], line['breakpoints'])])

def get_romaji_event_text(line, actorToStyle, withK=True, switchDuration: int=200) -> str:
    s = get_style_tags(line, actorToStyle, switchDuration)

    if not withK:
        s += ''.join([rf"{syllable['text']}" for syllable in line['syllables']])
    else:
        # Make sure the syllable finishes before the line starts fading
        line['syllables'][-1]['len'] = max(line['syllables'][-1]['len'] - switchDuration // 10, 10)

        s += ''.join([rf"{{\kf{syllable['len']}}}{syllable['text']}" for syllable in line['syllables']])

    if line['secondary']:
        return SECONDARY_LYRICS_TAG + SECONDARY_ROMAJI_POS_TAG + s
    elif line['romaji'] == line['en']:
        return LYRICS_TAG + NO_EN_ROMAJI_POS_TAG + s
    else:
        return LYRICS_TAG + ROMAJI_POS_TAG + s

def get_en_event_text(line, actorToStyle) -> str:
    s = get_style_tags(line, actorToStyle)
    return SECONDARY_LYRICS_TAG + SECONDARY_EN_POS_TAG + s + line['en'] if line['secondary'] else LYRICS_TAG + EN_POS_TAG + s + line['en']

def get_title_event_text(song) -> str:
    s = TITLE_CARD_TAG
    s += rf"{song['title']['romaji']}\N"
    s += rf"({song['title']['en']})\N" if 'en' in song['title'] else ''
    s += rf"{song['artist']}\N"
    s += rf"Composed by: {', '.join(song['composers'])}\N"
    s += rf"Arranged by: {', '.join(song['arrangers'])}\N"
    s += rf"Written by: {', '.join(song['writers'])}\N"

    return s

def get_song_events(spreadsheetId, songName, actorToStyle, shouldPrintTitle, modifiers: list[Modifier]=[]):
    songJson = scan_song(spreadsheetId, songName)
    songJson = modify_song(songJson, modifiers)

    return get_song_json_events(songJson, actorToStyle, shouldPrintTitle)

def get_song_json_events(songJson, actorToStyle, shouldPrintTitle):
    romajiEvents = []
    enEvents = []

    for line in songJson['lyrics']['detailed']:
        start = timedelta(seconds=pytimeparse.parse(line['start']))
        end =  timedelta(seconds=pytimeparse.parse(line['end']))

        romajiEvents.append(ass.line.Dialogue(
            style=ROMAJI_STYLE_NAME,
            start=start,
            end=end,
            text=get_romaji_event_text(line, actorToStyle),
        ))

        enLine = ass.line.Dialogue(
            style=EN_STYLE_NAME,
            start=start,
            end=end,
            text=get_en_event_text(line, actorToStyle),
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
        template.events = get_song_events(spreadsheetId, args.title, actorToStyle, modifiers=modifiers)

        with open(args.output_fname, 'w+', encoding='utf_8_sig') as outFile:
            template.dump_file(outFile)

if __name__ == '__main__':
    main()
