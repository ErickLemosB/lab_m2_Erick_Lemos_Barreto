import os

import cv2
import numpy as np


class ErroPdi(Exception):
    """caso tenha alg erro de entrada ou formato."""


# No Windows, o OpenCV pode ter problemas para abrir ou salvar arquivos em caminhos com acentos.
# Para evitar isso, leio os bytes com o NumPy e deixo o OpenCV decodificar a imagem.
def ler_imagem(caminho, flags=cv2.IMREAD_COLOR):
    if not os.path.isfile(caminho):
        raise ErroPdi("arquivo de input não encontrado: %s" % caminho)
    imagem = cv2.imdecode(np.fromfile(caminho, dtype=np.uint8), flags)
    if imagem is None:
        raise ErroPdi("erro ao abrir a imagem %s" % caminho)
    return imagem


def gravar_imagem(imagem, caminho):
    try:
        pasta = os.path.dirname(caminho)
        if pasta:
            os.makedirs(pasta, exist_ok=True)
        ok, dados = cv2.imencode(os.path.splitext(caminho)[1], imagem)
        if not ok:
            raise ErroPdi("não foi possível codificar %s" % caminho)
        dados.tofile(caminho)
    except (OSError, cv2.error) as erro:
        raise ErroPdi("falha ao salvar a imagem %s (%s)" % (caminho, erro))


# Para a máscara estar correta, ela precisa ter um canal, usar uint8 e conter só 0 (fundo) ou 255 (primeiro plano).
def verificar_mascara(mascara, altura=None, largura=None):
    if mascara.ndim != 2:
        raise ErroPdi("a máscara deve ter um único canal")
    if mascara.dtype != np.uint8:
        raise ErroPdi("a máscara deve ser uint8 (é %s)" % mascara.dtype)
    if altura is not None and mascara.shape != (altura, largura):
        raise ErroPdi("a máscara não tem o mesmo tamanho da imagem")
    if not set(np.unique(mascara).tolist()) <= {0, 255}:
        raise ErroPdi("a máscara não é binária: tem valores fora de {0, 255}")


# Se a máscara tiver outros valores além de 0 e 255, eu prefiro dar erro em vez de converter tudo para binário automaticamente.def ler_mascara(caminho, altura=None, largura=None):
    mascara = ler_imagem(caminho, cv2.IMREAD_UNCHANGED)
    verificar_mascara(mascara, altura, largura)
    return mascara
