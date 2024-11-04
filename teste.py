import requests

hasAntecedentes = False
url = "https://api.exato.digital/br/policia-civil/mg/antecedentes-criminais?"
payload = {
'rg': '19800380',
 'nome_completo': 'Bernardo Augusto Amorim Vieira',
'data_nascimento': '15032005'
 }
response = requests.post(url, json=payload)

print(response.json())