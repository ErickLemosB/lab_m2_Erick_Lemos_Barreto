import json


def test_lab_json_e_valido():
    with open("lab.json", encoding="utf-8") as arquivo:
        dados = json.load(arquivo)
    assert dados["language"] == "python"
    assert dados["labs"] == ["m2.1", "m2.2"]
