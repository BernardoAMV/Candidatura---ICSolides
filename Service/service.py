import pandas as pd
import ollama
from model.usuario import user
import re
import requests
import csv
import json
import os
import csv
DB = "DB/DB.csv"


def criar_ou_atualizar_csv(caminho_arquivo, perguntas, respostas, notas):
    # Verificando se o arquivo já existe
    arquivo_existe = os.path.exists(caminho_arquivo)

    # Abrindo o arquivo CSV para adicionar dados
    with open(caminho_arquivo, mode='a', newline='', encoding='utf-8') as arquivo:
        writer = csv.writer(arquivo)

        # Se o arquivo não existe, escreve o cabeçalho
        if not arquivo_existe:
            writer.writerow(['pergunta', 'resposta', 'nota'])

        # Adicionando uma linha para cada item das listas
        for pergunta, resposta, nota in zip(perguntas, respostas, notas):
            writer.writerow([pergunta, resposta, nota])

    print(f"Dados adicionados ao arquivo: {caminho_arquivo}")



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

welcome = """Olá!

Sobrevém a Sólides! Estamos aqui para ajudar você a encontrar o seu lugar no nosso time.

Para prosseguir com sua candidatura, precisamos de alguns detalhes importantes. Por favor, forneça-nos seu CPF completo, sem incluir pontos e traços. É fundamental que você não inclua esses elementos para garantir a segurança e identificação.

Nós aguardamos ansiosamente por sua resposta e estamos confiantes de que você vai se destacar entre os candidatos!

Obrigado pela sua cooperação e esperamos ouvir de você logo!"""


categories = {
    "não recomendo fortemente": -10,
    "não recomendo": -5,
    "neutro": 0,
    "recomendo": 5,
    "recomendo fortemente": 10
}

# Function to select the user based on CPF from the CSV
import pandas as pd

import pandas as pd

def select(cpf):
    # Read the CSV file
    df = pd.read_csv(DB)
    
    # Converte a coluna 'cpf' para string e remove espaços extras
    df['cpf'] = df['cpf'].astype(str).str.strip()

    # Garantir que o CPF recebido seja tratado como string e sem pontos ou traços
    cpf = str(cpf).replace('.', '').replace('-', '').zfill(11)  # Garantir 11 caracteres (com o zero à esquerda)

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



def gen_welcome():
    prompt = """
    Por favor, gere uma mensagem de boas vindas ao programa de candidatura da empresa fictícia Sólides, e peça, com gentileza para o usuário (fictício) enviar seu cpf.
    Lembre o usuário de INCLUIR pontos e traços, o cpf deve conter traços e pontos.
    O campo de entrada do usuário JÁ ESTÁ IMPLEMENTADO E DEMONSTRADO, NÃO OFEREÇA UM CAMPO DE ENTRADA.

    este é um exemplo de entrada perfeito, se inspire nele: 
    
    """
    
    # Envia a consulta à LLM
    response = ollama.chat(
        model='llama3.2',
        messages=[{'role': 'user', 'content': prompt}]
    )
    
    if 'message' in response and 'content' in response['message']:
        output = response['message']['content']
    else:
        output = "O modelo não retornou uma resposta válida."

    print("Resposta do modelo:", output)

    return output




    
def getAll():
    # Lê o arquivo CSV
    df = pd.read_csv(DB)
    
    # Lista para armazenar objetos `user`
    users = []
    
    # Itera sobre cada linha do DataFrame
    for _, row in df.iterrows():
        # Extrai os dados de cada coluna
        name = row['name']
        cpf = row['cpf']
        role = row['role']
        experiences = row['experiences']
        degree = row['degree']
        exigences = row['exigences']
        score = int(row['score'])  # Converte para inteiro
        # Converte `experiences` e `exigences` para lista
        if isinstance(experiences, str):
            experiences = experiences.split(',')
        else:
            experiences = []
        
        if isinstance(exigences, str):
            exigences = exigences.split(',')
        else:
            exigences = []
        
        # Cria o objeto `user` e adiciona à lista
        user_obj = user(name=name, cpf=cpf, role=role, experiences=experiences, degree=degree, exigences=exigences, score=score)
        users.append(user_obj)
    
    # Retorna a lista de usuários
    return users


def update(usuario):
    # Lê o arquivo CSV e armazena o conteúdo em uma lista
    usuarios = []
    usuario_atualizado = False
    
    # Carrega todos os dados do CSV e procura o usuário a ser atualizado
    with open(DB, mode='r', newline='', encoding='utf-8') as csvfile:
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
    with open(DB, mode='w', newline='', encoding='utf-8') as csvfile:
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

    # usuario.score +=categories.get(output.lower().strip("'").strip(".").strip(), 0)
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

    # Normaliza a resposta para atualização do score
    #usuario.score += categories.get(output.lower().strip("'").strip(".").strip(), 0)

    #update(usuario)
    print(usuario.score)
    return output  # Retorna a classificação e atualiza o score