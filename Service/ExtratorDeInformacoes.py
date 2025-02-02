import json
import os
from typing import Dict, Any, List
from langchain.tools import Tool
from langchain_anthropic import ChatAnthropic
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

class ValidadorUsuario:
    def __init__(self, client: ChatAnthropic):
        self.client = client
        self.campos_obrigatorios = [
            "nome", 
            "vaga_candidatura", 
            "experiencia_profissional", 
            "formacao_profissional"
        ]

    def validar_campos(self, dados_usuario: Dict[str, Any]) -> Dict[str, Any]:
        """
        Valida os campos do usuário e identifica os faltantes
        """
        campos_faltando = [
            campo for campo in self.campos_obrigatorios 
            if not dados_usuario.get(campo)
        ]

        if not campos_faltando:
            return {
                "status": "sucesso",
                "mensagem": "Todos os campos preenchidos",
                "dados": dados_usuario
            }

        prompt_faltantes = self.gerar_prompt_campos_faltantes(campos_faltando)

        return {
            "status": "pendente",
            "mensagem": "Campos incompletos",
            "campos_faltando": campos_faltando,
            "prompt_complementar": prompt_faltantes
        }

    def gerar_prompt_campos_faltantes(self, campos_faltando: List[str]) -> str:
        """
        Gera um prompt personalizado para solicitar campos faltantes
        """
        mensagens_campos = {
            "nome": "Por favor, informe seu nome completo.",
            "vaga_candidatura": "Para qual vaga você está se candidatando?",
            "experiencia_profissional": "Descreva uma experiência profissional relevante do seu currículo.",
            "formacao_profissional": "Qual é sua formação profissional mais recente?"
        }

        prompt = "Alguns campos importantes estão faltando no seu perfil:\n\n"
        for campo in campos_faltando:
            prompt += f"- {mensagens_campos.get(campo, 'Campo não identificado')}\n"
        
        prompt += "\nPor favor, complete as informações faltantes para prosseguir com sua candidatura."
        
        return prompt

    def complementar_informacoes(self, dados_usuario: Dict[str, Any], resposta_usuario: str) -> Dict[str, Any]:
        """
        Complementa as informações do usuário com a nova resposta
        """
        informacoes_complementares = extrair_informacoes(self.client, resposta_usuario)
        
        dados_usuario.update({
            k: v for k, v in informacoes_complementares.items() 
            if v is not None
        })

        return self.validar_campos(dados_usuario)

# Ferramenta de extração utilizando LangChain Tools com Anthropic Claude
def extrair_informacoes(client: ChatAnthropic, texto: str) -> Dict[str, Any]:
    """
    Extrai informações do texto chamando o modelo Claude via API
    """
    tool = Tool(
        name="extrair_informacoes",
        description="Extrai informações do texto fornecido sobre nome, vaga, experiência e formação",
        func=lambda x: client.invoke(x).content if hasattr(client.invoke(x), 'content') else str(client.invoke(x))
    )
    
    prompt = f"""
    Extraia do seguinte texto as seguintes informações: nome, vaga de candidatura, experiência profissional e formação profissional.
    
    Texto: {texto}
    
    Responda em formato JSON válido. Se alguma informação não estiver presente, defina como null.
    
    Exemplo de resposta:
    {{
        "nome": "João Silva",
        "vaga_candidatura": "Desenvolvedor Python",
        "experiencia_profissional": null,
        "formacao_profissional": "Bacharel em Ciência da Computação"
    }}
    """
    
    response = tool.run(prompt)
    
    try:
        return json.loads(response)
    except json.JSONDecodeError:
        return {"erro": "Falha ao processar resposta do Claude"}

def processar_usuario(client: ChatAnthropic, dados_usuario: Dict[str, Any], resposta_usuario: str = None):
    """
    Função principal de processamento no backend
    """
    validador = ValidadorUsuario(client)
    resultado = validador.validar_campos(dados_usuario)
    
    if resultado['status'] == 'sucesso':
        return resultado
    
    if resposta_usuario:
        return validador.complementar_informacoes(dados_usuario, resposta_usuario)
    
    return resultado
