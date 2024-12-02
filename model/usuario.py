import json


class user :
    def __init__(self,name=None,cpf=None,role=None,experiences=None,degree=None, exigences=None, score=50):
        self.name = name
        self.cpf = cpf
        self.role = role
        self.experiences = experiences
        self.degree = degree
        self.exigences = exigences
        self.score = score

    def to_string(self):
        return (f"Name: {self.name}\n"
                f"CPF: {self.cpf}\n"
                f"Role: {self.role}\n"
                f"Experiences: {self.experiences}\n"
                f"Degree: {self.degree}\n"
                f"Exigences: {self.exigences}"
                f"Score: {self.score}")   
    def to_json(self):
        # Converte o objeto para um dicionário
        person_dict = {
            "name": self.name,
            "cpf": self.cpf,
            "role": self.role,
            "experiences": self.experiences,
            "degree": self.degree,
            "exigences": self.exigences,
            "score": self.score,
        }
        # Retorna o dicionário como uma string JSON
        return json.dumps(person_dict, indent=4)
    def to_dict(self):
        return {
            "name": self.name,
            "cpf": self.cpf,
            "role": self.role,
            "experiences": self.experiences,
            "degree": self.degree,
            "exigences": self.exigences,
            "score": self.score,
        }