from flask import Flask, request, jsonify
import Service.service as service
from model.usuario import user
from Fases import Fase2
from Fases import Fase3
from twilio.twiml.messaging_response import MessagingResponse
from antecedentes import CPFService
import os
from dotenv import load_dotenv
import requests
import Service.videohandler as videohandler
# Carregar variáveis de ambiente do arquivo .env    
load_dotenv()
import anthropic

API_KEY = os.getenv("CLAUDE_API_KEY")

client = anthropic.Anthropic(
    # defaults to os.environ.get("ANTHROPIC_API_KEY")
    api_key=API_KEY,
)
user_sessions = {} # Dicionario.
user_sessionsFase4 = {}

user_model = {
    # fase 1
    "nome":                               "",
    "idade":                              16,
    "etc":                          "asfasf",
    # fase 2
    "perfilComportamental":               "", # Resultado, em texto, da avaliacao MBTI/Profiler
    "avaliacaoFase2":                     "", # Resultado em texto da avaliação total MBTI + Analise Sentimento
    "fase2_current_question_index":        0,
    "fase2_scores":      Fase2.scores.copy(),
    "fase2_questions_completed":       False,
    # fase 3
    "current_question":                    0, # Trackeia qual questão estamos na fase 3
    "score":                               50, # Pontuação total?
    "questions":                          [], # Lista de questoes que foram perguntadas.
    "answers":                            [], # Lista de respostas dadas pelo usuario.
    "correction":                         [],  # 'Correcao'/Opiniao da IA sobre a resposta para a pergunta.  
    "fase":                                0,
    "cpf":                                 "",
    "controle":                             1,
    "question":                             True,
    "diretorio":                            "Candidatura---ICSolides/Registros-",
    "incomplete":                           False,
    "dados_usuario":                        {},
}
# Funcao para adicionar ID ao user_sessions se não existir
def newSessionID(idCandidato):
    if idCandidato not in user_sessions:
        user_sessions[idCandidato] = user_model.copy()
def process_media(media_url, media_type, save_path="video_recebido.mp4"):
    """
    Processa e baixa uma mídia do Twilio.

    Args:
        media_url (str): URL da mídia fornecida pelo Twilio.
        media_type (str): Tipo da mídia (ex.: video/mp4).
        save_path (str): Caminho para salvar a mídia baixada.

    Returns:
        bool: True se a mídia foi baixada e salva com sucesso, False caso contrário.
    """
    if not media_url or not media_type.startswith("video"):
        print("A mídia não é um vídeo válido.")
        return False

    print(f"Baixando mídia do URL: {media_url}")
    try:
        # Fazer a requisição para baixar a mídia
        response = requests.get(media_url, headers={
            "Authorization": f"Basic {os.getenv('TWILIO_AUTH')}"
        })

        if response.status_code == 200:
            # Salvar o conteúdo no arquivo
            with open(save_path, "wb") as video_file:
                video_file.write(response.content)
            print(f"Vídeo salvo em: {save_path}")
            return True
        else:
            print(f"Falha ao baixar a mídia. Código de status: {response.status_code}")
            return False
    except Exception as e:
        print(f"Erro ao processar a mídia: {e}")
        return False


app = Flask(__name__)
    
