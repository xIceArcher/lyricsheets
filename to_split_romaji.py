from scan import *
from populate_songs import *

def main():
    parser = argparse.ArgumentParser(
        description='Prints the romaji lines of a song to be used as input into the karaoke timing app'
    )
    parser.add_argument('song_name')
    parser.add_argument('--line-nums', nargs='*', type=int)

    args = parser.parse_args()
    songJson = scan_lyrics(spreadsheetId, get_full_song_name(spreadsheetId, args.song_name))
    for i, line in enumerate(songJson['lyrics']['detailed']):
        if not args.line_nums or i+1 in args.line_nums:
            print('|'.join([syllable['text'] for syllable in line['syllables']]))

if __name__ == '__main__':
    main()
