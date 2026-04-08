import os
import sys
import pandas as pd
from datetime import datetime

# Adiciona a raiz do projeto ao path para encontrar o pacote 'methods'
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from methods.sheets import Sheets
from methods.setup_logger import get_logger

# Configuração de Logs
logger = get_logger("gold_to_sheets")

# --- Configurações ---
GOOGLE_CREDENTIALS_FILE = "google_credentials.json"
GOOGLE_SHEETS_ID = "1xvuHa4a-vOTCQemrV9giBtAc2Z81rs96Dm87KsoLq1E"
PATH_GOLD_PARQUET = "lake/gold/vagas_consolidadas.parquet"

def sync_gold_to_sheets():
    try:
        # 1. Carrega os dados da Camada Gold
        if not os.path.exists(PATH_GOLD_PARQUET):
            logger.error("Arquivo Gold nao encontrado em: %s", PATH_GOLD_PARQUET)
            return

        logger.info("Lendo dados da camada Gold...")
        df_gold = pd.read_parquet(PATH_GOLD_PARQUET)

        # 2. Tratamento opcional: Google Sheets nao lida bem com NaN/Null
        # Vamos substituir valores nulos por strings vazias para evitar erros no gspread
        df_gold = df_gold.fillna("")

        # 3. Conexao com a Planilha
        sheets = Sheets(GOOGLE_CREDENTIALS_FILE, GOOGLE_SHEETS_ID)
        
        # 4. Envio dos dados (Overwrite para manter a planilha sempre atualizada com o consolidado)
        logger.info("Enviando %d registros para o Google Sheets...", len(df_gold))
        
        # Usando index=0 conforme o ID que voce passou (gid=0)
        sheets.overwrite(df_gold, worksheet_index=0)
        
        logger.info("Sucesso: Planilha atualizada com os dados da Camada Gold.")

    except Exception as e:
        logger.error("Falha ao sincronizar Gold com Sheets: %s", e, exc_info=True)

if __name__ == "__main__":
    sync_gold_to_sheets()