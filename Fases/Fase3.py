import anthropic

def enviar_prompt_claude(prompt, client):
    message = client.messages.create(
    model="claude-3-haiku-20240307",
    max_tokens=1024,
    messages=[
        {"role": "user", "content": prompt}
    ]
    )
    return message.content[0].text

def gerar_pergunta(area, perguntas_anteriores, client):
    # Basta especificar uma área para obter perguntas.

    perguntas = ""
    for Perguntas in perguntas_anteriores:
        perguntas += Perguntas + "\n"


    prompt = f"""Gerar UMA, e apenas UMA, BREVE pergunta para uma entrevista técnica na área de {area}, lembre-se APENAS UMA PERGUNTA. Mantenha a pergunta concisa e específica. Importante: Escreva apenas a pergunta e nada mais. Gere perguntas diferentes, se as perguntas anteriores
     estiverem vazias é por que é a primeira pergunta que você está gerando, gere 1(uma) pergunta, suas perguntas anteriores foram:
              {perguntas}"""

    stream = enviar_prompt_claude(prompt, client)
    # pergunta = ""
    # for chunk in stream:
    #     pergunta += chunk
    return stream.strip()

def avaliar_resposta(pergunta, resposta_usuario, client):
    # Esse prompt precisa de mais trabalho para ficar melhor. Ainda não está muito bom
    prompt = f"""
    Pergunta: {pergunta}
    Resposta fornecida pelo candidato: {resposta_usuario}
    Você é um avaliador de uma empresa fictícia, conduzindo uma avaliação formal frente a frente com um candidato. Sua tarefa é avaliar a resposta do candidato em uma escala de 0 a 100, seguindo estas diretrizes:

Coerência e relevância:
Se a resposta do candidato não fizer sentido algum, fugir completamente do assunto, ou consistir em palavras/letras aleatórias (exemplo: "asdf", "123xyz"), ou for uma pergunta ou algo irrelevante, você deve atribuir nota 0, é muito importante atribuir a nota 0 nesses casos.
Erro no conteúdo:
Caso a resposta esteja errada, mas faça sentido no contexto, atribua uma nota proporcional à qualidade da resposta, sem ser 0.
Se o usuário se recusar a responder: se o usuário nao quiser responder, quiser pular a pergunta, e etc. Atribua a nota 1, é muito importante atribuir a nota 1 nesse caso.
Formato da resposta:
Forneça a avaliação em duas partes:
a) Nota numérica: Indique a nota atribuída como o único número presente na resposta.
b) Explicação textual: Justifique sua avaliação de forma clara e detalhada.

Exemplo de resposta formatada:
Nota: 70.
"Esta resposta contém alguns erros conceituais, mas está alinhada ao contexto da pergunta. "

Agora, avalie a resposta do candidato seguindo estas instruções.
    """
    stream = enviar_prompt_claude(prompt, client)
    
    print("RESPOSTA LLM: " + stream.strip())
    return stream.strip()

# usamos regex para extrair a nota.
# ainda dá para melhorar isso muito.
def extrair_nota(avaliacao):
    import re
    match = re.search(r'\b\d{1,3}\b', avaliacao)
    
    '''
    COMO ESSA REGEX FUNCIONA??

    r - raw string - trata casos de '\' dentro da string como chars literais, e não como uma sequencia de escape
    \b - garante que o caractere antes da expressao deve ser um espaço ou um \n
    \d - garante que todos os chars da expressao são digitos de 0 a 9
    {1,3} - expressão que procuramos tem tamanho de 1 a 3
    \b - final da expressão é um espaço ou \n.

    O que quebra a REGEX?

    Numeros soltos na resposta vão quebrar a regex. "A resposta está certa, pois existem 25 especies..." NOTA = 25.

    '''

    if match:
        return int(match.group())
    return 0  # não conseguimos achar a nota

# # placeholder. Ainda preciso estabelecer um limite de tamanho.
# area = input("Selecione uma área de conhecimento: ")
# total_nota = 0

# # numero de perguntas que serão feitas. Seria interessante deixar isso mais dinamico
# num_perguntas = 10

# # gera I perguntas de uma area X, pega a resposta, avalia, e extrai a nota.
# for i in range(num_perguntas):
#     print(f"\nPergunta {i+1}:")
#     pergunta = gerar_pergunta(area)
#     print(pergunta)
    
#     resposta_usuario = input("\nSua Resposta: ")
    
#     avaliacao = avaliar_resposta(pergunta, resposta_usuario)
#     print("\nAvaliação Final:\n")
#     print(avaliacao)
    
#     nota = extrair_nota(avaliacao)
#     total_nota += nota

# media_nota = total_nota / num_perguntas
# print(f"\nMédia Final das Notas: {media_nota:.2f}")