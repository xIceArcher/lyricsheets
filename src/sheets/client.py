from collections.abc import Mapping, Sequence

from apiclient import discovery
from google.oauth2 import service_account
from token_bucket import MemoryStorage

from .decorator import token_bucket
from .limiter import BurstLimiter


class GoogleSheetsClient:
    SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

    def __init__(self, googleCredentials: Mapping[str, str]) -> None:
        self.service = discovery.build(
            "sheets",
            "v4",
            credentials=service_account.Credentials.from_service_account_info(
                googleCredentials, scopes=GoogleSheetsClient.SCOPES
            ),
        ).spreadsheets()

    def get_values(self, spreadsheetId: str, range: str = ""):
        return (
            self.service.values()
            .get(spreadsheetId=spreadsheetId, range=range)
            .execute()["values"]
        )

    def get(self, spreadsheetId: str, ranges: Sequence[str] = [], fields: str = ""):
        return self.service.get(
            spreadsheetId=spreadsheetId, ranges=ranges, fields=fields
        ).execute()

    def get_row(self, cellRef: str) -> int:
        for i in range(len(cellRef)):
            try:
                return int(cellRef[i:])
            except ValueError:
                continue

        return -1

    def get_row_idx(self, cellRef: str) -> int:
        row = self.get_row(cellRef)
        if row == -1:
            return -1

        return row - 1

    def get_column(self, cellRef: str) -> str:
        row = self.get_row(cellRef)
        if row == -1:
            return cellRef

        return cellRef[: len(cellRef) - len(str(row))]

    def get_column_idx(self, cellRef: str) -> int:
        col = self.get_column(cellRef)
        ret = -1
        for i, c in enumerate(col[::-1]):
            cVal = ord(c) - ord("A") + 1
            ret += cVal * (26**i)

        return ret

    def color_to_hex(self, color: Mapping[str, int]) -> str:
        r, g, b = map(
            lambda colorComponent: round(color[colorComponent] * 255)
            if colorComponent in color
            else 0,
            ["red", "green", "blue"],
        )
        return f"{r:02x}{g:02x}{b:02x}"

    def is_white(self, color: Mapping[str, int]) -> bool:
        return self.color_to_hex(color).upper() == "FFFFFF"


class RateLimitedGoogleSheetsClient(GoogleSheetsClient):
    def __init__(self, googleCredentials: Mapping[str, str]) -> None:
        super().__init__(googleCredentials)

        self.bucket = BurstLimiter(
            rate=1, capacity=1, initialCapacity=60, storage=MemoryStorage()
        )

    @token_bucket("read", 1)
    def get_values(self, spreadsheetId: str, range: str = ""):
        return super().get_values(spreadsheetId, range)

    @token_bucket("read", 1)
    def get(self, spreadsheetId: str, ranges: Sequence[str] = [], fields: str = ""):
        return super().get(spreadsheetId, ranges, fields)
