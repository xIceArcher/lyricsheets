import os
import json

from apiclient import discovery
from google.oauth2 import service_account

from utils import *

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
CONFIG_PATH = os.path.join(os.getcwd(), 'config.json')
TEMPLATE_SHEET_NAME = 'Template'

service = None
spreadsheetId = None

with open(CONFIG_PATH) as f:
    config = json.load(f)
    service = discovery.build('sheets', 'v4', credentials=service_account.Credentials.from_service_account_info(config['google_credentials'], scopes=SCOPES)).spreadsheets()
    spreadsheetId = config['spreadsheet_id']

def get_sheets_properties(spreadsheetId):
    resp = service.get(spreadsheetId=spreadsheetId,fields='sheets.properties').execute()
    return {sheet['properties']['title']: sheet['properties']['sheetId'] for sheet in resp['sheets']}

def get_format_map(spreadsheetId, rootPos='J1'):
    row = get_row(rootPos)

    resp = service.get(spreadsheetId=spreadsheetId,ranges=f'{TEMPLATE_SHEET_NAME}!{rootPos}:{row}',fields='sheets.data.rowData.values(userEnteredValue,userEnteredFormat(backgroundColor,textFormat.foregroundColor))').execute()
    return {value['userEnteredValue']['numberValue']: value['userEnteredFormat'] for value in resp['sheets'][0]['data'][0]['rowData'][0]['values'] if 'userEnteredFormat' in value and 'userEnteredValue' in value}

