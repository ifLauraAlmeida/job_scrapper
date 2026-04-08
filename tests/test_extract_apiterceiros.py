import sys
import os

# Adiciona a raiz do projeto ao path do Python
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import requests
from endpoints import queries # Agora ele vai encontrar
from methods.setup_logger import get_logger

# Instancia o logger com o nome do módulo
logger = get_logger("extract_theirstack")

# Configurações de Autenticação
API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ2ZXIiOjEsImp0aSI6IjE0MmQwN2E0LWUwNWEtNDY0Yi04NGI1LWE3YTExZjI0ODk0MiIsImNyZWF0ZWRfYnkiOjE1NTM5MCwicGVybWlzc2lvbnMiOltdLCJhdWQiOiJhcGkiLCJpYXQiOjE3NzUzMjE4NjksInN1YiI6IjE1NDczNiIsIm5hbWUiOiJEUFQiLCJlbWFpbCI6ImxhdXJhYWxtZWlkYWpvYkBnbWFpbC5jb20ifQ.UydfgtxspT_Z3_VziFa-1AQeOfGUliXTcOSoN9VEMic"
URL = "https://api.theirstack.com/v1/jobs/search"

headers = {
    "Accept": "application/json",
    "Content-Type": "application/json",
    "Authorization": f"Bearer {API_KEY}"
}

def fetch_theirstack_jobs():
    logger.info("Iniciando busca de vagas na TheirStack API")
    
    # Usando a lista de queries que você já definiu nos endpoints
    # Limitando para as primeiras para teste, ou percorrendo todas
    data = {
        "order_by": [{"desc": True, "field": "date_posted"}],
        "page": 0,
        "limit": 20,
        "posted_at_max_age_days": 30,
        "job_country_code_or": ["BR"],
        "job_title_or": list(queries), # <--- ADICIONE O list() AQUI
    }

    try:
        response = requests.post(URL, headers=headers, json=data, timeout=30)
        response.raise_for_status()
        
        json_data = response.json()
        
        # Normalização da resposta da API
        if isinstance(json_data, dict):
            vagas = json_data.get('data', [])
        elif isinstance(json_data, list):
            vagas = json_data
        else:
            vagas = []

        if not vagas:
            logger.warning("Nenhuma vaga encontrada para as queries fornecidas.")
            return

        logger.info("Sucesso: %d vagas encontradas.", len(vagas))

        print("\n" + "="*60)
        print(f"RELATÓRIO DE VAGAS - THEIRSTACK - {len(vagas)} RESULTADOS")
        print("="*60 + "\n")

        for vaga in vagas:
            if not isinstance(vaga, dict):
                continue
            
            # Extração padronizada
            titulo = vaga.get('job_title', 'N/A')
            link = vaga.get('url', 'N/A')
            data_postagem = vaga.get('date_posted', 'N/A')
            empresa = vaga.get('company', "N/A")
            localizacao = vaga.get('job_location') or vaga.get('location') or "Brasil (Remote/Hybrid)"

            # Print formatado para visualização rápida (sem salvar em arquivo)
            print(f"TITULO: {titulo}")
            print(f"EMPRESA: {empresa}")
            print(f"LOCAL: {localizacao}")
            print(f"POSTAGEM: {data_postagem}")
            print(f"URL: {link}")
            print("-" * 30)

    except requests.exceptions.HTTPError as http_err:
        logger.error("Erro HTTP na TheirStack: %s", http_err)
        if hasattr(response, 'text'):
            logger.debug("Resposta bruta do erro: %s", response.text[:200])
    except Exception as e:
        logger.error("Erro inesperado na extração TheirStack: %s", e, exc_info=True)

if __name__ == "__main__":
    fetch_theirstack_jobs()