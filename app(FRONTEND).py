from flask import Flask, request, jsonify
from flask_cors import CORS  # Importando o CORS
import ollama
import Service.service as service
from model.usuario import user
import Fase2
import Fase3
from twilio.twiml.messaging_response import MessagingResponse



app = Flask(__name__)
CORS(app)  # Habilitando CORS para todas as rotas


# Bernardo, estou optando por usar o user_session para guardar os dados da Fase 2 e da Fase 3.
# Isso vai facilitar para exportar só o que é importante mais tarde para a fase 4.
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
    "score":                               0, # Pontuação total?
    "questions":                          [], # Lista de questoes que foram perguntadas.
    "answers":                            [], # Lista de respostas dadas pelo usuario.
    "correction":                         []  # 'Correcao'/Opiniao da IA sobre a resposta para a pergunta.  
}

# Funcao para adicionar ID ao user_sessions se não existir
def newSessionID(idCandidato):
    if idCandidato not in user_sessions:
        user_sessions[idCandidato] = user_model.copy()


# Fase 1
@app.route('/Fase1', methods=['POST'])
def Fase1():
    try:
        data = request.json
        user_input = data.get("message")
        user_input = service.select(user_input)
        
        if user_input != None:
            print(user_input.score)
            output_resultado = service.fase1(user_input)
            print(user_input.score)
            return jsonify({'response': output_resultado})
        else:
            return jsonify({'response': "Usuário não encontrado!"})
    except Exception as e:
        return jsonify({'error': f'Erro ao gerar resposta: {str(e)}'}), 500
    
@app.route('/Valida', methods=['POST'])
def Valida():
    try:
        data = request.json
        user_input = data.get("cpf")
        user_input = service.select(user_input)
        user2 = data
        service.validarUsuario(user_input, user2)
        return jsonify({'response': "Obrigado!" })
    except Exception as e:
        return jsonify({'error': f'Erro ao gerar resposta: {str(e)}'}), 500
    
# Fase 2
@app.route('/Fase2Ask', methods=['POST'])
def Fase2Ask():
    try:

        data = request.json
        user_id = data.get("cpf")
        newSessionID(user_id)
        question = Fase2.nextQuestion()
        print(question)
        return jsonify({'response': question})
    except Exception as e:
        return jsonify({'error': f'Error generating MBTI question: {str(e)}'}), 500

@app.route('/Fase2Answer', methods=['POST'])
def Fase2Answer():
    try:
        data = request.json
        user_id = data.get("cpf")
        response = data.get("resposta")
        if response != "":
            response = int(data.get("resposta"))
            print(response)
            print("bababa")
            Fase2.grabResposta(response)
            question = Fase2.nextQuestion()
        else:    
            question = Fase2.nextQuestion()
        if user_id not in user_sessions or user_sessions[user_id].get("fase2_questions_completed"):
            return jsonify({'error': 'Session not found or phase 2 already completed'}), 400
        if question == "All questions completed.":
            print("ACABO")
            result = Fase2.getResultado()
            user_sessions[user_id]["perfilComportamental"] = result
            user_sessions[user_id]["fase2_questions_completed"] = True
            return jsonify({'response': 'Phase 2 completed', 'perfilComportamental': result, 'final': True})

        return jsonify({'response': question})
    except Exception as e:
        return jsonify({'error': f'Error processing MBTI answer: {str(e)}'}), 500

# Fase 3
@app.route('/Fase3Ask', methods=['POST'])
def Pergunta():
    try:
        data = request.json
        user_id = data.get("cpf")
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

        return jsonify({'response': question})
    except Exception as e:
        return jsonify({'error': f'Erro ao gerar resposta: {str(e)}'}), 500

@app.route('/Fase3Answer', methods=['POST'])
def Resposta():
    try:
        data = request.json
        user_id = data.get("cpf")
        user_answer = data.get("resposta")
        user_data = service.select(user_id)

        session = user_sessions.get(user_id)
        if not session:
            return jsonify({'error': 'Sessão não encontrada'}), 400

        current_question = session["questions"][session["current_question"] - 1]
       
        score = Fase3.extrair_nota(Fase3.avaliar_resposta(current_question, user_answer))
        
        print(session["score"])
        session["score"] += int(score)
        session["answers"].append(user_answer)
        
        if session["current_question"] >= 5:
            final_score = session["score"]
            user_sessions.pop(user_id)
            return jsonify({'response': f'Entrevista finalizada!', 'final_score': final_score, 'final': True})
        
        next_question = Fase3.gerar_pergunta(user_data.role)
        session["questions"].append(next_question)
        session["current_question"] += 1
        
        return jsonify({'response': next_question})
    except Exception as e:
        return jsonify({'error': f'Erro ao avaliar resposta: {str(e)}'}), 500



if __name__ == '__main__':
    app.run(debug=True)
