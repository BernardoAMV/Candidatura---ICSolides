import ollama
import whisper
import warnings

warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", message="FP16 is not supported on CPU; using FP32 instead")

questions = {
    "EI": [
        "Você gosta de participar de eventos sociais com muitas pessoas?",
        "Você prefere passar tempo sozinho ou com um pequeno grupo de amigos próximos?",
        "Você se sente energizado quando interage com outras pessoas?",
        "Você costuma evitar grandes encontros e prefere atividades mais solitárias?"
    ],
    "SN": [
        "Você se concentra mais em fatos e detalhes do que em teorias ou ideias?",
        "Você prefere pensar no quadro geral e em conceitos abstratos, ao invés de se ater aos detalhes?",
        "Você confia mais em suas observações diretas do que em suas intuições?",
        "Você gosta de explorar possibilidades futuras em vez de se focar no que é concreto e tangível?"
    ],
    "TF": [
        "Você toma decisões com base na lógica e consistência, em vez de nas emoções pessoais?",
        "Você prioriza seus sentimentos e valores pessoais ao tomar decisões?",
        "Você acredita que as decisões devem ser objetivas e baseadas em fatos?",
        "Você tende a considerar como as decisões afetarão as pessoas ao seu redor?"
    ],
    "JP": [
        "Você prefere ter um plano e segui-lo rigorosamente?",
        "Você gosta de manter suas opções em aberto e ser flexível?",
        "Você se sente mais confortável quando tem um cronograma ou uma lista de tarefas?",
        "Você prefere reagir às circunstâncias à medida que elas surgem, em vez de planejar com antecedência?"
    ]
}

scores = {
    "EI": 0,  # Extroversão (E) vs. Introversão (I)
    "SN": 0,  # Sensação (S) vs. Intuição (N)
    "TF": 0,  # Pensamento (T) vs. Sentimento (F)
    "JP": 0   # Julgamento (J) vs. Percepção (P)
}

dimensionGrab = 0
iGrab= 0

# Retorna questoes de forma lazy
def nextQuestion():
    global dimensionGrab, iGrab

    question_dimensions = list(questions.items())
    if dimensionGrab < len(question_dimensions):
        dimension_key, dimension_questions = question_dimensions[dimensionGrab]
        if iGrab < len(dimension_questions):
            question = dimension_questions[iGrab]
            output = f"Q{iGrab+1}: {question} (1-5)"
            iGrab += 1
            return output
        else:
            dimensionGrab += 1
            iGrab = 0
            return nextQuestion()
    else:
        return "All questions completed."
    
def grabResposta(response):
    if response >= 4: 
        if iGrab % 2 == 0: # basicamente, perguntas de numero par reforçam um perfil (extroversão)
            scores[dimensionGrab] += 1
        else:          # e perguntas de numero impar reforçam o anti-perfil (introversão)
            scores[dimensionGrab] -= 1

def getResultado():

    # calcular os percentuais, fonte: 16personalities
    results = {
        "Extroversão (E)": max(0, scores["EI"] / len(questions["EI"]) * 100),
        "Introversão (I)": max(0, (-scores["EI"]) / len(questions["EI"]) * 100),
        "Sensação (S)": max(0, scores["SN"] / len(questions["SN"]) * 100),
        "Intuição (N)": max(0, (-scores["SN"]) / len(questions["SN"]) * 100),
        "Pensamento (T)": max(0, scores["TF"] / len(questions["TF"]) * 100),
        "Sentimento (F)": max(0, (-scores["TF"]) / len(questions["TF"]) * 100),
        "Julgamento (J)": max(0, scores["JP"] / len(questions["JP"]) * 100),
        "Percepção (P)": max(0, (-scores["JP"]) / len(questions["JP"]) * 100)
    }

    # mostrar o resultado em percentuais
    print("\nResultados do MBTI (em percentuais):")
    resultadoMBTI = ""
    for trait, percentage in results.items():
        resultadoMBTI += f"{trait}: {percentage:.2f}%"
    mbti_profile = ", ".join([f"{trait}: {percentage:.2f}%" for trait, percentage in results.items()])
    return mbti_profile

def transcreveTexto(pathDoVideo):
    model = whisper.load_model("base") 
    result = model.transcribe(pathDoVideo)
    transcribed_text = result["text"]
    return transcribed_text

def extraiEmocao(textoTranscrito):
    stream = ollama.chat(
        model='llama3.2',
        messages=[{'role': 'user', 'content': ("Analise o sentimento do seguinte texto: " + textoTranscrito)}],
        stream=True,
    )
    #print("\nAnálise de Sentimento:")
    sentiment_analysis = ""
    for chunk in stream:
        sentiment_analysis += chunk['message']['content']
    #print(sentiment_analysis)
    return sentiment_analysis


def gerarScoreEAvaliacao(testeMBTI, textoTranscrito, analiseSentimento):
    final_prompt = f"""
    Forneça uma breve análise do perfil cultural do candidato com base nos seguintes resultados:
    1. Perfil MBTI (percentuais):
    {testeMBTI}
    2. Transcrição da Entrevista:
    {textoTranscrito}
    3. Análise de Sentimento:
    {analiseSentimento}

    Leve em conta o perfil comportamental e o tom utilizado durante a entrevista para fornecer insights sobre o estilo de trabalho e adaptação cultural deste candidato.
    """

    stream = ollama.chat(
        model='llama3.2',
        messages=[{'role': 'user', 'content': final_prompt}],
        stream=True,
    )

    # Análise do perfil cultural. Ultima etapa da fase 2.
    print("\nAnálise Final do Perfil Cultural:")

    mensagemFinal = ""

    for chunk in stream:
        mensagemFinal += chunk['message']['content']
    # Agora basta passar a mensagemFinal para o recrutador, ou implementar uma heuristica para dar uma nota a essa avaliação.
    return mensagemFinal


