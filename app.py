from flask import Flask, request, jsonify
from flask_cors import CORS  # Importando o CORS
import ollama
import service
from model.usuario import user
import Fase3
app = Flask(__name__)
CORS(app)  # Habilitando CORS para todas as rotas


user_sessions = {}



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
@app.route('/Ask', methods=['POST'])
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

@app.route('/Answer', methods=['POST'])
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
