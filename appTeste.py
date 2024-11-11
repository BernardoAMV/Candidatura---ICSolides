from flask import Flask, request, jsonify
from collections import defaultdict
from flask_cors import CORS  # Importando o CORS
import ollama
import service
from model.usuario import user
import Fase2
import Fase3
from twilio.twiml.messaging_response import MessagingResponse




app = Flask(__name__)
CORS(app)
fase = 1

@app.route("/webhook", methods=["POST"])
def webhook():
    # Recebe a mensagem do usuário e seu número de telefone
    data = request.values.get('Body', '')
    user = service.select(data)
    # Identifica o usuário e sua fase atual
    user = get_user(phone)
    fase = user["fase"]

    if fase == 1:
        # Validação de CPF
        if is_valid_cpf(user_message):  # Suponha uma função de validação de CPF
            user["cpf"] = user_message
            user["fase"] = 2
            return jsonify({"response": "CPF válido. Por favor, me informe seu nome."})
        else:
            return jsonify({"response": "CPF inválido! Tente novamente, incluindo pontos e traços."})

    elif fase == 2:
        # Coleta de Nome
        user["nome"] = user_message
        user["fase"] = 3
        return jsonify({"response": "Para qual vaga você está se candidatando?"})

    elif fase == 3:
        # Coleta da Vaga
        user["vaga"] = user_message
        user["fase"] = 4
        return jsonify({"response": "Conte-me sobre uma experiência profissional sua."})

    elif fase == 4:
        # Coleta de Experiência Profissional
        user["experiencia"] = user_message
        user["fase"] = 5
        return jsonify({"response": "Qual sua formação acadêmica?"})

    elif fase == 5:
        # Coleta de Formação Acadêmica
        user["formacao"] = user_message
        user["fase"] = 6
        # Agora pode validar as informações do usuário
        return jsonify({"response": "Informações coletadas! Vamos começar a próxima etapa de perguntas comportamentais."})

    elif fase == 6:
        # Perguntas de perfil comportamental, enviando uma a uma
        pergunta = proxima_pergunta_mbti(user)  # Função que gera a próxima pergunta MBTI
        if pergunta:
            return jsonify({"response": pergunta})
        else:
            user["fase"] = 7  # Fase finalizada
            return jsonify({"response": "Perguntas comportamentais finalizadas!"})

    elif fase == 7:
        # Perguntas técnicas da entrevista
        pergunta_entrevista = proxima_pergunta_tecnica(user)
        if pergunta_entrevista:
            return jsonify({"response": pergunta_entrevista})
        else:
            return jsonify({"response": "Entrevista finalizada! Obrigado."})

    return jsonify({"response": "Erro na fase da entrevista."})


def is_valid_cpf(cpf):
    # Aqui você implementa a validação do CPF
    return True  # Placeholder para simplificação

def proxima_pergunta_mbti(user):
    # Simula a próxima pergunta MBTI, avança fase se terminar
    # Exemplo de perguntas MBTI fictícias
    perguntas_mbti = [
        "Você prefere trabalho em equipe ou sozinho?",
        "Você toma decisões com base na lógica ou nos sentimentos?",
    ]
    if "pergunta_mbti_index" not in user:
        user["pergunta_mbti_index"] = 0
    if user["pergunta_mbti_index"] < len(perguntas_mbti):
        pergunta = perguntas_mbti[user["pergunta_mbti_index"]]
        user["pergunta_mbti_index"] += 1
        return pergunta
    return None

def proxima_pergunta_tecnica(user):
    # Exemplo de perguntas técnicas fictícias
    perguntas_tecnicas = [
        "Qual a sua experiência com desenvolvimento web?",
        "Como você lida com prazos apertados?",
    ]
    if "pergunta_tecnica_index" not in user:
        user["pergunta_tecnica_index"] = 0
    if user["pergunta_tecnica_index"] < len(perguntas_tecnicas):
        pergunta = perguntas_tecnicas[user["pergunta_tecnica_index"]]
        user["pergunta_tecnica_index"] += 1
        return pergunta
    return None

if __name__ == "__main__":
    app.run(debug=True)
