import argparse
import ass
import re
import string
import subprocess

from sheets import *
from to_ass import *
from modifier import *

SONG_STYLE_NAME = 'Song'

TAGS_REGEX = r'\{[^\}]+\}'
LYRICS_MODIFIER_TAG_REGEX = r'\{\\lyricsmodify\(([^\)]+)\)}'

TEMPLATE = 'template'

def normalize_song_name(songName: str):
    asciiSongName = songName.encode('ascii', 'ignore').decode().lower()
    return ''.join('' if c in string.punctuation or c in string.whitespace else c for c in asciiSongName)

def get_full_song_name(spreadsheetId, inSongName: str):
    searchKey = normalize_song_name(inSongName)

    songNames = get_sheets_properties(spreadsheetId).keys()
    for songName in songNames:
        if normalize_song_name(songName) == searchKey:
            return songName

def populate_songs(spreadsheetId, inEvents, shouldPrintTitle):
    outEvents = []

    for inEvent in inEvents:
        if inEvent.style == SONG_STYLE_NAME:
            outEvents.append(to_comment(inEvent))

            allModifiers = []
            for match in re.findall(LYRICS_MODIFIER_TAG_REGEX, inEvent.text):
                allModifiers.extend(parse_modifiers(match))

            songName = re.sub(TAGS_REGEX, '', inEvent.text)
            actualSongName = get_full_song_name(spreadsheetId, songName)
            if actualSongName is not None:
                print(f'Populating {actualSongName}')

                actorToStyle = get_format_string_map(spreadsheetId)
                songEvents = get_song_events(spreadsheetId, actualSongName, actorToStyle, shouldPrintTitle, allModifiers)

                firstLine = songEvents[3]
                songOffset = inEvent.start - firstLine.start

                for event in songEvents:
                    event.start += songOffset
                    event.end += songOffset

                    event.start = max(timedelta(0), event.start)
                    event.end = max(timedelta(0), event.end)

                outEvents.extend(songEvents)
            else:
                print(f'Could not find song {inEvent.text}')
        else:
            outEvents.append(inEvent)

    return outEvents

def populate_styles(styles: list[ass.Style]):
    requiredStyles = {
        DIVIDER_STYLE_NAME: DIVIDER_STYLE,
        TITLE_STYLE_NAME: TITLE_STYLE,
        ROMAJI_STYLE_NAME: ROMAJI_STYLE,
        EN_STYLE_NAME: EN_STYLE,
    }

    currStyles = {style.name: style for style in styles}
    for requiredStyleName, requiredStyle in requiredStyles.items():
        if requiredStyleName not in currStyles:
            styles.append(requiredStyle)

    return styles

def remove_old_song_lines(events):
    return [event for event in events if event.style == SONG_STYLE_NAME or not event.style.startswith(SONG_STYLE_NAME) or TEMPLATE in event.effect]

def main():
    parser = argparse.ArgumentParser(
        description='Populate lyrics in an .ass file'
    )
    parser.add_argument('fname', help='Path to input file')
    parser.add_argument('--title', help='Whether to print the title', action=argparse.BooleanOptionalAction)

    args = parser.parse_args()

    inputAss = None
    with open(args.fname, encoding='utf_8_sig') as inputFile:
        inputAss = ass.parse(inputFile)

        inputAss.styles = populate_styles(inputAss.styles)

        inputAss.events = remove_old_song_lines(inputAss.events)
        inputAss.events = populate_songs(spreadsheetId, inputAss.events, args.title)

    with open(args.fname, 'w+', encoding='utf_8_sig') as outFile:
        inputAss.dump_file(outFile)
    
    try:
        subprocess.run(['aegisub-cli', '--automation', 'kara-templater.lua', args.fname, args.fname, 'Apply karaoke template'])
    except FileNotFoundError:
        pass

if __name__ == '__main__':
    main()
