import argparse
import ass
import re
import string

from sheets import *
from to_ass import get_song_events, to_comment
from modifier import *

SONG_STYLE_NAME = 'Song'

TAGS_REGEX = r'\{[^\}]+\}'
LYRICS_MODIFIER_TAG_REGEX = r'\{\\lyricsmodify\(([^\)]+)\)}'

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

                outEvents.extend(songEvents)
            else:
                print(f'Could not find song {inEvent.text}')
        else:
            outEvents.append(inEvent)

    return outEvents

def main():
    parser = argparse.ArgumentParser(
        description='Populate lyrics in an .ass file'
    )
    parser.add_argument('input_fname', help='Path to input file')
    parser.add_argument('output_fname', help='Path to output file')
    parser.add_argument('--title', help='Whether to print the title', action=argparse.BooleanOptionalAction)

    args = parser.parse_args()

    with open(args.input_fname, encoding='utf_8_sig') as inputFile:
        inputAss = ass.parse(inputFile)
        inputAss.events = populate_songs(spreadsheetId, inputAss.events, args.title)

        with open(args.output_fname, 'w+', encoding='utf_8_sig') as outFile:
            inputAss.dump_file(outFile)

if __name__ == '__main__':
    main()
