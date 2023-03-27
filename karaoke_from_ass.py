import argparse
from models import Song, SongTitle

from print import *
from from_ass import *

def main():
    parser = argparse.ArgumentParser(
        description='Reads karaoke timing from an .ass file and uploads it to Google Sheets'
    )

    parser.add_argument('input_fname', help='Path to input file')
    parser.add_argument('title', help='Title of the song')

    args = parser.parse_args()
    if not os.path.isfile(args.input_fname):
        raise Exception(f'{args.input_fname} is not a file')

    lyrics = read_karaoke(args.input_fname)
    song = Song(
        title=SongTitle(
            romaji=args.title
        ),
        lyrics=lyrics,
    )

    create_new_song_sheet(spreadsheetId, song)
    print_title(spreadsheetId, args.title, song)
    print_line_times(spreadsheetId, args.title, song)
    print_line_karaoke(spreadsheetId, args.title, song)
    print_romaji(spreadsheetId, args.title, song)

if __name__ == '__main__':
    main()
