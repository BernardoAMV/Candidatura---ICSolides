import pandas as pd

# Lista de usuários com os atributos da classe Pessoa
data = {
    "name": ["João", "Maria", "Carlos", "Ana", "Paulo", "Fernanda", "Roberto", "Juliana", "Luís", "Clara"],
    "cpf": ["123.456.789-00", "234.567.890-11", "345.678.901-22", "456.789.012-33", "567.890.123-44", 
            "678.901.234-55", "789.012.345-66", "890.123.456-77", "901.234.567-88", "012.345.678-99"],
    "role": ["Desenvolvedor", "Gerente", "Analista de Dados", "Designer", "Engenheiro", 
             "Cientista de Dados", "Desenvolvedor", "Analista de Sistemas", "Administrador", "Recursos Humanos"],
    "experiences": [
        '[{"cargo": "Desenvolvedor Júnior", "empresa": "Empresa A", "tempo_de_casa": "1 ano"}, '
        '{"cargo": "Desenvolvedor Pleno", "empresa": "Empresa B", "tempo_de_casa": "2 anos"}]',
        
        '[{"cargo": "Gerente de Projetos", "empresa": "Empresa C", "tempo_de_casa": "3 anos"}]',
        
        '[{"cargo": "Analista de Dados Júnior", "empresa": "Empresa D", "tempo_de_casa": "1 ano"}, '
        '{"cargo": "Analista de Dados Pleno", "empresa": "Empresa E", "tempo_de_casa": "2 anos"}]',
        
        '[{"cargo": "Designer Gráfico", "empresa": "Empresa F", "tempo_de_casa": "5 anos"}]',
        
        '[{"cargo": "Engenheiro de Software", "empresa": "Empresa G", "tempo_de_casa": "4 anos"}]',
        
        '[{"cargo": "Cientista de Dados Júnior", "empresa": "Empresa H", "tempo_de_casa": "1 ano"}]',
        
        '[{"cargo": "Desenvolvedor Sênior", "empresa": "Empresa I", "tempo_de_casa": "3 anos"}, '
        '{"cargo": "Desenvolvedor Pleno", "empresa": "Empresa J", "tempo_de_casa": "2 anos"}]',
        
        '[{"cargo": "Analista de Sistemas", "empresa": "Empresa K", "tempo_de_casa": "2 anos"}]',
        
        '[{"cargo": "Administrador", "empresa": "Empresa L", "tempo_de_casa": "3 anos"}]',
        
        '[{"cargo": "Recursos Humanos", "empresa": "Empresa M", "tempo_de_casa": "2 anos"}]'
    ],
    "degree": ["Bacharel em Engenharia", "Técnico em Administração", "Bacharel em Ciência da Computação", 
               "Bacharel em Design Gráfico", "Bacharel em Engenharia Civil", "Mestre em Matemática", 
               "Doutor em Sistemas de Informação", "Bacharel em Ciência da Computação", 
               "Bacharel em Administração", "Bacharel em Psicologia"],
    "exigences": [
        "Senior, 5 anos de experiência, Bacharel em Engenharia",
        "Junior, 1 ano de experiência, Técnico em Administração",
        "Pleno, 3 anos de experiência, Bacharel em Ciência da Computação",
        "Senior, 6 anos de experiência, Bacharel em Design Gráfico",
        "Pleno, 4 anos de experiência, Bacharel em Engenharia Civil",
        "Junior, 2 anos de experiência, Mestre em Matemática",
        "Senior, 7 anos de experiência, Doutor em Sistemas de Informação",
        "Pleno, 3 anos de experiência, Bacharel em Ciência da Computação",
        "Junior, 1 ano de experiência, Bacharel em Administração",
        "Pleno, 4 anos de experiência, Bacharel em Psicologia"
    ]
}

# Criando um DataFrame com os dados
df = pd.DataFrame(data)

# Adicionando a coluna 'score' com o valor 50 para todos os usuários
df['score'] = 50

# Salvando o DataFrame como um arquivo CSV
df.to_csv("DB.csv", index=False)

print("Arquivo CSV criado com sucesso com a coluna 'score'!")
