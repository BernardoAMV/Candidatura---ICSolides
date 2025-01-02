from flask import Flask, request, jsonify
from threading import Lock
import queue
from dataclasses import dataclass, asdict
from typing import Dict, Any
import time
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
@dataclass
class UserSession:
    nome: str = ""
    idade: int = 16
    etc: str = "asfasf"
    perfilComportamental: str = ""
    avaliacaoFase2: str = ""
    fase2_current_question_index: int = 0
    fase2_scores: Dict = None
    fase2_questions_completed: bool = False
    current_question: int = 0
    score: int = 50
    questions: list = None
    answers: list = None
    correction: list = None
    fase: int = 0
    cpf: str = ""
    controle: int = 1
    question: bool = True
    diretorio: str = "Candidatura---ICSolides/Registros-"
    incomplete: bool = False
    dados_usuario: Dict = None
    last_activity: float = 0
    
    def __post_init__(self):
        self.questions = []
        self.answers = []
        self.correction = []
        self.dados_usuario = {}
        self.fase2_scores = {}
        self.last_activity = time.time()

class SessionManager:
    def __init__(self, session_timeout=1800):  # 30 minutes timeout
        self.sessions: Dict[str, UserSession] = {}
        self.session_locks: Dict[str, Lock] = {}
        self.cleanup_queue = queue.Queue()
        self.session_timeout = session_timeout
        self.manager_lock = Lock()
    
    def get_session(self, session_id: str) -> UserSession:
        with self.manager_lock:
            if session_id not in self.sessions:
                self.sessions[session_id] = UserSession()
                self.session_locks[session_id] = Lock()
            self.sessions[session_id].last_activity = time.time()
            return self.sessions[session_id]
    
    def get_session_lock(self, session_id: str) -> Lock:
        with self.manager_lock:
            if session_id not in self.session_locks:
                self.session_locks[session_id] = Lock()
            return self.session_locks[session_id]
    
    def cleanup_old_sessions(self):
        current_time = time.time()
        with self.manager_lock:
            expired_sessions = [
                session_id for session_id, session in self.sessions.items()
                if current_time - session.last_activity > self.session_timeout
            ]
            for session_id in expired_sessions:
                del self.sessions[session_id]
                del self.session_locks[session_id]

session_manager = SessionManager()

