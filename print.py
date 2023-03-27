import functools
import operator
from models import Song
import pyass
import datetime

from sheets import *

def create_new_song_sheet(spreadsheetId, song: Song):
    allSheets = get_sheets_properties(spreadsheetId)
    duplicateSheetReq = {
        'duplicateSheet': {
            'sourceSheetId': allSheets[TEMPLATE_SHEET_NAME],
            'insertSheetIndex': len(allSheets)-1, # Template sheet should be the last sheet
            'newSheetName': song.title.romaji,
        }
    }

    body = {
        'requests': [duplicateSheetReq],
    }

    return service.batchUpdate(spreadsheetId=spreadsheetId, body=body).execute()

def print_title(spreadsheetId, sheetName, song: Song, rootPos='B1'):
    body = {
        'values': [
            [song.title.romaji],
            [song.title.en if song.title.en else ''],
        ]
    }

    return service.values().append(spreadsheetId=spreadsheetId, range=f'{sheetName}!{rootPos}', body=body, valueInputOption='RAW').execute()

def print_creators(spreadsheetId, sheetName, song: Song, rootPos='E1'):
    body = {
        'values': [
            [song.creators.artist],
            [', '.join(song.creators.composers)],
            [', '.join(song.creators.arrangers)],
            [', '.join(song.creators.writers)],
        ]
    }

    return service.values().append(spreadsheetId=spreadsheetId, range=f'{sheetName}!{rootPos}', body=body, valueInputOption='RAW').execute()

def print_preamble(spreadsheetId, sheetName, song: Song):
    print_title(spreadsheetId, sheetName, song)
    print_creators(spreadsheetId, sheetName, song)

def print_english(spreadsheetId, sheetName, song: Song, rootPos='B6'):
    body = {
        'values': [[line.en] for line in song.lyrics]
    }

    return service.values().append(spreadsheetId=spreadsheetId, range=f'{sheetName}!{rootPos}', body=body, valueInputOption='RAW').execute()

def print_is_secondary(spreadsheetId, sheetName, song: Song, rootPos='F6'):
    body = {
        'values': [['U'] if line.isSecondary else [] for line in song.lyrics]
    }

    return service.values().append(spreadsheetId=spreadsheetId, range=f'{sheetName}!{rootPos}', body=body, valueInputOption='RAW').execute()

def print_line_times(spreadsheetId, sheetName, song: Song, rootPos='G6'):
    body = {
        'values': [[str(pyass.timedelta(line.start)), str(pyass.timedelta(line.end))] for line in song.lyrics]
    }

    return service.values().append(spreadsheetId=spreadsheetId, range=f'{sheetName}!{rootPos}', body=body, valueInputOption='RAW').execute()

def print_line_karaoke(spreadsheetId, sheetName, song: Song, rootPos='I6'):
    body = {
        'values': [functools.reduce(operator.iconcat, [[pyass.timedelta(syllable.length).total_centiseconds(), syllable.text] for syllable in line.syllables], []) for line in song.lyrics],
    }

    return service.values().append(spreadsheetId=spreadsheetId, range=f'{sheetName}!{rootPos}', body=body, valueInputOption='RAW').execute()

def color_syllables(spreadsheetId, sheetName, song: Song, rootPos='I6'):
    sheetId = get_sheets_properties(spreadsheetId)[sheetName]
    rowOffset = get_row_idx(rootPos)
    columnOffset = get_column_idx(rootPos)

    formatMap = get_format_map(spreadsheetId)

    reqs = []
    for lineIdx, line in enumerate(song.lyrics):
        for i in range(len(line.actors)):
            actor = line.actors[i]
            startIdx = line.breakpoints[i]
            endIdx = len(line.syllables) if i == len(line.actors) - 1 else line.breakpoints[i+1]

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

def print_romaji(spreadsheetId, sheetName, song: Song, rootPos='E6'):
    r = get_row(rootPos)

    body = {
        'values': [[f'=CONCATENATE(ARRAYFORMULA(IF(MOD(COLUMN(I{r+i}:{r+i}),2)=MOD(COLUMN(I{r+i}),2), "", I{r+i}:{r+i})))'] for i in range(len(song.lyrics))]
    }

    return service.values().append(spreadsheetId=spreadsheetId, range=f'{sheetName}!{rootPos}', body=body, valueInputOption='USER_ENTERED').execute()

def print_song(spreadsheetId, song: Song):
    create_new_song_sheet(spreadsheetId, song)

    newSheetName = song.title.romaji
    print_preamble(spreadsheetId, newSheetName, song)
    print_english(spreadsheetId, newSheetName, song)
    print_is_secondary(spreadsheetId, newSheetName, song)
    print_line_times(spreadsheetId, newSheetName, song)
    print_line_karaoke(spreadsheetId, newSheetName, song)
    print_romaji(spreadsheetId, newSheetName, song)
    color_syllables(spreadsheetId, newSheetName, song)
