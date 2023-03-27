import argparse
from models import Song, SongCreators, SongLine, SongLineSyllable, SongTitle
import pyass

from sheets import *

def scan_title(spreadsheetId, sheetName, range='B1:B2') -> SongTitle:
    result = service.values().get(spreadsheetId=spreadsheetId, range=f'{sheetName}!{range}').execute()['values']

    ret = SongTitle(
        romaji=result[0][0]
    )

    if len(result) > 1:
        ret.en = result[1][0]

    return ret

def scan_creators(spreadsheetId, sheetName, range='E1:E4') -> SongCreators:
    result = service.values().get(spreadsheetId=spreadsheetId, range=f'{sheetName}!{range}').execute()['values']

    return SongCreators(
        artist=result[0][0],
        composers=[composer.strip() for composer in result[1][0].split(',')],
        arrangers=[composer.strip() for composer in result[2][0].split(',')],
        writers=[composer.strip() for composer in result[3][0].split(',')],
    )

def scan_lyrics(spreadsheetId, sheetName, rootPos='A6') -> list[SongLine]:
    rootPosRow = get_row(rootPos)
    rootPosCol = get_column(rootPos)

    enLines = service.values().get(spreadsheetId=spreadsheetId, range=f'{sheetName}!B{rootPosRow}:B').execute()['values']
    ranges = [f'{sheetName}!{rootPosCol}{rootPosRow}:{rootPosRow + len(enLines) - 1}']

    result = service.get(
        spreadsheetId=spreadsheetId,
        ranges=ranges,
        fields='sheets.data.rowData.values(formattedValue,effectiveFormat.backgroundColor)'
    ).execute()

    formatToActorMap = {color_to_hex(format['backgroundColor']): actor for actor, format in get_format_map(spreadsheetId).items()}
    return [parse_line(line, formatToActorMap) for line in result['sheets'][0]['data'][0]['rowData'] if 'formattedValue' in line['values'][1]]

def parse_line(rowData, formatToActorMap) -> SongLine:
    values = rowData['values']
    timeAndSyllables = [syllable for syllable in values[get_column_idx('I'):] if 'formattedValue' in syllable]

    syllables: list[SongLineSyllable] = []
    actors: list[str] = []
    breakpoints: list[int] = []

    timeAndSyllablesIter = iter(timeAndSyllables)
    for i, (val1, val2) in enumerate(zip(timeAndSyllablesIter, timeAndSyllablesIter)):
        syllables.append(SongLineSyllable(
            pyass.timedelta(centiseconds=int(val1['formattedValue'])),
            val2['formattedValue']
        ))

        currActor = formatToActorMap[color_to_hex(val2['effectiveFormat']['backgroundColor'])]
        if not actors or currActor != actors[-1]:
            actors.append(currActor)
            breakpoints.append(i)

    return SongLine(
        en=values[get_column_idx('B')]['formattedValue'],
        karaokeEffect=values[get_column_idx('D')].get('formattedValue'),
        isSecondary='formattedValue' in values[get_column_idx('F')],
        start=pyass.timedelta.parse(values[get_column_idx('G')]['formattedValue']),
        end=pyass.timedelta.parse(values[get_column_idx('H')]['formattedValue']),
        syllables=syllables,
        actors=actors,
        breakpoints=breakpoints,
    )

def scan_song(spreadsheetId, songName) -> Song:
    return Song(
        title=scan_title(spreadsheetId, songName),
        creators=scan_creators(spreadsheetId, songName),
        lyrics=scan_lyrics(spreadsheetId, songName),
    )

def main():
    parser = argparse.ArgumentParser(
        description='Writes the JSON representation of a song to a file'
    )

    parser.add_argument('title', help='Title of the song')
    parser.add_argument('output_fname', help='Path to output file')

    args = parser.parse_args()

    song = scan_song(spreadsheetId, args.title)

    with open(args.output_fname, 'w+') as f:
        json.dump(song, f)

if __name__ == '__main__':
    main()
