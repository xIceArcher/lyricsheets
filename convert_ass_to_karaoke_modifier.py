import argparse
import os
import pyass

from lyricsheets.ass import read_karaoke


def main():
    parser = argparse.ArgumentParser(
        description="Reads karaoke timing and prints out the style modifier"
    )

    parser.add_argument("input_fname", help="Path to input file")
    parser.add_argument("--offset", help="Index of first line", type=int, default=1)

    args = parser.parse_args()
    if not os.path.isfile(args.input_fname):
        raise Exception(f"{args.input_fname} is not a file")

    with open(args.input_fname, encoding="utf_8_sig") as f:
        rawFile = pyass.load(f)
        detailedLyrics = read_karaoke(rawFile.events)

        print(
            ";".join(
                [
                    f'Karaoke,{i+args.offset},{line.start},{line.end},{",".join([str(int(syllable.length.total_seconds() * 100)) for syllable in line.syllables])}'
                    for i, line in enumerate(detailedLyrics)
                ]
            )
        )


if __name__ == "__main__":
    main()
