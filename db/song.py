from collections.abc import Mapping
from datetime import timedelta
from typing import Optional, Any

from ..models import *
from ..sheets import GoogleSheetsClient, RateLimitedGoogleSheetsClient

class SongTemplateDB:
    TEMPLATE_SHEET_NAME = 'Template'

    def __init__(self, googleCredentials: Mapping[str, str], client: Optional[GoogleSheetsClient] = None) -> None:
        if client is not None:
            self.sheetsClient = client
        else:
            self.sheetsClient = RateLimitedGoogleSheetsClient(googleCredentials)

    def get_format_map(self, spreadsheetId: str) -> Mapping[str, Any]:
        rootPos = 'I1'
        rootPosRow = self.sheetsClient.get_row('I1') + 1

        resp = self.sheetsClient.get(
            spreadsheetId,
            ranges=f'{SongTemplateDB.TEMPLATE_SHEET_NAME}!{rootPos}:{rootPosRow}',
            fields='sheets.data.rowData.values(userEnteredValue,userEnteredFormat(backgroundColor,textFormat.foregroundColor))'
        )

        return {
            resp['sheets'][0]['data'][0]['rowData'][1]['values'][i-1]['userEnteredValue']['stringValue']: v['userEnteredFormat']
            for i, v in enumerate(resp['sheets'][0]['data'][0]['rowData'][0]['values'])
            if 'userEnteredFormat' in v and 'userEnteredValue' in v and not self.sheetsClient.is_white(v['userEnteredFormat']['backgroundColor'])
        }

class SongDB:
    def __init__(self, googleCredentials: Mapping[str, str], client: Optional[GoogleSheetsClient] = None) -> None:
        if client is not None:
            self.sheetsClient = client
        else:
            self.sheetsClient = RateLimitedGoogleSheetsClient(googleCredentials)

        self.songTemplateDB = SongTemplateDB(googleCredentials, self.sheetsClient)

    def scan_song(self, spreadsheetId: str, songName: str) -> models.Song:
        return models.Song(
            title=self.get_title(spreadsheetId, songName),
            creators=self.get_creators(spreadsheetId, songName),
            lyrics=self.get_lyrics(spreadsheetId, songName),
        )

    def get_title(self, spreadsheetId: str, songName: str) -> models.SongTitle:
        result = self.sheetsClient.get_values(spreadsheetId, f'{songName}!B1:B2')

        ret = models.SongTitle(
            romaji=result[0][0]
        )

        if len(result) > 1:
            ret.en = result[1][0]

        return ret

    def get_creators(self, spreadsheetId: str, songName: str) -> models.SongCreators:
        result = self.sheetsClient.get_values(spreadsheetId, f'{songName}!E1:E4')

        return models.SongCreators(
            artist=result[0][0],
            composers=[composer.strip() for composer in result[1][0].split(',')],
            arrangers=[composer.strip() for composer in result[2][0].split(',')],
            writers=[composer.strip() for composer in result[3][0].split(',')],
        )

    def get_lyrics(self, spreadsheetId: str, songName: str) -> list[models.SongLine]:
        rootPos = 'A6'
        rootPosRow = self.sheetsClient.get_row(rootPos)
        rootPosCol = self.sheetsClient.get_column(rootPos)

        enLines = self.sheetsClient.get_values(spreadsheetId, f'{songName}!B{rootPosRow}:B')

        result = self.sheetsClient.get(
            spreadsheetId,
            ranges=[f'{songName}!{rootPosCol}{rootPosRow}:{rootPosRow + len(enLines) - 1}'],
            fields='sheets.data.rowData.values(formattedValue,effectiveFormat.backgroundColor)'
        )

        colorToActorMap = {
            self.sheetsClient.color_to_hex(format['backgroundColor']): actor
            for actor, format in self.songTemplateDB.get_format_map(spreadsheetId).items()
        }
        return [
            self._parse_line(line, colorToActorMap)
            for line in result['sheets'][0]['data'][0]['rowData']
            if 'formattedValue' in line['values'][1]
        ]

    def _parse_line(self, rowData: Mapping[str, Any], colorToActorMap: Mapping[str, str]) -> models.SongLine:
        values = rowData['values']
        timeAndSyllables = [syllable for syllable in values[self.sheetsClient.get_column_idx('I'):] if 'formattedValue' in syllable]

        syllables: list[models.SongLineSyllable] = []
        actors: list[str] = []
        breakpoints: list[int] = []

        timeAndSyllablesIter = iter(timeAndSyllables)
        for i, (val1, val2) in enumerate(zip(timeAndSyllablesIter, timeAndSyllablesIter)):
            syllables.append(models.SongLineSyllable(
                timedelta(milliseconds=int(val1['formattedValue'])*10),
                val2['formattedValue']
            ))

            currActor = colorToActorMap[self.sheetsClient.color_to_hex(val2['effectiveFormat']['backgroundColor'])]
            if not actors or currActor != actors[-1]:
                actors.append(currActor)
                breakpoints.append(i)

        return models.SongLine(
            en=values[self.sheetsClient.get_column_idx('B')]['formattedValue'],
            karaokeEffect=values[self.sheetsClient.get_column_idx('D')].get('formattedValue'),
            isSecondary='formattedValue' in values[self.sheetsClient.get_column_idx('F')],
            start=self._parse_timedelta(values[self.sheetsClient.get_column_idx('G')]['formattedValue']),
            end=self._parse_timedelta(values[self.sheetsClient.get_column_idx('H')]['formattedValue']),
            syllables=syllables,
            actors=actors,
            breakpoints=breakpoints,
        )

    def _parse_timedelta(self, tdStr: str) -> timedelta:
        sStr, _, csStr = tdStr.partition(".")
        hrs, mins, secs = map(int, sStr.split(":"))
        cs = int(csStr)

        return timedelta(hours=hrs, minutes=mins, seconds=secs, milliseconds=cs*10)
