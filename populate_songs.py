import argparse
import ass
import string

from sheets import *
from to_ass import get_song_events

SONG_STYLE_NAME = 'Song'

def normalize_song_name(songName: str):
    asciiSongName = songName.encode('ascii', 'ignore').decode().lower()
    return ''.join('' if c in string.punctuation or c in string.whitespace else c for c in asciiSongName)

def get_full_song_name(spreadsheetId, inSongName: str):
    searchKey = normalize_song_name(inSongName)

    songNames = get_sheets_properties(spreadsheetId).keys()
    for songName in songNames:
        if normalize_song_name(songName) == searchKey:
            return songName

def populate_songs(spreadsheetId, inEvents):
    outEvents = []

    for inEvent in inEvents:
        if inEvent.style == SONG_STYLE_NAME:
            actualSongName = get_full_song_name(spreadsheetId, inEvent.text)
            if actualSongName is not None:
                print(f'Populating {actualSongName}')

                actorToStyle = get_format_string_map(spreadsheetId)
                songEvents = get_song_events(spreadsheetId, actualSongName, actorToStyle)

                firstLine = songEvents[3]
                songOffset = inEvent.start - firstLine.start

                for event in songEvents:
                    event.start += songOffset
                    event.end += songOffset

                outEvents.extend(songEvents)
                continue
            else:
                print(f'Could not find song {inEvent.text}')

        outEvents.append(inEvent)

    return outEvents

def main():
    parser = argparse.ArgumentParser(
        description='Populate lyrics in an .ass file'
    )
    parser.add_argument('input_fname', help='Path to input file')
    parser.add_argument('output_fname', help='Path to output file')
    parser.add_argument('--template', help='Path to template file', default='template.ass')

    args = parser.parse_args()

    with open(args.input_fname, encoding='utf_8_sig') as inputFile:
        inputEvents = ass.parse(inputFile).events
        outputEvents = populate_songs(spreadsheetId, inputEvents)

        with open(args.template, encoding='utf_8_sig') as templateFile:
            template = ass.parse(templateFile)
            template.events = outputEvents

            with open(args.output_fname, 'w+', encoding='utf_8_sig') as outFile:
                template.dump_file(outFile)

if __name__ == '__main__':
    main()
