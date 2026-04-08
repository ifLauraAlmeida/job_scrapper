import sys
import os
import json
from datetime import datetime

# 1. Configuração de Path para localizar o pacote 'methods'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from methods.transform import Transform
from methods.utils import Utils
from methods.setup_logger import get_logger

logger = get_logger("test_transform_engenha")
utils = Utils()
transformer = Transform()

def run_transform_test():
    # --- CAMINHOS ---
    # Onde o HTML está (Bronze)
    bronze_dir = "tests/lake/bronze/engenha/data_engineer"
    # Onde o JSON será salvo (Silver)
    silver_dir = "tests/lake/silver/engenha/data_engineer"
    
    # Garante que a pasta silver existe
    utils.createDir(silver_dir)

    try:
        # 2. Busca o arquivo mais recente na Bronze para testar
        arquivos = [f for f in os.listdir(bronze_dir) if f.endswith(".html")]
        if not arquivos:
            logger.error("Nenhum arquivo HTML encontrado em %s", bronze_dir)
            return
        
        # Ordena para pegar o último salvo
        ultimo_html = sorted(arquivos)[-1]
        path_input = os.path.join(bronze_dir, ultimo_html)
        
        logger.info("Lendo arquivo Bronze: %s", ultimo_html)
        
        with open(path_input, "r", encoding="utf-8") as f:
            html_content = f.read()

        # 3. Executa o Transform (Sua função getJobs)
        logger.info("Iniciando processamento via Transform.getJobs()")
        vagas_processadas = transformer.getJobs("engenha", html_content)

        if not vagas_processadas:
            logger.warning("O Transform retornou 0 vagas. Verifique o seletor 'vagas-container'.")
            return

        # 4. Salva o resultado em Silver (JSON)
        timestamp = datetime.now().strftime("%Y_%m_%d-%H_%M")
        path_output = os.path.join(silver_dir, f"{timestamp}.json")

        with open(path_output, "w", encoding="utf-8") as f:
            json.dump(vagas_processadas, f, indent=4, ensure_ascii=False)

        logger.info("Sucesso! %d vagas convertidas e salvas em: %s", len(vagas_processadas), path_output)
        
        # Print opcional do primeiro registro para conferência rápida
        print("\nExemplo da primeira vaga processada:")
        print(json.dumps(vagas_processadas[0], indent=2, ensure_ascii=False))

    except Exception as e:
        logger.error("Erro no teste de transformacao: %s", e, exc_info=True)

if __name__ == "__main__":
    run_transform_test()