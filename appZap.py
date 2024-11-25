from flask import Flask, request, jsonify
import ollama
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



user_sessions = {} # Dicionario.
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
    "diretorio":                            "/home/bernardoamv/projects/Pesquisa científica/rep/Candidatura---ICSolides/Registros-",
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
            msg.body("""Certo! Já te achei no nosso sistema, Agora vou te pedir algumas informações para confirmação. Por favor, envie suas informações da seguinte forma:
                     Seu nome
                     Vaga que está candidatando
                     Uma experiência profissional sua descrita no currículo
                     Sua mais recente formação profissional""")
            if not os.path.exists(user_model["diretorio"] + user_model['cpf'] + "-" + user_model['nome']):
                user_model["diretorio"] = user_model["diretorio"] + user_model['cpf'] + "-" + user_model['nome']
                os.makedirs(user_model["diretorio"])
                print(f'Diretório "{user_model["diretorio"]}" criado com sucesso!')
            else:
                print(f'O diretório "{user_model["diretorio"]}" já existe.')
            user_model["fase"] += 1
        return str(bot_resp)
    
    elif(user_model["fase"] == 2):
        user = service.parse_string_to_json(incoming_que)
        if user == "A string não contém 4 campos esperados (nome, vaga, experiencia, formação).":
            bot_resp = MessagingResponse()
            msg = bot_resp.message()
            msg.body("""Houve algum problema com sua resposta, por favor reenvie a resposta e certifique que a mesma esteja no seguinte padrão:
                     Seu nome
                     Vaga que está candidatando
                     Uma experiência profissional sua descrita no currículo
                     Sua mais recente formação profissional""")
            return str(bot_resp)
        user2 = service.select(user_model["cpf"])
        user_model['score'] += service.validarUsuario(user2,user)
        print("Novo score do usuário " + user_model['nome'] + ": " + str(user_model['score'])) 
        bot_resp = MessagingResponse()
        msg = bot_resp.message()
        msg.body("""Tudo nos conformes! Agora vou lhe fazer algumas perguntinhas para identificar seu perfil comportamental, ok? E lembre-se, respostas fora dos limites estipulados (1 a 5) irão afetar negativamente seu desempenho!""")
        user_model["fase"] += 1
        return str(bot_resp)
    
    elif(user_model["fase"] == 3):
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
    elif(user_model["fase"] == 4):
        if(user_model["question"]):
             user_model["question"] = False
             user_id = user_model['cpf']
             user_data = service.select(user_id)
             if user_id not in user_sessions:
                user_sessions[user_id] = {
                    "current_question": 0,
                    "score": 0,
                    "questions": [],
                    "answers": [],
                    "notas": [],
                    "respostas_llm": [],
            }
             question = Fase3.gerar_pergunta(user_data.role,user_sessions[user_id]["questions"])
             user_sessions[user_id]["questions"].append(question)
             user_sessions[user_id]["current_question"] += 1
             bot_resp = MessagingResponse()
             msg = bot_resp.message()
             msg.body(question)
             return str(bot_resp)
        else:
            user_id = user_model['cpf']
            user_data = service.select(user_id)
            session = user_sessions.get(user_id)
            if not session:
                return jsonify({'error': 'Sessão não encontrada'}), 400

            current_question = session["questions"][session["current_question"] - 1]
            resposta = Fase3.avaliar_resposta(current_question, incoming_que)
            score = Fase3.extrair_nota(resposta)
            print(f"SCORE ERRADO:{score}")
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
                service.criar_ou_atualizar_csv(user_model["diretorio"] + "/Entrevista_Técnica_" + user_model['cpf'], user_sessions[user_model["cpf"]]["questions"],user_sessions[user_model["cpf"]]["answers"],user_sessions[user_model["cpf"]]["notas"],user_sessions[user_model["cpf"]]["respostas_llm"])
                user_sessions.pop(user_id)
                bot_resp = MessagingResponse()
                msg = bot_resp.message()
                msg.body("Entrevista Finalizada! Agora precisamos que nos envie por aqui mesmo um vídeo se apresentando, falando um pouco sobre si")
                return str(bot_resp)
        
            next_question = Fase3.gerar_pergunta(user_data.role, user_sessions[user_id]["questions"])
            session["questions"].append(next_question)
            session["current_question"] += 1
            bot_resp = MessagingResponse()
            msg = bot_resp.message()
            msg.body(next_question)
            return str(bot_resp)
    elif (user_model["fase"] == 5):
        Video_handler = videohandler.WhatsAppVideoHandler(
            account_sid=f'{os.getenv("TWILLIO_ACCOUNT")}',
            auth_token=f'{os.getenv("TWILLIO_TOKEN")}',
            upload_folder=user_model["diretorio"],
        )
        success, message, saved_path =  Video_handler.process_video_message(request.values)
    
        if success:
        # Add your custom logic here
        # For example, store the path in your database
            Video_handler.store_in_database(saved_path)
    
        resp = MessagingResponse()
        resp.message(message)
        return str(resp)

    


if __name__ == '__main__':
    app.run(debug=True, port=5000)
