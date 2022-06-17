import argparse
import ass
import re
from datetime import timedelta

from print import *

def timedelta_to_str(td: timedelta):
    hours, remainder = td.total_seconds() // 3600, td.total_seconds() % 3600
    minutes, seconds = remainder // 60, remainder % 60

    return '{:01}:{:02}:{:02}.{:02}'.format(int(hours), int(minutes), int(seconds), int(td.microseconds // 10000))

def read_karaoke(filePath: str):
    with open(filePath, encoding='utf_8_sig') as f:
        rawSong = ass.parse(f)
        events = [event for event in rawSong.events if event.text != '']

        song = []

        for event in events:
            matches = re.findall(r'\{\\[kK][f]?([0-9]+)[^0-9]*\}([^\{]+)', event.text)
            if len(matches) == 0:
                continue

            syllables = [{'len': int(time), 'text': text} for time, text in matches]
            kTimeSumMicro = sum([int(time) for time, _ in matches]) * 10 * 1000

            if len(syllables) > 0:
                syllables[-1]['len'] -= int((timedelta(microseconds=kTimeSumMicro) - (event.end - event.start)).total_seconds() * 100)

            song.append({
                'syllables': syllables,
                'start': timedelta_to_str(event.start),
                'end': timedelta_to_str(event.end),
            })

        return song

def main():
    parser = argparse.ArgumentParser(
        description='Reads karaoke timing from an .ass file and uploads it to Google Sheets'
    )

    parser.add_argument('input_fname', help='Path to input file')
    parser.add_argument('title', help='Title of the song')

    args = parser.parse_args()
    if not os.path.isfile(args.input_fname):
        raise Exception(f'{args.input_fname} is not a file')

    detailedLyrics = read_karaoke(args.input_fname)
    song = {
        'title': {
            'romaji': args.title
        },
        'lyrics': {
            'detailed': detailedLyrics
        }
    }

    create_new_song_sheet(spreadsheetId, song)
    print_title(spreadsheetId, args.title, song)
    print_line_times(spreadsheetId, args.title, song)
    print_line_karaoke(spreadsheetId, args.title, song)
    print_romaji(spreadsheetId, args.title, song)

if __name__ == '__main__':
    main()
