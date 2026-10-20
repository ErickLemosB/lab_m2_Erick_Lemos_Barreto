import csv
import json

import numpy as np
import pytest

from pdi_lab.__main__ import main
from pdi_lab.componentes import aplicar_etapa, ler_sequencia, rotular
from pdi_lab.imagem import ErroPdi, gravar_imagem, ler_mascara


def analyze(entrada, prefixo, *extras):
    return main(["--input", str(entrada), "--output", str(prefixo), "--operation", "analyze", *extras])


def salvar(tmp_path, mascara):
    caminho = tmp_path / "mask.png"
    gravar_imagem(mascara, str(caminho))
    return caminho


def contar(mascara, conectividade):
    return len(rotular(mascara, conectividade, 0)[1])


def test_pixels_na_diagonal_4_contra_8():
    mascara = np.zeros((4, 4), dtype=np.uint8)
    mascara[1, 1] = 255
    mascara[2, 2] = 255
    assert contar(mascara, 4) == 2
    assert contar(mascara, 8) == 1


def test_abertura_remove_ruido_e_mantem_regiao():
    mascara = np.zeros((20, 20), dtype=np.uint8)
    mascara[5:15, 5:15] = 255
    mascara[1, 18] = 255  # ruído isolado
    aberta = aplicar_etapa(mascara, {"operacao": "open", "forma": "rect", "tamanho": 3, "iteracoes": 1})
    assert contar(aberta, 8) == 1
    assert np.count_nonzero(aberta) == 100


def test_fechamento_preenche_furo():
    mascara = np.zeros((15, 15), dtype=np.uint8)
    mascara[3:12, 3:12] = 255
    mascara[7, 7] = 0
    fechada = aplicar_etapa(mascara, {"operacao": "close", "forma": "rect", "tamanho": 3, "iteracoes": 1})
    assert np.count_nonzero(fechada) == 81


def test_objeto_na_borda():
    mascara = np.zeros((10, 10), dtype=np.uint8)
    mascara[0:5, 0:5] = 255
    _, componentes = rotular(mascara, 8, 0)
    assert (componentes[0]["x"], componentes[0]["y"], componentes[0]["area"]) == (0, 0, 25)
    erodida = aplicar_etapa(mascara, {"operacao": "erode", "forma": "rect", "tamanho": 3, "iteracoes": 1})
    assert np.count_nonzero(erodida) == 16  # só os lados internos perdem 1 pixel


def test_filtro_de_area_e_fundo_fora():
    mascara = np.zeros((20, 20), dtype=np.uint8)
    mascara[0, 0] = 255
    mascara[10:15, 10:15] = 255
    _, componentes = rotular(mascara, 8, 2)
    assert [(c["label"], c["area"], c["kept"]) for c in componentes] == [(1, 1, 0), (2, 25, 1)]
    assert (componentes[1]["cx"], componentes[1]["cy"]) == (12.0, 12.0)


@pytest.mark.parametrize("texto", ["open:ellipse:3", "blur:rect:3:1", "open:circle:3:1", "open:rect:0:1"])
def test_sequencia_invalida(texto):
    with pytest.raises(ErroPdi):
        ler_sequencia(texto)


def test_mascara_vazia(tmp_path):
    assert analyze(salvar(tmp_path, np.zeros((10, 10), dtype=np.uint8)), tmp_path / "v") == 0
    resumo = json.loads((tmp_path / "v_resumo.json").read_text(encoding="utf-8"))
    assert resumo["antes"]["brutos"] == 0 and resumo["depois"]["area_primeiro_plano"] == 0
    assert (tmp_path / "v_componentes_final.csv").read_text(encoding="utf-8").strip() == "label,area,x,y,width,height,cx,cy,kept"


@pytest.mark.parametrize("mascara", [np.array([[0, 100], [255, 0]], dtype=np.uint8), np.zeros((5, 5, 3), dtype=np.uint8)])
def test_recusa_mascara_invalida(tmp_path, mascara):
    assert analyze(salvar(tmp_path, mascara), tmp_path / "r") == 1


def test_min_area_negativa_e_conectividade_invalida(tmp_path):
    entrada = salvar(tmp_path, np.zeros((5, 5), dtype=np.uint8))
    assert analyze(entrada, tmp_path / "r", "--min-area", "-1") == 1
    with pytest.raises(SystemExit) as saida:
        analyze(entrada, tmp_path / "r", "--connectivity", "6")
    assert saida.value.code == 2


def test_erros_de_leitura_e_gravacao(tmp_path):
    assert analyze(tmp_path / "nao_existe.png", tmp_path / "r") == 1
    arquivo = tmp_path / "arquivo_comum"
    arquivo.write_text("x")
    entrada = salvar(tmp_path, np.zeros((5, 5), dtype=np.uint8))
    assert analyze(entrada, arquivo / "r") == 1  # pasta dentro de um arquivo


@pytest.mark.parametrize("imagem", ["images/input/tampas_papel_branco.webp", "images/input/tampas_papel_amassado.webp"])
def test_imagens_reais_segment_e_analyze(tmp_path, imagem):
    mascara = tmp_path / "hsv.png"
    assert main(["--input", imagem, "--output", str(mascara), "--operation", "segment",
                 "--method", "hsv", "--hsv-min", "95,120,30", "--hsv-max", "130,255,255"]) == 0
    prefixo = str(tmp_path / "t")
    assert analyze(mascara, prefixo, "--min-area", "1000") == 0

    resumo = json.loads(open(prefixo + "_resumo.json", encoding="utf-8").read())
    for nome in ("0_inicial", "1_open", "2_close"):
        ler_mascara(prefixo + "_mask_%s.png" % nome)  # intermediárias gravadas e binárias

    for csv_nome, medidas in (("inicial", resumo["antes"]), ("final", resumo["depois"])):
        with open(prefixo + "_componentes_%s.csv" % csv_nome, encoding="utf-8") as arquivo:
            linhas = list(csv.DictReader(arquivo))
        # soma das áreas brutas = pixels de primeiro plano da máscara
        assert sum(int(l["area"]) for l in linhas) == medidas["area_primeiro_plano"]
        assert all(int(l["label"]) >= 1 for l in linhas)
        assert all(l["kept"] == str(int(int(l["area"]) >= 1000)) for l in linhas)
        assert sum(int(l["kept"]) for l in linhas) == medidas["filtrados"]
