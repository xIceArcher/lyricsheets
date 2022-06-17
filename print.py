import functools
import operator

from sheets import *

def create_new_song_sheet(spreadsheetId, song):
    allSheets = get_sheets_properties(spreadsheetId)
    duplicateSheetReq = {
        'duplicateSheet': {
            'sourceSheetId': allSheets[TEMPLATE_SHEET_NAME],
            'insertSheetIndex': len(allSheets)-1, # Template sheet should be the last sheet
            'newSheetName': song['title']['romaji'],
        }
    }

    body = {
        'requests': [duplicateSheetReq],
    }

    return service.batchUpdate(spreadsheetId=spreadsheetId, body=body).execute()

def print_title(spreadsheetId, sheetName, song, rootPos='A1'):
    body = {
        'values': [
            [song['title']['romaji']],
            [song['title']['en'] if 'en' in song['title'] else ''],
        ]
    }

    return service.values().append(spreadsheetId=spreadsheetId, range=f'{sheetName}!{rootPos}', body=body, valueInputOption='RAW').execute()

def print_creators(spreadsheetId, sheetName, song, rootPos='E1'):
    body = {
        'values': [
            [song['artist']],
            [', '.join(song['composers'])],
            [', '.join(song['arrangers'])],
            [', '.join(song['writers'])],
        ]
    }

    return service.values().append(spreadsheetId=spreadsheetId, range=f'{sheetName}!{rootPos}', body=body, valueInputOption='RAW').execute()

def print_preamble(spreadsheetId, sheetName, song):
    print_title(spreadsheetId, sheetName, song)
    print_creators(spreadsheetId, sheetName, song)

def print_english(spreadsheetId, sheetName, song, rootPos='A6'):
    body = {
        'values': [[line['en']] for line in song['lyrics']['detailed']]
    }

    return service.values().append(spreadsheetId=spreadsheetId, range=f'{sheetName}!{rootPos}', body=body, valueInputOption='RAW').execute()

def print_is_secondary(spreadsheetId, sheetName, song, rootPos='F6'):
    body = {
        'values': [['U' if line['secondary'] else '' for line in song['lyrics']['detailed']]]
    }

    return service.values().append(spreadsheetId=spreadsheetId, range=f'{sheetName}!{rootPos}', body=body, valueInputOption='RAW').execute()

def print_line_times(spreadsheetId, sheetName, song, rootPos='G6'):
    body = {
        'values': [[line['start'], line['end']] for line in song['lyrics']['detailed']]
    }

    return service.values().append(spreadsheetId=spreadsheetId, range=f'{sheetName}!{rootPos}', body=body, valueInputOption='RAW').execute()

def print_line_karaoke(spreadsheetId, sheetName, song, rootPos='I6'):
    body = {
        'values': [functools.reduce(operator.iconcat, [[int(syllable['len']), syllable['text']] for syllable in line['syllables']], []) for line in song['lyrics']['detailed']],
    }

    return service.values().append(spreadsheetId=spreadsheetId, range=f'{sheetName}!{rootPos}', body=body, valueInputOption='RAW').execute()

def color_syllables(spreadsheetId, sheetName, song, rootPos='I6'):
    sheetId = get_sheets_properties(spreadsheetId)[sheetName]
    rowOffset = get_row_idx(rootPos)
    columnOffset = get_column_idx(rootPos)

    formatMap = get_format_map(spreadsheetId)

    reqs = []
    for lineIdx, line in enumerate(song['lyrics']['detailed']):
        for i in range(len(line['actors'])):
            actor = line['actors'][i]
            startIdx = int(line['breakpoints'][i])
            endIdx = len(line['syllables']) if i == len(line['actors']) - 1 else int(line['breakpoints'][i+1])

            req = {
                'repeatCell': {
                    'range': {
                        'sheetId': sheetId,
                        'startRowIndex': rowOffset+lineIdx,
                        'endRowIndex': rowOffset+lineIdx+1,
                        'startColumnIndex': columnOffset+startIdx*2,
                        'endColumnIndex': columnOffset+endIdx*2,
                    },
                    'cell': {
                        'userEnteredFormat': formatMap[int(actor)]
                    },
                    'fields': 'userEnteredFormat(backgroundColor,textFormat.foregroundColor)'
                }
            }

            reqs.append(req)

    body = {
        'requests': reqs
    }

    return service.batchUpdate(spreadsheetId=spreadsheetId,body=body).execute()

def print_romaji(spreadsheetId, sheetName, song, rootPos='E6'):
    r = get_row(rootPos)

    body = {
        'values': [[f'=CONCATENATE(ARRAYFORMULA(IF(MOD(COLUMN(I{r+i}:{r+i}),2)=MOD(COLUMN(I{r+i}),2), "", I{r+i}:{r+i})))'] for i in range(len(song['lyrics']['detailed']))]
    }

    return service.values().append(spreadsheetId=spreadsheetId, range=f'{sheetName}!{rootPos}', body=body, valueInputOption='USER_ENTERED').execute()
