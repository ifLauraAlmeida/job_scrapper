import os
from datetime import datetime
from methods.setup_logger import get_logger

logger = get_logger("utils")

class Utils:
    def __init__(self):
        pass
    
    def createDir(self, directory):
        # Trocamos os.path.exists + os.mkdir por os.makedirs
        # exist_ok=True: Se a pasta já existir, ele não faz nada (e não dá erro)
        try:
            if not os.path.exists(directory):
                os.makedirs(directory, exist_ok=True)
                logger.debug("Diretório criado (incluindo pais, se necessário): %s", directory)
        except Exception as e:
            logger.error("Falha ao criar diretório %s: %s", directory, e)
            
    def listDir(self, directory):
        try:
            if os.path.exists(directory):
                return os.listdir(directory)
            return []
        except Exception as e:
            logger.error("Falha ao listar diretório %s: %s", directory, e, exc_info=True)
            return []
    
    def loadFile(self, file_name_path):
        try:
            with open(file_name_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            logger.error("Falha ao ler o arquivo %s: %s", file_name_path, e, exc_info=True)
            return ""