@app.route('/webhook', methods=['POST'])
def webhook():
    incoming_que = request.values.get('Body', '').lower()
    print(incoming_que)
    if(user_model["fase"] == 0):
            resp =  service.welcome
            bot_resp = MessagingResponse()
            msg = bot_resp.message()
            msg.body(resp)
            user_model["fase"] += 1
            return str(bot_resp)
    if(user_model["fase"] == 1):
        if(CPFService.validaCPF(incoming_que)):
            print("validou")
            user = service.select(str(incoming_que))
            user_model['nome'] = user.name
            user_model['cpf'] = incoming_que
        else:
            print(CPFService.validaCPF(incoming_que))
            user = None
        if(user == None):
            resp =  "Usuário não encontrado, Por favor digite seu cpf Novamente! (Não inclua símbolos)"
            bot_resp = MessagingResponse()
            msg = bot_resp.message()
            msg.body(resp)
        else:
            print(CPFService.possuiAntecedentes(incoming_que, "antecedentes/banco_de_CPF.json"))
            if(CPFService.possuiAntecedentes(incoming_que, "antecedentes/banco_de_CPF.json")):
                user_model['score'] += service.fase1(user)
                user_model['score'] -= 30;
                print("Novo score do usuário " + user_model['nome'] + ": " + str(user_model['score']))
            else:
                user_model['score'] += service.fase1(user)
                print("Novo score do usuário " + user_model['nome'] + ": " + str(user_model['score']))
            bot_resp = MessagingResponse()
            msg = bot_resp.message()
            msg.body("""Certo! Já te achei no nosso sistema, Agora vou te pedir algumas informações para confirmação. Por favor, nos envie seu nome, uma experiência profissional, a vaga que está candidatando e sua formação profissional (Bacharel, Técnico, Mestrado):
                     """)
            if not os.path.exists(user_model["diretorio"] + user_model['cpf'] + "-" + user_model['nome']):
                user_model["diretorio"] = user_model["diretorio"] + user_model['cpf'] + "-" + user_model['nome']
                os.makedirs(user_model["diretorio"])
                print(f'Diretório "{user_model["diretorio"]}" criado com sucesso!')
            else:
                print(f'O diretório "{user_model["diretorio"]}" já existe.')
            user_model["fase"] += 1
        return str(bot_resp)
    
    elif(user_model["fase"] == 2):
        user2 = service.select(user_model["cpf"])
        if not user_model["incomplete"]:
            user_model["dados_usuario"] = service.mapear_campos_disponiveis(incoming_que)
            print(user_model["dados_usuario"])
        print(user_model["dados_usuario"])
        resposta = service.ExtrairInfos(incoming_que, user_model["incomplete"],user_model["dados_usuario"])
        if(resposta["status"] != "sucesso"):
            bot_resp = MessagingResponse()
            msg = bot_resp.message()
            msg.body(resposta["prompt_complementar"])
            user_model["incomplete"] = True
            return str(bot_resp)
        user_model['score'] += service.validarUsuario(user2,resposta["dados"])
        print("Novo score do usuário " + user_model['nome'] + ": " + str(user_model['score'])) 
        bot_resp = MessagingResponse()
        msg = bot_resp.message()
        msg.body("""Tudo nos conformes! Agora vou lhe fazer algumas perguntinhas para identificar seu perfil comportamental, ok? E lembre-se, respostas fora dos limites estipulados (1 a 5) irão afetar negativamente seu desempenho!""")
        user_model["fase"] += 1
        return str(bot_resp)
    
    elif(user_model["fase"] == 35):
        if(user_model["question"]):
            newSessionID(user_model["cpf"])
            resp = Fase2.nextQuestion()
            user_model["question"] = False
            bot_resp = MessagingResponse()
            msg = bot_resp.message()
            msg.body(resp)
            return str(bot_resp)
        else:
            if incoming_que != "":
                response = int(incoming_que)
                print(response)
                Fase2.grabResposta(response)
                question = Fase2.nextQuestion()
            else:    
                question = Fase2.nextQuestion()
            if user_model["cpf"] not in user_sessions or user_sessions[user_model["cpf"]].get("fase2_questions_completed"):
                return jsonify({'error': 'Session not found or phase 2 already completed'}), 400
            if question == "All questions completed.":
                result = Fase2.getResultado()
                user_model["perfilComportamental"] = result
                print("Resultado mbti: " + result)
                user_sessions[user_model["cpf"]]["perfilComportamental"] = result
                user_sessions[user_model["cpf"]]["fase2_questions_completed"] = True
                user_model["fase"] += 1
                user_model["question"] = True
                bot_resp = MessagingResponse()
                msg = bot_resp.message()
                msg.body("""Certo, acabamos seu perfil comportamental! Agora vamos fazer uma mini entrevista técnica, serão 5 perguntinhas sobre sua área de atuação, ok? Caso não saiba responder à pergunta, responda 'pular pergunta'.""")
                return str(bot_resp)

            bot_resp = MessagingResponse()
            msg = bot_resp.message()
            msg.body(question)
            return str(bot_resp)
    elif(user_model["fase"] == 3):
        if(user_model["question"]):
             user_model["question"] = False
             user_id = user_model['cpf']
             user_data = service.select(user_id)
             if user_id not in user_sessionsFase4:
                user_sessionsFase4[user_id] = {
                    "current_question": 0,
                    "score": 0,
                    "questions": [],
                    "answers": [],
                    "notas": [],
                    "respostas_llm": [],
            }
             question = Fase3.gerar_pergunta(user_data.role,user_sessionsFase4[user_id]["questions"], client)
             user_sessionsFase4[user_id]["questions"].append(question)
             user_sessionsFase4[user_id]["current_question"] += 1
             bot_resp = MessagingResponse()
             msg = bot_resp.message()
             msg.body(question)
             return str(bot_resp)
        else:
            user_id = user_model['cpf']
            user_data = service.select(user_id)
            session = user_sessionsFase4.get(user_id)
            if not session:
                return jsonify({'error': 'Sessão não encontrada'}), 400

            current_question = session["questions"][session["current_question"] - 1]
            resposta = Fase3.avaliar_resposta(current_question, incoming_que, client)
            score = Fase3.extrair_nota(resposta)
            print(f"SCORE atual:{score}")
            if(score == 0):
                bot_resp = MessagingResponse()
                msg = bot_resp.message()
                msg.body("Desculpe, não entendi sua resposta, pode responder novamente?")
                return str(bot_resp)
            else:
                session["respostas_llm"].append(resposta)
            print(session["score"])
            session["score"] += int(score)
            session["answers"].append(incoming_que)
            session["notas"].append(int(score))
        
            if session["current_question"] >= 5:
                final_score = session["score"]
                user_model['score'] += final_score / 5 #média das notas das respostas
                print("Novo score do usuário " + user_model['nome'] + ": " + str(user_model['score']))
                print(user_model['diretorio'])
                service.criar_ou_atualizar_csv(user_model["diretorio"] + "/Entrevista_Técnica_" + user_model['cpf'], user_sessionsFase4[user_model["cpf"]]["questions"],user_sessionsFase4[user_model["cpf"]]["answers"],user_sessionsFase4[user_model["cpf"]]["notas"],user_sessionsFase4[user_model["cpf"]]["respostas_llm"])
                user_sessionsFase4.pop(user_id)
                bot_resp = MessagingResponse()
                msg = bot_resp.message()
                msg.body("Entrevista Finalizada! Agora precisamos que nos envie por aqui mesmo um vídeo se apresentando, falando um pouco sobre si")
                user_model["fase"] += 1
                return str(bot_resp)
        
            next_question = Fase3.gerar_pergunta(user_data.role, user_sessionsFase4[user_id]["questions"], client)
            session["questions"].append(next_question)
            session["current_question"] += 1
            bot_resp = MessagingResponse()
            msg = bot_resp.message()
            msg.body(next_question)
            return str(bot_resp)
    elif (user_model["fase"] == 5):
        texto_transcrito =  Fase2.transcreveTexto("video/video.mp4")
        emocao = Fase2.extraiEmocao(texto_transcrito)
        resultado = Fase2.gerarScoreEAvaliacao(user_model["perfilComportamental"],texto_transcrito,emocao)
        print(resultado)
        bot_resp = MessagingResponse()
        msg = bot_resp.message()
        msg.body("Prontinho! Agora é só aguardar!")
        return str(bot_resp)
    


if __name__ == '__main__':
    app.run(debug=True, port=5000)
