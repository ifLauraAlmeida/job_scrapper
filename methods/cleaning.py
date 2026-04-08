import os
import json
import pandas as pd
from datetime import datetime
from methods.setup_logger import get_logger

# Instancia o logger para a camada de limpeza
logger = get_logger("cleaning")

class Cleaning:
    def __init__(self, lake_path="lake"):
        self.lake_path = lake_path
        self.silver_path = os.path.join(lake_path, "silver")
        self.gold_path = os.path.join(lake_path, "gold")
        
    def consolidate_gold(self, sources, queries):
        """
        Consolida arquivos JSON da Silver em um dataset único (CSV/Parquet) na Gold,
        removendo duplicatas baseadas no hash_id.
        """
        all_jobs = []
        seen_ids = set()
        total_files_processed = 0

        logger.info("Iniciando processo de consolidacao: Silver -> Gold")

        # Navegação estruturada: Site -> Query
        for site in sources.keys():
            site_path = os.path.join(self.silver_path, site)
            if not os.path.exists(site_path):
                logger.debug("Diretorio de site nao encontrado na Silver: %s", site)
                continue

            for q in queries:
                q_folder = q.replace(" ", "_")
                folder_path = os.path.join(site_path, q_folder)
                
                if not os.path.exists(folder_path):
                    continue

                # Coleta de arquivos JSON processados
                try:
                    files = [f for f in os.listdir(folder_path) if f.endswith('.json')]
                except Exception as e:
                    logger.error("Falha ao listar diretorio %s: %s", folder_path, e)
                    continue
                
                for file in files:
                    file_path = os.path.join(folder_path, file)
                    total_files_processed += 1
                    
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            jobs_list = json.load(f)
                            
                        for job in jobs_list:
                            hid = job.get("hash_id")
                            
                            # Validação de Unicidade
                            if hid and hid not in seen_ids:
                                job["extracted_query"] = q 
                                job["extraction_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                all_jobs.append(job)
                                seen_ids.add(hid)
                            else:
                                logger.debug("Hash duplicado ignorado: %s", hid)
                                
                    except Exception as e:
                        logger.error("Erro na leitura do arquivo %s: %s", file_path, e)

        if not all_jobs:
            logger.warning("Nenhum registro unico encontrado para consolidacao.")
            return

        # Persistência dos Dados
        try:
            df = pd.DataFrame(all_jobs)
            
            if not os.path.exists(self.gold_path):
                os.makedirs(self.gold_path)
                logger.info("Diretorio Gold criado: %s", self.gold_path)

            # Exportação CSV
            csv_file = os.path.join(self.gold_path, "vagas_consolidadas.csv")
            df.to_csv(csv_file, index=False, encoding='utf-8-sig')
            
            # Exportação Parquet
            parquet_file = os.path.join(self.gold_path, "vagas_consolidadas.parquet")
            df.to_parquet(parquet_file, index=False)

            logger.info("Sucesso: Gold atualizada. Arquivos processados: %d | Registros unicos: %d", 
                        total_files_processed, len(df))
            
        except Exception as e:
            logger.error("Falha ao persistir dados na camada Gold: %s", e, exc_info=True)

        return df