import ollama

def gerar_pergunta(area):
    # Basta especificar uma área para obter perguntas.
    prompt = f"Gerar uma BREVE pergunta para uma entrevista técnica na área de {area}. Mantenha a pergunta concisa e específica. Importante: Escreva apenas a pergunta e nada mais."

    stream = ollama.chat(
        model='llama3.2',
        messages=[{'role': 'user', 'content': prompt}],
        stream=True,
    )
    pergunta = ""
    for chunk in stream:
        pergunta += chunk['message']['content']
    return pergunta.strip()

def avaliar_resposta(pergunta, resposta_usuario):
    # Esse prompt precisa de mais trabalho para ficar melhor. Ainda não está muito bom
    prompt = f"""
    Pergunta: {pergunta}
    Resposta fornecida pelo candidato: {resposta_usuario}
    Você trabalha como avaliador em uma empresa imaginária e está tendo uma conversa formal, frente a frente com um candidato.
    Avalie a correção da resposta do candidato em uma escala de 1 a 100, e apenas isso. Caso a resposta fuja do assunto ou não tenha sentido nenhum com a pergunta, peça para o usuário responder novamente. 
    Não justifique sua avaliação.
    Seja direto, apenas diga que não compreendeu a resposta e peça para o candidato responder novamente. Não ajude o candidato a responder, você esta o avaliando.
    """
    stream = ollama.chat(
        model='llama3.2',
        messages=[{'role': 'user', 'content': prompt}],
        stream=True,
    )
    avaliacao = ""
    for chunk in stream:
        avaliacao += chunk['message']['content']
    
    print("RESPOSTA LLM: " + avaliacao.strip())
    return avaliacao.strip()

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