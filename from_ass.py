import functools
from models import SongLine, SongLineSyllable
import pyass
import argparse
import os
import re
from datetime import timedelta

def read_karaoke(filePath: str) -> list[SongLine]:
    with open(filePath, encoding='utf_8_sig') as f:
        rawSong = pyass.load(f)
        events = [event for event in rawSong.events if event.text != '']

        ret = []

        for event in events:
            matches: list[tuple[int, str]] = re.findall(r'\{\\[kK][f]?([0-9]+)[^0-9]*\}([^\{]+)', event.text)
            if len(matches) == 0:
                continue

            syllables = [SongLineSyllable(length=pyass.timedelta(centiseconds=int(time)), text=text) for time, text in matches]
            kTimeSum = functools.reduce(lambda a, b: a + b.length, syllables, timedelta())

            if len(syllables) > 0:
                syllables[-1].length -= kTimeSum - event.length

            ret.append(SongLine(
                syllables=syllables,
                start=event.start,
                end=event.end,
            ))

        return ret

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
    print(';'.join([f'Karaoke,{i+args.offset},{line.start},{line.end},{",".join([str(round(syllable.length.total_seconds() * 100)) for syllable in line.syllables])}' for i, line in enumerate(detailedLyrics)]))

if __name__ == '__main__':
    main()
