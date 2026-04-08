import json
import re
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from methods.setup_logger import get_logger

logger = get_logger("transform")

class Transform:
    def __init__(self):
        pass
    
    def soupHtml(self, html_text):
        return BeautifulSoup(html_text, "html.parser") if html_text else None
    
    def getJobs(self, site_source, raw_content):
        """
        Recebe o conteúdo bruto e direciona para o extrator específico.
        """
        if not raw_content or len(raw_content.strip()) == 0:
            return []

        match site_source:
            case "workingnomads":
                return self.handleWorkingNomads(raw_content)
            case "engenha":
                soup = self.soupHtml(raw_content)
                return self.handleEngenha(soup)
            case _:
                return []
            
    def handleWorkingNomads(self, json_data):
        """Trata o JSON bruto da API do WorkingNomads"""
        jobs_processed = []
        try:
            # Garante que temos um dicionário
            data = json.loads(json_data) if isinstance(json_data, str) else json_data
            
            # No seu exemplo, as vagas ficam em hits -> hits
            items = data.get('hits', {}).get('hits', [])
            
            for item in items:
                source = item.get('_source', {})
                
                # --- LÓGICA DE LOCALIZAÇÃO E REMOTO ---
                # No WorkingNomads, quase tudo é remoto, mas vamos validar:
                locations = source.get("locations", [])
                location_str = ", ".join(locations) if locations else "Global"
                
                # Distinguir se é 100% remoto ou tem restrição
                # O campo 'description' ou as tags costumam indicar isso
                tipo_vaga = "Remoto" # Default para WorkingNomads
                if "100% Remote" in source.get("description", ""):
                    tipo_vaga = "Remoto (100%)"
                
                # --- DATA DE PUBLICAÇÃO ---
                # A API traz 'pub_date' (ex: 2026-03-07T09:33...)
                # Vamos converter para o seu formato padrão AAAA-MM-DD
                raw_date = source.get("pub_date", "")
                date_published = raw_date.split("T")[0] if raw_date else "N/A"

                jobs_processed.append({
                    "hash_id": str(source.get("id", item.get("_id"))),
                    "title": source.get("title", "N/A"),
                    "company": source.get("company", "N/A"),
                    "location": location_str,
                    "tipo_vaga": tipo_vaga,
                    "date_published": date_published,
                    "url": source.get("apply_url") or f"https://www.workingnomads.com/jobs/{source.get('id')}",
                    "site_source": "workingnomads"
                })
            
            logger.info("WorkingNomads: %d vagas processadas.", len(jobs_processed))
        except Exception as e:
            logger.error("Erro no Transform WorkingNomads: %s", e, exc_info=True)
        return jobs_processed

    def handleEngenha(self, soup):
        """Trata o HTML do Engenha com cálculo de data de lançamento"""
        jobs_processed = []
        container = soup.find(id="vagas-container")
        now = datetime.now() # Data de referência do PC
    
        if container:
            vagas_listadas = container.find_all(class_="vaga-item")

            for vaga in vagas_listadas:
                # 1. Título e URL
                title_tag = vaga.find("h2", class_="vaga-titulo")
                link_tag = title_tag.find("a") if title_tag else None
                if not link_tag: continue

                # 2. ID e Empresa (Mantendo sua lógica de sucesso)
                url = link_tag["href"]
                match_id = re.search(r'/vagas/([^/]+)/', url)
                vaga_id = match_id.group(1) if match_id else "id_nao_encontrado"
                
                empresa_tag = vaga.find("span", class_="vaga-label-empresa")
                empresa = empresa_tag.get_text(strip=True) if empresa_tag else "Não informada"

                # 3. Lógica de Data de Lançamento (O "pulo do gato")
                # Buscamos o small que contém o ícone de relógio
                data_postagem_txt = "N/A"
                data_lancamento = now.strftime("%Y-%m-%d") # Default é hoje
                
                # Procuramos a tag que contém o texto de tempo (ex: "1 mês", "2 semanas")
                time_tag = vaga.find("small")
                if time_tag:
                    raw_time = time_tag.get_text(strip=True).lower()
                    # Regex para pegar o número (ex: '1', '2') e a unidade ('mês', 'semana', 'dia')
                    match_time = re.search(r'(\d+)\s*(mes|mês|semana|dia|hora|minuto)', raw_time)
                    
                    if match_time:
                        quantidade = int(match_time.group(1))
                        unidade = match_time.group(2)
                        
                        # Cálculo de subtração
                        if "mes" in unidade:
                            delta = timedelta(days=quantidade * 30)
                        elif "semana" in unidade:
                            delta = timedelta(weeks=quantidade)
                        elif "dia" in unidade:
                            delta = timedelta(days=quantidade)
                        else:
                            delta = timedelta(days=0) # Horas/Minutos consideramos hoje
                        
                        data_calculada = now - delta
                        data_lancamento = data_calculada.strftime("%Y-%m-%d")
                        data_postagem_txt = raw_time

                # 4. Localização e Tipo (Sua lógica de labels)
                labels = vaga.find_all("span", class_="vaga-label")
                location, tipo_vaga = "Brasil", "Presencial"
                for label in labels:
                    txt = label.get_text(strip=True)
                    if "," in txt or re.search(r'[A-Z]{2}$', txt):
                        location = txt
                    elif txt.lower() in ["remoto", "híbrido", "hibrido", "presencial"]:
                        tipo_vaga = txt

                jobs_processed.append({
                    "hash_id": vaga_id,
                    "title": link_tag.get_text(strip=True),
                    "company": empresa,
                    "location": location,
                    "tipo_vaga": tipo_vaga,
                    "date_posted_text": data_postagem_txt, # Texto original (ex: 1 mês)
                    "date_published": data_lancamento,     # Data calculada (ex: 2026-03-06)
                    "url": url,
                    "site_source": "engenha"
                })
                
        logger.info("Engenha: %d vagas processadas com datas calculadas.", len(jobs_processed))
        return jobs_processed