app = Flask(__name__)
@app.route('/webhook', methods=['POST'])
def webhook():
    incoming_que = request.values.get('Body', '').lower()
    cpf = request.values.get('From', '')
    
    session = session_manager.get_session(cpf)
    session_lock = session_manager.get_session_lock(cpf)
    
    with session_lock:
        if session.fase == 0:
            resp = service.welcome
            bot_resp = MessagingResponse()
            msg = bot_resp.message()
            msg.body(resp)
            session.fase += 1
            return str(bot_resp)
            
        if session.fase == 1:
            if CPFService.validaCPF(incoming_que):
                user = service.select(str(incoming_que))
                session.nome = user.name
                session.cpf = incoming_que
            else:
                user = None
                
            if user == None:
                resp = "Usuário não encontrado, Por favor digite seu cpf Novamente! (Não inclua símbolos)"
                bot_resp = MessagingResponse()
                msg = bot_resp.message()
                msg.body(resp)
            else:
                if CPFService.possuiAntecedentes(incoming_que, "antecedentes/banco_de_CPF.json"):
                    session.score += service.fase1(user)
                    session.score -= 30
                    print(f"Novo score do usuário {session.nome}: {session.score}")
                else:
                    session.score += service.fase1(user)
                    print(f"Novo score do usuário {session.nome}: {session.score}")
                    
                bot_resp = MessagingResponse()
                msg = bot_resp.message()
                msg.body("""Certo! Já te achei no nosso sistema, Agora vou te pedir algumas informações para confirmação. Por favor, nos envie seu nome, uma experiência profissional, a vaga que está candidatando e sua formação profissional (Bacharel, Técnico, Mestrado):""")
                
                if not os.path.exists(session.diretorio + session.cpf + "-" + session.nome):
                    session.diretorio = session.diretorio + session.cpf + "-" + session.nome
                    os.makedirs(session.diretorio)
                    print(f'Diretório "{session.diretorio}" criado com sucesso!')
                else:
                    print(f'O diretório "{session.diretorio}" já existe.')
                session.fase += 1
            return str(bot_resp)
        
        elif session.fase == 2:
            user2 = service.select(session.cpf)
            if not session.incomplete:
                session.dados_usuario = service.mapear_campos_disponiveis(incoming_que)
                
            resposta = service.ExtrairInfos(incoming_que, session.incomplete, session.dados_usuario)
            if resposta["status"] != "sucesso":
                bot_resp = MessagingResponse()
                msg = bot_resp.message()
                msg.body(resposta["prompt_complementar"])
                session.incomplete = True
                return str(bot_resp)
                
            session.score += service.validarUsuario(user2, resposta["dados"])
            print(f"Novo score do usuário {session.nome}: {session.score}")
            
            bot_resp = MessagingResponse()
            msg = bot_resp.message()
            msg.body("""Tudo nos conformes! Agora vou lhe fazer algumas perguntinhas para identificar seu perfil comportamental, ok? E lembre-se, respostas fora dos limites estipulados (1 a 5) irão afetar negativamente seu desempenho!""")
            session.fase += 1
            return str(bot_resp)
        
        elif session.fase == 35:
            if session.question:
                resp = Fase2.nextQuestion()
                session.question = False
                bot_resp = MessagingResponse()
                msg = bot_resp.message()
                msg.body(resp)
                return str(bot_resp)
            else:
                if incoming_que != "":
                    response = int(incoming_que)
                    Fase2.grabResposta(response)
                
                question = Fase2.nextQuestion()
                if question == "All questions completed.":
                    result = Fase2.getResultado()
                    session.perfilComportamental = result
                    session.fase2_questions_completed = True
                    session.fase += 1
                    session.question = True
                    
                    bot_resp = MessagingResponse()
                    msg = bot_resp.message()
                    msg.body("""Certo, acabamos seu perfil comportamental! Agora vamos fazer uma mini entrevista técnica, serão 5 perguntinhas sobre sua área de atuação, ok? Caso não saiba responder à pergunta, responda 'pular pergunta'.""")
                    return str(bot_resp)

                bot_resp = MessagingResponse()
                msg = bot_resp.message()
                msg.body(question)
                return str(bot_resp)
                
        elif session.fase == 3:
            if session.question:
                session.question = False
                user_data = service.select(session.cpf)
                
                session.current_question = 0
                session.questions = []
                session.answers = []
                session.correction = []
                
                question = Fase3.gerar_pergunta(user_data.role, session.questions, client)
                session.questions.append(question)
                session.current_question += 1
                
                bot_resp = MessagingResponse()
                msg = bot_resp.message()
                msg.body(question)
                return str(bot_resp)
            else:
                user_data = service.select(session.cpf)
                current_question = session.questions[session.current_question - 1]
                resposta = Fase3.avaliar_resposta(current_question, incoming_que, client)
                score = Fase3.extrair_nota(resposta)
                
                if score == 0:
                    bot_resp = MessagingResponse()
                    msg = bot_resp.message()
                    msg.body("Desculpe, não entendi sua resposta, pode responder novamente?")
                    return str(bot_resp)
                    
                session.correction.append(resposta)
                session.score += int(score)
                session.answers.append(incoming_que)
                
                if session.current_question >= 5:
                    final_score = session.score
                    session.score = final_score / 5
                    print(f"Novo score do usuário {session.nome}: {session.score}")
                    
                    service.criar_ou_atualizar_csv(
                        session.diretorio + "/Entrevista_Técnica_" + session.cpf,
                        session.questions,
                        session.answers,
                        session.notas,
                        session.correction
                    )
                    
                    bot_resp = MessagingResponse()
                    msg = bot_resp.message()
                    msg.body("Entrevista Finalizada! Agora precisamos que nos envie por aqui mesmo um vídeo se apresentando, falando um pouco sobre si")
                    session.fase += 1
                    return str(bot_resp)
                
                next_question = Fase3.gerar_pergunta(user_data.role, session.questions, client)
                session.questions.append(next_question)
                session.current_question += 1
                
                bot_resp = MessagingResponse()
                msg = bot_resp.message()
                msg.body(next_question)
                return str(bot_resp)
                
        elif session.fase == 5:
            texto_transcrito = Fase2.transcreveTexto("video/video.mp4")
            emocao = Fase2.extraiEmocao(texto_transcrito)
            resultado = Fase2.gerarScoreEAvaliacao(session.perfilComportamental, texto_transcrito, emocao)
            
            bot_resp = MessagingResponse()
            msg = bot_resp.message()
            msg.body("Prontinho! Agora é só aguardar!")
            return str(bot_resp)
        
# Periodic cleanup task (can be run in a separate thread)
def cleanup_task():
    while True:
        session_manager.cleanup_old_sessions()
        time.sleep(300)  # Run every 5 minutes

from threading import Thread
cleanup_thread = Thread(target=cleanup_task, daemon=True)
cleanup_thread.start()
if __name__ == '__main__':
    app.run(debug=True, port=5000)