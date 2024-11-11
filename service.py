import pandas as pd
import ollama
from model.usuario import user
import re
import requests
import csv
import json
def parse_string_to_json(input_string):
    try:
        # Divida a string nas linhas
        lines = input_string.strip().split("\n")
        
        # Verifique se há 4 linhas (nome, vaga, experiencia, formação)
        if len(lines) != 4:
            raise ValueError("A string não contém 4 campos esperados (nome, vaga, experiencia, formação).")
        
        # Crie um dicionário com as chaves apropriadas
        parsed_data = {
            "nome": lines[0].strip(),
            "vaga": lines[1].strip(),
            "experiencia": lines[2].strip(),
            "formacao": lines[3].strip()
        }
        
        # Retorne o JSON (em formato de dicionário)
        return json.dumps(parsed_data, ensure_ascii=False)
    
    except Exception as e:
        return str(e)




categories = {
    "não recomendo fortemente": -10,
    "não recomendo": -5,
    "neutro": 0,
    "recomendo": 5,
    "recomendo fortemente": 10
}

# Function to select the user based on CPF from the CSV
def select(cpf):
    # Read the CSV file
    df = pd.read_csv("DB.csv")
    
    # Find the row containing the given CPF
    user_row = df[df['cpf'] == cpf]
    
    # Check if a user was found
    if not user_row.empty:
        # Extract the values from the found row
        name = user_row.iloc[0]['name']
        role = user_row.iloc[0]['role']
        experiences = user_row.iloc[0]['experiences']
        degree = user_row.iloc[0]['degree']
        exigences = user_row.iloc[0]['exigences']
        score = user_row.iloc[0]['score'].astype(int)
        score = int(score)
        # Convert experiences and exigences from string to list
        if isinstance(experiences, str):
            experiences = experiences.split(',')
        if isinstance(exigences, str):
            exigences = exigences.split(',')
            
        # Create and return the user object with the extracted data
        return user(name=name, cpf=cpf, role=role, experiences=experiences, degree=degree, exigences=exigences, score=score)
    
    # Return None if no user is found
    return None    

def update(usuario):
    # Lê o arquivo CSV e armazena o conteúdo em uma lista
    usuarios = []
    usuario_atualizado = False
    
    # Carrega todos os dados do CSV e procura o usuário a ser atualizado
    with open("DB.csv", mode='r', newline='', encoding='utf-8') as csvfile:
        leitor = csv.DictReader(csvfile)
        for linha in leitor:
            if linha['cpf'] == usuario.cpf:
                # Atualiza a linha com os dados do usuário fornecido
                linha.update(usuario.to_dict())
                usuario_atualizado = True
            usuarios.append(linha)
    
    # Verifica se o usuário foi encontrado e atualizado
    if not usuario_atualizado:
        print("Usuário não encontrado no arquivo CSV.")
        return False

    # Escreve os dados atualizados de volta ao CSV
    with open("DB.csv", mode='w', newline='', encoding='utf-8') as csvfile:
        campos = ["name", "cpf", "role", "experiences", "degree", "exigences", "score"]
        escritor = csv.DictWriter(csvfile, fieldnames=campos)
        escritor.writeheader()
        escritor.writerows(usuarios)

    print("Usuário atualizado com sucesso.")
    return True


# Function for the first phase of the interview process
def fase1(usuario):
    
    usuario_json = usuario.to_json()
    # Construct the prompt for the model
    prompt = f"""
    Aqui estão as informações sobre o candidato:
        {usuario_json}
        
        Pode me recomendar o usuário com base nas suas habilidades e experiências para um possível cargo de {usuario.role}? As exigências do cargo são: {usuario.exigences}
        Sua resposta deve conter apenas: 'não recomendo fortemente', 'não recomendo', 'neutro', 'recomendo' ou 'recomendo fortemente', nada mais.
    """

    # Use Llama to ask the question
    response = ollama.chat(
        model='llama3.2',
        messages=[{'role': 'user', 'content': prompt}]
    )
    
    # Get the model's response
    if 'message' in response and 'content' in response['message']:
        output = response['message']['content']
    else:
        output = "O modelo não retornou uma resposta válida."

    print("Resposta do modelo:", output)

    # Validate the response using the validator

    usuario.score +=categories.get(output.lower().strip("'").strip(".").strip(), 0)
    return output

def validarUsuario(usuario, usuario2):
    print("Usuário 1:", usuario.to_json())
    print("Usuário 2:", usuario2)
    
    # Prompt para a LLM
    prompt = f"""
    Sua tarefa é comparar informações para verificar se os dois perfis a seguir pertencem ao mesmo usuário.
    Considere apenas o conteúdo das informações, sem focar na estrutura dos dados JSON. Ignore o campo "exigences" se ele estiver presente.
    
    Usuário 1: {usuario.to_json()}
    Usuário 2: {usuario2}
    
    Com base na similaridade entre os dois perfis, classifique a correspondência entre eles em uma das seguintes opções: 
    'não recomendo fortemente', 'não recomendo', 'neutro', 'recomendo' ou 'recomendo fortemente'. 
    RESPONDA APENAS UMA DAS OPÇÕES, NADA MAIS.
    """
    
    # Envia a consulta à LLM
    response = ollama.chat(
        model='llama3.2',
        messages=[{'role': 'user', 'content': prompt}]
    )
    
    # Extrai a resposta do modelo
    output = response.get('message', {}).get('content', "O modelo não retornou uma resposta válida.")
    
    print("Resposta do modelo:", output)

    print(usuario.score)
    print(categories.get(output.lower().strip("'").strip(".").strip(), 0))
    print(categories)
    # Normaliza a resposta para atualização do score
    usuario.score += categories.get(output.lower().strip("'").strip(".").strip(), 0)

    #update(usuario)
    print(usuario.score)
    print(output.lower().strip("'").strip(".").strip())
    return output  # Retorna a classificação e atualiza o score