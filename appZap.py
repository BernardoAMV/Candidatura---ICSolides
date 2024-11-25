from flask import Flask, request, jsonify
import ollama
import service
from model.usuario import user
import Fase2
import Fase3
from twilio.twiml.messaging_response import MessagingResponse

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
    "fase2_videoEmocaoAnalise":           "",
    "fase2_notafinal":                    -1,
    # fase 3
    "current_question":                    0, # Trackeia qual questão estamos na fase 3
    "score":                               0, # Pontuação total?
    "questions":                          [], # Lista de questoes que foram perguntadas.
    "answers":                            [], # Lista de respostas dadas pelo usuario.
    "correction":                         [],  # 'Correcao'/Opiniao da IA sobre a resposta para a pergunta.  
    "fase":                                1,
    "cpf":                                 "",
    "controle":                             1,
    "question":                             True,
}
# Funcao para adicionar ID ao user_sessions se não existir
def newSessionID(idCandidato):
    if idCandidato not in user_sessions:
        user_sessions[idCandidato] = user_model.copy()



app = Flask(__name__)
def gen_resp(prompt):
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
    
    return output
    
@app.route('/webhook', methods=['POST'])
def teste():
    incoming_que = request.values.get('Body', '').lower()
    print(incoming_que)

    if(user_model["fase"] == 1):
        user = service.select(incoming_que)
        if(user == None):
            resp =  "Usuário não encontrado, Por favor digite seu cpf Novamente! (Inclua números e símbolos)"
            bot_resp = MessagingResponse()
            msg = bot_resp.message()
            msg.body(resp)
        else:
            service.fase1(user)
            bot_resp = MessagingResponse()
            msg = bot_resp.message()
            msg.body("""Certo! Já te achei no nosso Sistema, Agora vou te pedir algumas informações para confirmação. Por favor, envie suas informações da seguinte forma:
                     Seu nome
                     Vaga que está candidatando
                     Uma experiência profissional sua descrita no currículo
                     Sua mais recente formação profissional""")
            user_model["cpf"] = incoming_que
            user_model["fase"] += 1
        return str(bot_resp)
    
    elif(user_model["fase"] == 2):
        user = service.parse_string_to_json(incoming_que)
        user2 = service.select(user_model["cpf"])
        service.validarUsuario(user2,user)
        bot_resp = MessagingResponse()
        msg = bot_resp.message()
        msg.body("Tudo nos conformes! Agora vou lhe fazer algumas perguntinhas para identificar seu perfil comportamental, ok?")
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
                user_sessions[user_model["cpf"]]["perfilComportamental"] = result
                user_sessions[user_model["cpf"]]["fase2_questions_completed"] = True
                user_model["fase"] += 1
                user_model["question"] = True
                bot_resp = MessagingResponse()
                msg = bot_resp.message()
                msg.body("Certo, acabamos seu o teste de perfil comportamental! Agora vou pedir para que voce me envie um video curto falando sobre o seu interesse na vaga!")
                return str(bot_resp)

            bot_resp = MessagingResponse()
            msg = bot_resp.message()
            msg.body(question)
            return str(bot_resp)
    
    elif(user_model["fase"] == 4):
        if 'file' not in request.files:
            bot_resp = MessagingResponse()
            msg = bot_resp.message()
            msg.body("Por favor, envie um vídeo no formato .mp4 para continuar.")
            return str(bot_resp)
        file = request.files['file']
        if file.filename == '':
            bot_resp = MessagingResponse()
            msg = bot_resp.message()
            msg.body("Nenhum arquivo enviado. Por favor, envie um vídeo no formato .mp4 para continuar.")
            return str(bot_resp)
        if file and file.filename.endswith('.mp4'):
            file_path = f"/tmp/{file.filename}"
            file.save(file_path)
            user_model["fase2_videoEmocaoAnalise"] = Fase2.extraiEmocao(Fase2.transcreveTexto(f"/tmp/{file.filename}"))
            user_model["fase2_avaliacaoFase2"] = Fase2.gerarScoreEAvaliacao(user_model["perfilComportamental"],
                                                                          Fase2.transcreveTexto(f"/tmp/{file.filename}"),
                                                                          user_model["fase2_videoEmocaoAnalise"])
            file.remove(file_path)
            bot_resp = MessagingResponse()
            msg = bot_resp.message()
            msg.body("Vídeo recebido e processado! Obrigado! Vamos para a próxima etapa.")
            user_model["fase"] += 1
            return str(bot_resp)
        else:
            bot_resp = MessagingResponse()
            msg = bot_resp.message()
            msg.body("O arquivo enviado não é um vídeo .mp4 válido. Por favor, envie um vídeo no formato correto.")
            return str(bot_resp)

    elif(user_model["fase"] == 5):
        if(user_model["question"]):
             user_model["question"] = False
             user_id = user_model['cpf']
             user_data = service.select(user_id)
             if user_id not in user_sessions:
                user_sessions[user_id] = {
                    "current_question": 0,
                    "score": 0,
                    "questions": [],
                    "answers": []
            }
             question = Fase3.gerar_pergunta(user_data.role)
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
       
            score = Fase3.extrair_nota(Fase3.avaliar_resposta(current_question, incoming_que))
            print(session["score"])
            session["score"] += int(score)
            session["answers"].append(incoming_que)
        
            if session["current_question"] >= 5:
                final_score = session["score"]
                user_sessions.pop(user_id)
                bot_resp = MessagingResponse()
                msg = bot_resp.message()
                msg.body("Entrevista Finalizada! Muito obrigado por participar de nosso processo!")
                return str(bot_resp)
        
            next_question = Fase3.gerar_pergunta(user_data.role)
            session["questions"].append(next_question)
            session["current_question"] += 1
            bot_resp = MessagingResponse()
            msg = bot_resp.message()
            msg.body(next_question)
            return str(bot_resp)



if __name__ == '__main__':
    app.run(debug=True, port=5000)
