import requests

def listar_vagas_gupy(api_key):
    url = "https://gupy.io"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Verifica se a requisição foi bem-sucedida
        
        data = response.json()
        
        # A resposta contém uma lista de vagas em 'results'
        for vaga in data.get('results', []):
            print(f"Vaga: {vaga['name']} - ID: {vaga['id']} - Empresa: {vaga['companyName']}")
            
    except requests.exceptions.RequestException as e:
        print(f"Erro na requisição: {e}")

# Substitua pela sua chave API real
# api_key = "SEU_TOKEN_AQUI"
# listar_vagas_gupy(api_key)
