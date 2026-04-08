import json
import os
import pandas as pd
from datetime import datetime
from endpoints import sources, queries
from methods.utils import Utils
from methods.extract import Extract
from methods.transform import Transform
from methods.cleaning import Cleaning
from methods.sheets import Sheets  # Novo Import
from methods.setup_logger import get_logger

# Instancia o logger do pipeline principal
logger = get_logger("app")

utils = Utils()
transform = Transform()
cleaner = Cleaning()

# --- Configurações ---
lake_root = "lake"
path_bronze = f"{lake_root}/bronze"
path_silver = f"{lake_root}/silver" 
path_gold = f"{lake_root}/gold"
PATH_GOLD_PARQUET = f"{path_gold}/vagas_consolidadas.parquet"

# Configurações do Google Sheets
GOOGLE_CREDENTIALS_FILE = "google_credentials.json"
GOOGLE_SHEETS_ID = "1xvuHa4a-vOTCQemrV9giBtAc2Z81rs96Dm87KsoLq1E"

today_str = datetime.now().strftime("%Y_%m_%d") 
timestamp = datetime.now().strftime("%Y_%m_%d-%H_%M")

# 1. Garante que as pastas raiz existam
for folder in [lake_root, path_bronze, path_silver, path_gold]:
    utils.createDir(folder)

needs_cleaning = False

# --- 2. LOOP DE PROCESSAMENTO ---
for site in sources.keys():
    if sources[site].get("active") == 1:
        
        extract = Extract(
            urls=sources, 
            date={"timestamp": timestamp}, 
            utils=utils, 
            path=path_bronze
        )

        for q in queries:
            q_folder = q.replace(" ", "_")
            bronze_dir = f"{path_bronze}/{site}/{q_folder}"
            silver_dir = f"{path_silver}/{site}/{q_folder}"
            
            utils.createDir(bronze_dir)
            utils.createDir(silver_dir)

            # --- VERIFICAÇÃO DE EXISTÊNCIA EM SILVER ---
            existing_files = utils.listDir(silver_dir)
            already_done = any(f.startswith(today_str) for f in existing_files)

            if already_done:
                logger.info("[-] Check: '%s' em '%s' já processado hoje.", q, site)
                needs_cleaning = True 
                continue 

            # --- 3. EXTRAÇÃO ---
            logger.info("[+] Coletando: %s | %s", site, q)
            extract.extractData(query=q, site_name=site)

            # --- 4. TRANSFORMAÇÃO IMEDIATA (SILVER) ---
            ext = "json" if "jobsapi" in sources[site]["url"] else "html"
            file_name = f"{timestamp}.{ext}"

            try:
                raw_path = f"{bronze_dir}/{file_name}"
                raw_content = utils.loadFile(raw_path)
                
                if not raw_content:
                    continue

                vagas_processadas = transform.getJobs(site, raw_content)

                if vagas_processadas:
                    silver_path = f"{silver_dir}/{timestamp}.json"
                    with open(silver_path, "w", encoding="utf-8") as f:
                        json.dump(vagas_processadas, f, ensure_ascii=False, indent=4)
                    
                    logger.info("    [OK] %d vagas em Silver.", len(vagas_processadas))
                    needs_cleaning = True
            except Exception as e:
                logger.error("    [Erro] Falha no processamento Silver: %s", e)

# --- 5. CONSOLIDAÇÃO GOLD ---
if needs_cleaning:
    logger.info(">>> Iniciando consolidação Gold (Deduplicação)...")
    cleaner.consolidate_gold(sources, queries)
else:
    logger.info(">>> Nenhuma extração nova hoje, mantendo Gold atual.")

# --- 6. SINCRONIZAÇÃO TOTAL COM GOOGLE SHEETS ---
try:
    logger.info(">>> Sincronizando Base Consolidada (Gold) com Google Sheets...")
    
    if os.path.exists(PATH_GOLD_PARQUET):
        # 1. Carrega os dados
        df_gold = pd.read_parquet(PATH_GOLD_PARQUET)
        
        # 2. TRATAMENTO CRUCIAL: O df_gold.fillna("") fica AQUI
        # Isso garante que campos vazios na Gold não quebrem o upload
        df_gold = df_gold.fillna("")
        
        # 3. Envio para o Sheets
        sheets = Sheets(GOOGLE_CREDENTIALS_FILE, GOOGLE_SHEETS_ID)
        
        # O overwrite agora chamará o novo método que usa worksheet.update()
        sheets.overwrite(df_gold, worksheet_index=0)
        
        logger.info(">>> Sucesso: Google Sheets atualizado com %d vagas.", len(df_gold))
    else:
        logger.error("ERRO: Arquivo Gold não encontrado em %s.", PATH_GOLD_PARQUET)

except Exception as e:
    logger.error("Falha crítica na sincronização com Sheets: %s", e, exc_info=True)