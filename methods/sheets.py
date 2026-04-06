import gspread
import pandas as pd
from oauth2client.service_account import ServiceAccountCredentials

from methods.setup_logger import get_logger

logger = get_logger("sheets")

SCOPE = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive",
]


class Sheets:
    def __init__(self, credentials_file: str, spreadsheet_id: str):
        self.spreadsheet_id = spreadsheet_id
        creds = ServiceAccountCredentials.from_json_keyfile_name(
            credentials_file, SCOPE
        )
        self.client = gspread.authorize(creds)
        logger.info("Autenticação com Google Sheets realizada com sucesso.")

    def get_worksheet(self, index: int = 0):
        worksheet = self.client.open_by_key(self.spreadsheet_id).get_worksheet(index)
        logger.debug("Aba %d acessada.", index)
        return worksheet

    def read(self, worksheet_index: int = 0) -> pd.DataFrame:
        worksheet = self.get_worksheet(worksheet_index)
        records = worksheet.get_all_records()
        df = pd.DataFrame(records)
        logger.info("Aba %d lida: %d registros.", worksheet_index, len(df))
        return df

    def append(self, df: pd.DataFrame, worksheet_index: int = 0):
        worksheet = self.get_worksheet(worksheet_index)
        for _, row in df.iterrows():
            worksheet.append_row(row.tolist())
        logger.info("%d linha(s) adicionada(s) na aba %d.", len(df), worksheet_index)

    def clear(self, worksheet_index: int = 0):
        worksheet = self.get_worksheet(worksheet_index)
        worksheet.clear()
        logger.info("Aba %d limpa.", worksheet_index)

    def overwrite(self, df: pd.DataFrame, worksheet_index: int = 0):
        self.clear(worksheet_index)
        worksheet = self.get_worksheet(worksheet_index)
        worksheet.append_row(df.columns.tolist())
        for _, row in df.iterrows():
            worksheet.append_row(row.tolist())
        logger.info("Aba %d sobrescrita com %d registro(s).", worksheet_index, len(df))

    def list_worksheets(self):
        spreadsheet = self.client.open_by_key(self.spreadsheet_id)
        worksheets = spreadsheet.worksheets()
        titles = [ws.title for ws in worksheets]
        logger.info("Planilhas disponíveis: %s", titles)
        return titles
