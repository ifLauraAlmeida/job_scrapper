import requests
import json
import os
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from urllib.parse import quote  # <--- ADICIONE ESTE IMPORT
from methods.setup_logger import get_logger

load_dotenv()
logger = get_logger("extract")

class Extract:
    def __init__(self, urls, date, utils, path="bronze"):
        self.urls = urls
        self.path = path
        self.timestamp = date.get("timestamp")
        self.utils = utils
        self.session = requests.Session()
        self.logged_in_sites = [] 
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (X11; Fedora; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        })

    def _login_engenha(self):
        """Realiza o login apenas uma vez por execução do pipeline"""
        if "engenha" in self.logged_in_sites:
            return True

        email = os.getenv("ENGENHA_EMAIL")
        password = os.getenv("ENGENHA_PASSWORD")
        login_url = "https://engenha.com/login"

        try:
            logger.info("Tentando login único no Engenha.com...")
            res = self.session.get(login_url, timeout=15)
            soup = BeautifulSoup(res.text, "html.parser")
            
            token_element = soup.find("input", {"name": "_token"})
            if not token_element:
                logger.error("Token CSRF não encontrado.")
                return False

            token = token_element["value"]
            payload = {"_token": token, "email": email, "password": password}
            
            login_res = self.session.post(login_url, data=payload, allow_redirects=True)

            if login_res.status_code == 200 and login_url not in login_res.url:
                logger.info("Login realizado com sucesso!")
                self.logged_in_sites.append("engenha")
                return True
            
            return False
        except Exception as e:
            logger.error("Erro no login: %s", e)
            return False

    def _handle_api(self, endpoint, save_path):
        payload = {"query": {"match_all": {}}, "size": 50}
        try:
            response = self.session.post(endpoint, json=payload)
            response.raise_for_status()
            final_path = save_path if save_path.endswith(".json") else save_path.replace(".html", ".json")
            with open(final_path, "w", encoding="utf-8") as f:
                json.dump(response.json(), f, ensure_ascii=False, indent=4)
            logger.info("JSON salvo: %s", final_path)
        except Exception as e:
            logger.error("Erro na API: %s", e)

    def _handle_html(self, endpoint, save_path, site_name):
        try:
            if site_name == "engenha":
                if not self._login_engenha():
                    return

            # A URL aqui já chegará codificada corretamente pelo extractData
            response = self.session.get(endpoint, timeout=15)
            response.raise_for_status() # Lança erro se for 404, 500, etc.
            
            if len(response.text) < 1000:
                logger.warning("HTML muito curto. Possível bloqueio ou página vazia.")

            with open(save_path, "w", encoding="utf-8") as f:
                f.write(response.text)
            logger.info("HTML salvo: %s", save_path)
            
        except Exception as e:
            # Se der erro 404, ele cai aqui e NÃO salva o arquivo, 
            # evitando que o app.py tente ler algo que não existe.
            logger.error("Erro ao baixar HTML: %s | URL: %s", e, endpoint)
            
    def extractData(self, query, site_name):
        data = self.urls.get(site_name)
        if not data or data.get("active") != 1: return
        
        query_folder = query.replace(" ", "_")
        is_api = "jobsapi" in data["url"]
        ext = "json" if is_api else "html"
        
        full_dir = f"{self.path}/{site_name}/{query_folder}"
        self.utils.createDir(full_dir)
        file_path = f"{full_dir}/{self.timestamp}.{ext}"

        if is_api:
            self._handle_api(data["url"], file_path)
        else:
            # --- MUDANÇA ESSENCIAL AQUI ---
            # quote(query) transforma "analista de dados" em "analista%20de%20dados"
            # Isso é MUITO mais seguro que o .replace(' ', '+')
            query_safe = quote(query)
            endpoint = f"{data['url']}{query_safe}"
            
            self._handle_html(endpoint, file_path, site_name)