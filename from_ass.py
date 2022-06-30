import ass
import argparse
import os
import re
from datetime import timedelta

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
        description='Reads karaoke timing and prints out the style modifier'
    )

    parser.add_argument('input_fname', help='Path to input file')
    parser.add_argument('--offset', help='Index of first line', type=int, default=1)

    args = parser.parse_args()
    if not os.path.isfile(args.input_fname):
        raise Exception(f'{args.input_fname} is not a file')

    detailedLyrics = read_karaoke(args.input_fname)
    print(';'.join([f'Karaoke,{i+args.offset},{line["start"]},{line["end"]},{",".join([str(syllable["len"]) for syllable in line["syllables"]])}' for i, line in enumerate(detailedLyrics)]))

if __name__ == '__main__':
    main()
