from collections.abc import Mapping

from apiclient import discovery
from google.oauth2 import service_account
from token_bucket import MemoryStorage, Limiter

from .decorator import token_bucket

class GoogleSheetsClient:
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

    def __init__(self, googleCredentials: Mapping[str, str]) -> None:
        self.service = discovery.build(
            'sheets',
            'v4',
            credentials=service_account.Credentials.from_service_account_info(googleCredentials, scopes=GoogleSheetsClient.SCOPES)
        ).spreadsheets()

    def getValues(self, spreadsheetId: str, range: str):
        return self.service.values().get(spreadsheetId=spreadsheetId, range=range).execute()['values']

    def get(self, spreadsheetId: str, ranges: str, fields: str):
        return self.service.values().get(spreadsheetId=spreadsheetId, ranges=ranges, fields=fields).execute()

class RateLimitedGoogleSheetsClient(GoogleSheetsClient):
    def __init__(self, googleCredentials: Mapping[str, str]) -> None:
        super().__init__(googleCredentials)

        self.bucket = Limiter(rate=60, capacity=60, storage=MemoryStorage())

    @token_bucket('read', 1)
    def getValues(self, spreadsheetId: str, range: str):
        return super().getValues(spreadsheetId, range)

    @token_bucket('read', 1)
    def get(self, spreadsheetId: str, ranges: str, fields: str):
        return super().get(spreadsheetId, ranges, fields)
