import anthropic
import json
from typing import Dict, Any, List
import os
from dotenv import load_dotenv

load_dotenv()

class ValidadorUsuario:
    def __init__(self, client: anthropic.Anthropic):
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
        
        :param dados_usuario: Dicionário com informações do usuário
        :return: Dicionário com resultado da validação
        """
        # Campos faltantes
        campos_faltando = [
            campo for campo in self.campos_obrigatorios 
            if not dados_usuario.get(campo)
        ]

        # Se todos os campos estiverem presentes, retorna sucesso
        if not campos_faltando:
            return {
                "status": "sucesso",
                "mensagem": "Todos os campos preenchidos",
                "dados": dados_usuario
            }

        # Gera prompt para solicitar informações faltantes
        prompt_faltantes = self.gerar_prompt_campos_faltantes(campos_faltando)

        # Retorna resposta com campos faltantes
        return {
            "status": "pendente",
            "mensagem": "Campos incompletos",
            "campos_faltando": campos_faltando,
            "prompt_complementar": prompt_faltantes
        }

    def gerar_prompt_campos_faltantes(self, campos_faltando: List[str]) -> str:
        """
        Gera um prompt personalizado para solicitar campos faltantes
        
        :param campos_faltando: Lista de campos que faltam
        :return: Prompt para solicitação de informações
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
        
        :param dados_usuario: Dicionário com informações existentes
        :param resposta_usuario: Resposta do usuário com informações complementares
        :return: Dicionário atualizado com novas informações
        """
        # Gera prompt para extrair informações da resposta
        prompt = f"""
        Extraia do texto a seguir as seguintes informações:
        {self.gerar_prompt_extracao(dados_usuario)}

        Texto: {resposta_usuario}

        Responda em formato JSON válido. Use null para campos não encontrados.
        Exemplo de resposta:
        {{
            "nome": "João Silva",
            "vaga_candidatura": "Desenvolvedor Python",
            "experiencia_profissional": null,
            "formacao_profissional": null
        }}
        """

        try:
            # Envia prompt para o Claude
            response = self.client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=300,
                messages=[{"role": "user", "content": prompt}]
            )
            
            # Converte resposta para dicionário usando json.loads
            informacoes_complementares = json.loads(response.content[0].text)
            
            # Atualiza dados originais com novas informações
            dados_usuario.update({
                k: v for k, v in informacoes_complementares.items() 
                if v is not None
            })

            return self.validar_campos(dados_usuario)

        except Exception as e:
            return {
                "status": "erro",
                "mensagem": f"Erro ao processar informações: {str(e)}"
            }

    def gerar_prompt_extracao(self, dados_usuario: Dict[str, Any]) -> str:
        """
        Gera um prompt de extração considerando os campos já existentes
        
        :param dados_usuario: Dicionário com informações existentes
        :return: Prompt de extração personalizado
        """
        instrucoes = []
        
        if not dados_usuario.get("nome"):
            instrucoes.append("- Nome completo")
        
        if not dados_usuario.get("vaga_candidatura"):
            instrucoes.append("- Vaga de candidatura")
        
        if not dados_usuario.get("experiencia_profissional"):
            instrucoes.append("- Uma experiência profissional")
        
        if not dados_usuario.get("formacao_profissional"):
            instrucoes.append("- Formação profissional mais recente")
        
        return "\n".join(instrucoes)

def processar_usuario(client: anthropic.Anthropic, dados_usuario: Dict[str, Any], resposta_usuario: str = None):
    """
    Função principal de processamento no backend
    
    :param client: Cliente Anthropic
    :param dados_usuario: Dicionário com informações do usuário
    :param resposta_usuario: Resposta complementar do usuário (opcional)
    :return: Resultado do processamento
    """
    validador = ValidadorUsuario(client)
    
    # Primeira validação
    resultado = validador.validar_campos(dados_usuario)
    
    # Se todos os campos estiverem preenchidos, retorna sucesso
    if resultado['status'] == 'sucesso':
        return resultado
    
    # Se houver resposta complementar, tenta complementar informações
    if resposta_usuario:
        return validador.complementar_informacoes(dados_usuario, resposta_usuario)
    
    # Retorna campos faltantes
    return resultado

# # Exemplo de uso
# def main():
#     # Inicialização do cliente Anthropic
#     client = anthropic.Anthropic(api_key=os.getenv("CLAUDE_API_KEY"))
    
#     # Exemplo 1: Dados incompletos
#     dados_usuario1 = {
#         "nome": "João Silva"
#     }
    
#     resultado1 = processar_usuario(client, dados_usuario1)
#     print("Resultado 1:", resultado1)
    
#     # Exemplo 2: Complementando informações
#     resposta_usuario = "Estou me candidatando para Desenvolvedor Python na Empresa X"
#     resultado2 = processar_usuario(client, dados_usuario1, resposta_usuario)
#     print("Resultado 2:", resultado2)
#     resposta_usuario = "Já trabalhei na empresa CEMIG por 3 anos"
#     resultado3 = processar_usuario(client, dados_usuario1, resposta_usuario)
#     print("Resultado 2:", resultado3)
#     resposta_usuario = "Sou bacharel em Ciencia da computação"
#     resultado3 = processar_usuario(client, dados_usuario1, resposta_usuario)
#     print("Resultado 2:", resultado3)


# if __name__ == "__main__":
#     main()