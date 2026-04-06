import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd

GOOGLE_CREDENTIALS_FILE = "google_credentials.json"
GOOGLE_SHEETS_ID = "1H3O-8epWYwcxJTiKdD-PkvCRLnVI8tnsD2XeslxD-es"


def visualizar_planilhas_disponiveis():
    # Define o escopo da aplicação
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive",
    ]

    # Carrega as credenciais do arquivo JSON
    creds = ServiceAccountCredentials.from_json_keyfile_name(
        GOOGLE_CREDENTIALS_FILE, scope
    )

    # Autoriza o cliente
    client = gspread.authorize(creds)

    # Lista as planilhas disponíveis
    planilhas = client.openall()
    for planilha in planilhas:
        print(f"Título: {planilha.title}, ID: {planilha.id}")


def conectar_planilha(planilha_id, aba=0):
    # Define o escopo da aplicação
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive",
    ]

    # Carrega as credenciais do arquivo JSON
    creds = ServiceAccountCredentials.from_json_keyfile_name(
        GOOGLE_CREDENTIALS_FILE, scope
    )

    # Autoriza o cliente
    client = gspread.authorize(creds)

    # Abre a planilha pelo ID
    return client.open_by_key(planilha_id).get_worksheet(aba)


def ler_dados(aba) -> pd.DataFrame | None:
    # Retorna todos os registros como um dataframe pandas
    return pd.DataFrame(aba.get_all_records())


def escrever_dados(aba, df: pd.DataFrame):
    # Adiciona uma nova linha ao final da planilha
    for _, row in df.iterrows():
        aba.append_row(row.tolist())


# Exemplo de uso
if __name__ == "__main__":
    try:
        # 0. Visualizar planilhas disponíveis
        # print("Planilhas disponíveis:")
        # visualizar_planilhas_disponiveis()

        # 1. Conectar
        minha_aba = conectar_planilha(GOOGLE_SHEETS_ID, aba=1)

        # 3. Ler
        dados = ler_dados(minha_aba)
        print("Dados atuais na planilha:")
        print(dados)


        # 2. Escrever
        novo_registro = pd.DataFrame([["Monitor Gamer Samsung", "400", "https://example.com/monitor-samsung"]])
        escrever_dados(minha_aba, novo_registro)
        print("Dados gravados com sucesso!")


    except Exception as e:
        print(f"Erro: {e}")
