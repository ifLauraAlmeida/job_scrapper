import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime

import pandas as pd

from methods.sheets import Sheets

GOOGLE_CREDENTIALS_FILE = "google_credentials.json"
GOOGLE_SHEETS_ID = "1H3O-8epWYwcxJTiKdD-PkvCRLnVI8tnsD2XeslxD-es"

now = datetime.now().strftime("%Y-%m-%d %H:%M")

sheets = Sheets(GOOGLE_CREDENTIALS_FILE, GOOGLE_SHEETS_ID)

# ── ABA 1: ler, printar e adicionar um registro ─────────────────────────────

print("=== ABA 1 — Dados atuais ===")
df_aba1 = sheets.read(worksheet_index=1)
print(df_aba1)
print()

novo_registro_aba1 = pd.DataFrame(
    [[now, "Engenheiro de Dados Jr", "https://example.com/vaga1"]],
    columns=["Timestamp", "Titulo", "Link"],
)

sheets.append(novo_registro_aba1, worksheet_index=1)
print("Registro adicionado na aba 1:")
print(novo_registro_aba1)
print()

# ── ABA 2: ler, printar, limpar e popular ────────────────────────────────────

print("=== ABA 2 — Dados atuais ===")
df_aba2 = sheets.read(worksheet_index=2)
print(df_aba2)
print()

novos_registros_aba2 = pd.DataFrame(
    [
        [now, "Analista de Dados Pleno", "https://example.com/vaga2"],
        [now, "Cientista de Dados Sr", "https://example.com/vaga3"],
        [now, "Engenheiro de Machine Learning", "https://example.com/vaga4"],
        [now, "Arquiteto de Dados", "https://example.com/vaga5"],
    ],
    columns=["Timestamp", "Titulo", "Link"],
)

sheets.overwrite(novos_registros_aba2, worksheet_index=2)
print("Aba 2 repopulada com:")
print(novos_registros_aba2)
