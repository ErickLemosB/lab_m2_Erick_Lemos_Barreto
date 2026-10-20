import cv2
import numpy as np
import pytest

from pdi_lab.__main__ import main
from pdi_lab.imagem import ErroPdi, gravar_imagem, ler_mascara, verificar_mascara
from pdi_lab.segmentacao import faixa_hsv, limiar_fixo


def segment(entrada, saida, *extras):
    return main(["--input", str(entrada), "--output", str(saida), "--operation", "segment", *extras])


def cinza_bgr(valores):
    return cv2.cvtColor(np.array([valores], dtype=np.uint8), cv2.COLOR_GRAY2BGR)


def test_limiar_fixo_abaixo_igual_acima():
    # regra do OpenCV: só pixel > T vira primeiro plano
    assert limiar_fixo(cinza_bgr([119, 120, 121]), 120).tolist() == [[0, 0, 255]]
    assert limiar_fixo(cinza_bgr([119, 120, 121]), 120, inverter=True).tolist() == [[255, 255, 0]]


def test_limiar_fixo_pela_cli(tmp_path):
    entrada = tmp_path / "tres.png"
    gravar_imagem(np.array([[119, 120, 121]], dtype=np.uint8), str(entrada))
    assert segment(entrada, tmp_path / "m.png", "--method", "fixed", "--threshold", "120") == 0
    assert ler_mascara(str(tmp_path / "m.png")).tolist() == [[0, 0, 255]]


def test_hsv_pega_so_o_azul():
    hsv = np.array([[[110, 220, 150], [15, 80, 120], [110, 20, 210]]], dtype=np.uint8)  # azul, papel pardo, papel branco
    bgr = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)
    assert faixa_hsv(bgr, (95, 120, 30), (130, 255, 255)).tolist() == [[255, 0, 0]]


@pytest.mark.parametrize("mascara", [
    np.array([[0, 128]], dtype=np.uint8),    # valor fora de {0, 255}
    np.zeros((1, 2, 3), dtype=np.uint8),     # 3 canais
    np.zeros((2, 2), dtype=np.uint8),        # tamanho diferente
])
def test_verificar_mascara_recusa_invalidas(mascara):
    with pytest.raises(ErroPdi):
        verificar_mascara(mascara, 1, 2)


CONFIGURACOES = [
    ["--method", "fixed", "--threshold", "100", "--invert"],
    ["--method", "hsv", "--hsv-min", "95,120,30", "--hsv-max", "130,255,255"],
]


@pytest.mark.parametrize("imagem", ["images/input/tampas_papel_branco.webp", "images/input/tampas_papel_amassado.webp"])
@pytest.mark.parametrize("parametros", CONFIGURACOES)
def test_imagens_reais_geram_mascara_valida(tmp_path, imagem, parametros):
    assert segment(imagem, tmp_path / "m.png", *parametros, "--overlay", str(tmp_path / "ov.png")) == 0
    original = cv2.imread(imagem)
    mascara = cv2.imread(str(tmp_path / "m.png"), cv2.IMREAD_UNCHANGED)
    assert mascara.ndim == 2
    assert mascara.shape == original.shape[:2]
    assert set(np.unique(mascara).tolist()) == {0, 255}
    assert (tmp_path / "ov.png").is_file()


def test_arquivo_inexistente(tmp_path):
    assert segment("images/input/nao_existe.png", tmp_path / "m.png", "--method", "fixed", "--threshold", "10") == 1


def test_arquivo_que_nao_e_imagem(tmp_path):
    falso = tmp_path / "falso.png"
    falso.write_text("não é imagem")
    assert segment(falso, tmp_path / "m.png", "--method", "fixed", "--threshold", "10") == 1


def test_metodo_desconhecido(tmp_path):
    with pytest.raises(SystemExit) as saida:
        segment("images/input/tampas_papel_branco.webp", tmp_path / "m.png", "--method", "otsu")
    assert saida.value.code == 2


@pytest.mark.parametrize("parametros", [
    [],                                                       # sem --method
    ["--method", "fixed"],                                    # sem --threshold
    ["--method", "fixed", "--threshold", "300"],
    ["--method", "hsv", "--hsv-min", "95,120,30"],            # sem --hsv-max
    ["--method", "hsv", "--hsv-min", "95,120,30", "--hsv-max", "200,255,255"],
    ["--method", "hsv", "--hsv-min", "130,120,30", "--hsv-max", "95,255,255"],
])
def test_parametros_invalidos(tmp_path, parametros):
    assert segment("images/input/tampas_papel_branco.webp", tmp_path / "m.png", *parametros) == 1
    assert not (tmp_path / "m.png").exists()


def test_mascara_precisa_ser_png(tmp_path):
    assert segment("images/input/tampas_papel_branco.webp", tmp_path / "m.jpg",
                   "--method", "fixed", "--threshold", "100") == 1
