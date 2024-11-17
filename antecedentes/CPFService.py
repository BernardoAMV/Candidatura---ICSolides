'''
Script para validação de CPFs e testes de antecedentes criminais.

Leitura obrigatória: https://www.calculadorafacil.com.br/computacao/validar-cpf
'''
import re
import json

def validaCPF (cpf):
  cpf = re.sub(r'\D', '', cpf)
  if len(cpf) != 11:
    return False
  if cpf == cpf[0] * len(cpf):
    return False
  def calculate_check_digit(base):
    total = 0
    weight = len(base) + 1
    for digit in base:
      total += int(digit) * weight
      weight -= 1
    remainder = total % 11
    return 0 if remainder < 2 else 11 - remainder
  first_check_digit = calculate_check_digit(cpf[:9])
  if first_check_digit != int(cpf[9]):
    return False
  second_check_digit = calculate_check_digit(cpf[:10])
  if second_check_digit != int(cpf[10]):
    return False
  return True
  
def loadJSON(filename):
  with open(filename, 'r') as file:
    return json.load(file)
  
def saveJSON(filename, data):
  with open(filename, 'w') as file:
    json.dump(data, file, indent=4)
  
def possuiAntecedentes(CPFNUM, nomeDB):
  return bool(pesqBinaria(CPFNUM, loadJSON(nomeDB)))

def pesqBinaria(cpfnum, data):
  low = 0
  high = len(data) - 1
  while low <= high:
    mid = (low + high) // 2
    mid_cpf = data[mid]["CPFNUM"]
    if mid_cpf == cpfnum:
      return data[mid]["antecedente"]
    elif mid_cpf < cpfnum:
      low = mid + 1
    else:
      high = mid - 1
  return None
  
def addEntry(cpfnum, antecedente, data, filename):
  for entry in data:
    if entry["CPFNUM"] == cpfnum:
      print("CPFNUM already exists.")
      return
  data.append({"CPFNUM": cpfnum, "antecedente": antecedente})
  data.sort(key=lambda x: x["CPFNUM"])
  print(f"Entry added: {cpfnum}, antecedente: {antecedente}")
  data = sortByCPF(data)
  saveJSON(filename, data)
  
def removeEntry(cpfnum, data, filename):
  for entry in data:
    if entry["CPFNUM"] == cpfnum:
      data.remove(entry)
      print(f"Entry removed: {cpfnum}")
      return
  print("CPFNUM not found.")

def updateEntry(cpfnum, antecedente, data, filename):
  removeEntry(cpfnum, data, filename)
  addEntry(cpfnum, antecedente, data, filename)

def sortByCPF(data):
  if len(data) <= 1:
    return data
  else:
    pivot = data[len(data) // 2]["CPFNUM"]
    left = [x for x in data if x["CPFNUM"] < pivot]
    middle = [x for x in data if x["CPFNUM"] == pivot]
    right = [x for x in data if x["CPFNUM"] > pivot]
    return sortByCPF(left) + middle + sortByCPF(right)

def removeAllInvalids(data):
  valid_data = [entry for entry in data if is_valid_cpf(entry["CPFNUM"])]
  removed_count = len(data) - len(valid_data)
  print(f"Removed {removed_count} invalid CPF(s).")
  return valid_data

def formataString(input_string):
  numeric_string = ''.join(filter(str.isdigit, input_string))
  if len(numeric_string) < 11:
      numeric_string = numeric_string.zfill(11)
  else:
      numeric_string = numeric_string[:11]
  return numeric_string

# EXEMPLO DE USO:
# 
# print(pesqBinaria("36145585927", sortByCPF(loadJSON("banco_de_CPF.json"))))