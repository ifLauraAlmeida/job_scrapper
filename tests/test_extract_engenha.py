import sys
import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from dotenv import load_dotenv

# 1. Configuração de Path e Variáveis de Ambiente
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
load_dotenv() # Carrega o .env

from methods.setup_logger import get_logger
from methods.utils import Utils

logger = get_logger("test_extract_auth")
utils = Utils()

def extract_with_auth(query_url):
    """Extrai HTML usando credenciais do ambiente"""
    email = os.getenv("ENGENHA_EMAIL")
    password = os.getenv("ENGENHA_PASSWORD")
    login_url = "https://engenha.com/login"
    
    if not email or not password:
        logger.error("Credenciais não encontradas no arquivo .env")
        return None

    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (X11; Fedora; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    })

    try:
        # Passo 1: Captura do Token CSRF (Necessário em sites Laravel)
        logger.info("Capturando CSRF token...")
        response_get = session.get(login_url, timeout=15)
        soup = BeautifulSoup(response_get.text, "html.parser")
        
        token_input = soup.find("input", {"name": "_token"})
        if not token_input:
            logger.error("Não foi possível encontrar o _token no HTML.")
            return None
        
        csrf_token = token_input["value"]

        # Passo 2: Login (POST) - Simulando o comportamento do navegador
        payload = {
            "_token": csrf_token, 
            "email": email, 
            "password": password
        }
        
        logger.info("Realizando login para: %s", email)
        # O allow_redirects=True segue o status 302 automaticamente
        response_post = session.post(login_url, data=payload, allow_redirects=True)

        # Verificação: Se após o login a URL mudou (não estamos mais no /login), deu certo
        if response_post.status_code == 200 and login_url not in response_post.url:
            logger.info("Login realizado. Acessando: %s", query_url)
            
            # Passo 3: Coleta dos dados logados
            jobs_response = session.get(query_url, timeout=15)
            return jobs_response.text
        else:
            logger.error("Falha na autenticação. Verifique e-mail e senha no .env")
            return None

    except Exception as e:
        logger.error("Erro durante a extração: %s", e, exc_info=True)
        return None

if __name__ == "__main__":
    # Configuração da busca
    QUERY_URL = "https://engenha.com/vagas?q=data+engineer"
    DIR_PATH = "tests/lake/bronze/engenha/data_engineer"
    
    # Garante a estrutura de pastas (usando seu utils.py com makedirs)
    utils.createDir(DIR_PATH)
    
    timestamp = datetime.now().strftime("%Y_%m_%d-%H_%M")
    file_path = os.path.join(DIR_PATH, f"{timestamp}.html")

    # Execução
    html_content = extract_with_auth(QUERY_URL)

    if html_content:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(html_content)
        logger.info("Sucesso! HTML salvo em: %s", file_path)
    else:
        logger.warning("A extração falhou. Verifique os logs acima.")