import argparse

from sheets import *

def get_title(spreadsheetId, sheetName, range='A1:A2'):
    result = service.values().get(spreadsheetId=spreadsheetId, range=f'{sheetName}!{range}').execute()['values']

    ret = {
        'title': {
            'romaji': result[0][0],           
        }
    }

    if len(result) > 1:
        ret['title']['en'] = result[1][0]

    return ret

def get_creators(spreadsheetId, sheetName, range='E1:E4'):
    result = service.values().get(spreadsheetId=spreadsheetId, range=f'{sheetName}!{range}').execute()['values']

    return {
        'artist': result[0][0],
        'composers': [composer.strip() for composer in result[1][0].split(',')],
        'arrangers': [composer.strip() for composer in result[2][0].split(',')],
        'writers': [composer.strip() for composer in result[3][0].split(',')],
    }

def get_lyrics(spreadsheetId, sheetName, rootPos='A6'):
    rootPosRow = get_row(rootPos)
    rootPosCol = get_column(rootPos)

    enLines = service.values().get(spreadsheetId=spreadsheetId, range=f'{sheetName}!{rootPos}:{rootPosCol}').execute()['values']
    ranges = [f'{sheetName}!{rootPosCol}{rootPosRow}:{rootPosRow + len(enLines) - 1}']

    result = service.get(
        spreadsheetId=spreadsheetId,
        ranges=ranges,
        fields='sheets.data.rowData.values(formattedValue,effectiveFormat.backgroundColor)'
    ).execute()

    formatToActorMap = {color_to_hex(format['backgroundColor']): actor for actor, format in get_format_map(spreadsheetId).items()}
    return {
        'lyrics': {
            'detailed': [parse_line(line, formatToActorMap) for line in result['sheets'][0]['data'][0]['rowData'] if 'formattedValue' in line['values'][0]]
        }
    }

def parse_line(rowData, formatToActorMap):
    values = rowData['values']
    timeAndSyllables = [syllable for syllable in values[get_column_idx('I'):] if 'formattedValue' in syllable]

    syllables = []
    actors = []
    breakpoints = []

    timeAndSyllablesIter = iter(timeAndSyllables)
    for i, (val1, val2) in enumerate(zip(timeAndSyllablesIter, timeAndSyllablesIter)):
        syllables.append({
            'len': int(val1['formattedValue']),
            'text': val2['formattedValue']
        })

        currActor = formatToActorMap[color_to_hex(val2['effectiveFormat']['backgroundColor'])]
        if not actors or currActor != actors[-1]:
            actors.append(currActor)
            breakpoints.append(i)

    return {
        'en': values[get_column_idx('A')]['formattedValue'],
        'romaji': ''.join([syllable['text'] for syllable in syllables]),
        'secondary': 'formattedValue' in values[get_column_idx('F')],
        'start': values[get_column_idx('G')]['formattedValue'],
        'end': values[get_column_idx('H')]['formattedValue'],
        'syllables': syllables,
        'actors': actors,
        'breakpoints': breakpoints,
    }

def get_song_json(spreadsheetId, songName):
    ret = {}
    
    ret.update(get_title(spreadsheetId, songName))
    ret.update(get_creators(spreadsheetId, songName))
    ret.update(get_lyrics(spreadsheetId, songName))

    return ret

def main():
    parser = argparse.ArgumentParser(
        description='Writes the JSON representation of a song to a file'
    )

    parser.add_argument('title', help='Title of the song')
    parser.add_argument('output_fname', help='Path to output file')

    args = parser.parse_args()

    song = get_song_json(spreadsheetId, args.title)
    
    with open(args.output_fname, 'w+') as f:
        json.dump(song, f)

if __name__ == '__main__':
    main()
