from utils import *

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
TEMPLATE_SHEET_NAME = 'Template'

def get_sheets_properties(service, spreadsheetId) -> dict[str, str]:
    resp = service.get(spreadsheetId=spreadsheetId,fields='sheets.properties').execute()
    return {sheet['properties']['title']: sheet['properties']['sheetId'] for sheet in resp['sheets']}

def get_format_map(service, spreadsheetId, rootPos='I1'):
    row = get_row(rootPos) + 1

    resp = service.get(spreadsheetId=spreadsheetId,ranges=f'{TEMPLATE_SHEET_NAME}!{rootPos}:{row}',fields='sheets.data.rowData.values(userEnteredValue,userEnteredFormat(backgroundColor,textFormat.foregroundColor))').execute()
    return {resp['sheets'][0]['data'][0]['rowData'][1]['values'][i-1]['userEnteredValue']['stringValue']: v['userEnteredFormat'] for i, v in enumerate(resp['sheets'][0]['data'][0]['rowData'][0]['values']) if 'userEnteredFormat' in v and 'userEnteredValue' in v and not is_white(v['userEnteredFormat']['backgroundColor'])}

def get_format_string_map(service, spreadsheetId, rootPos='I1'):
    row = get_row(rootPos) + 1

    resp = service.get(spreadsheetId=spreadsheetId,ranges=f'{TEMPLATE_SHEET_NAME}!{rootPos}:{row}',fields='sheets.data.rowData.values.userEnteredValue').execute()
    respIter0 = iter(resp['sheets'][0]['data'][0]['rowData'][0]['values'])
    respIter1 = iter(resp['sheets'][0]['data'][0]['rowData'][1]['values'])

    return {formatKey['userEnteredValue']['stringValue']: formatStr['userEnteredValue']['stringValue'] for formatStr, formatKey in zip(respIter0, respIter1) if 'userEnteredValue' in formatStr and 'userEnteredValue' in formatKey}
