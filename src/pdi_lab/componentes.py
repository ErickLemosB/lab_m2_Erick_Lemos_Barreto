import csv
import json

import cv2
import numpy as np

from .imagem import ErroPdi, gravar_imagem, ler_mascara

OPERACOES_MORF = {
    "open": cv2.MORPH_OPEN,
    "close": cv2.MORPH_CLOSE,
    "erode": cv2.MORPH_ERODE,
    "dilate": cv2.MORPH_DILATE,
}
FORMAS = {"rect": cv2.MORPH_RECT, "ellipse": cv2.MORPH_ELLIPSE}


# Exemplo: "open:ellipse:5:1,close:ellipse:9:1" representa duas etapas morfológicas que eu separo em uma lista.
def ler_sequencia(texto):
    etapas = []
    for item in texto.split(","):
        partes = item.split(":")
        if len(partes) != 4:
            raise ErroPdi("etapa inválida '%s' (use operacao:forma:tamanho:iteracoes)" % item)
        operacao, forma, tamanho, iteracoes = partes
        if operacao not in OPERACOES_MORF or forma not in FORMAS:
            raise ErroPdi("operação ou forma desconhecida em '%s'" % item)
        if not tamanho.isdigit() or not iteracoes.isdigit() or int(tamanho) < 1 or int(iteracoes) < 1:
            raise ErroPdi("tamanho e iterações devem ser inteiros >= 1 em '%s'" % item)
        etapas.append({"operacao": operacao, "forma": forma, "tamanho": int(tamanho), "iteracoes": int(iteracoes)})
    return etapas


def aplicar_etapa(mascara, etapa):
    elemento = cv2.getStructuringElement(FORMAS[etapa["forma"]], (etapa["tamanho"], etapa["tamanho"]))
    # Com o preenchimento de borda padrão do OpenCV, a erosão não remove o objeto só porque ele encosta na borda da imagem.
    return cv2.morphologyEx(mascara, OPERACOES_MORF[etapa["operacao"]], elemento, iterations=etapa["iteracoes"])


def rotular(mascara, conectividade, area_minima):
    quantidade, rotulos, stats, centroides = cv2.connectedComponentsWithStats(mascara, connectivity=conectividade)
    componentes = []
    for rotulo in range(1, quantidade):  # rótulo 0 é o fundo
        x, y, largura, altura, area = (int(v) for v in stats[rotulo])
        componentes.append({
            "label": rotulo, "area": area, "x": x, "y": y, "width": largura, "height": altura,
            "cx": round(float(centroides[rotulo][0]), 2), "cy": round(float(centroides[rotulo][1]), 2),
            "kept": int(area >= area_minima),
        })
    return rotulos, componentes


def medir(mascara, conectividade, area_minima):
    _, componentes = rotular(mascara, conectividade, area_minima)
    return {
        "area_primeiro_plano": int(np.count_nonzero(mascara)),
        "componentes_4": len(rotular(mascara, 4, area_minima)[1]),
        "componentes_8": len(rotular(mascara, 8, area_minima)[1]),
        "brutos": len(componentes),
        "filtrados": sum(c["kept"] for c in componentes),
    }


# Mostro os componentes que passaram no filtro com cores e caixas delimitadoras; os que foram removidos ficam em cinza.
def colorir(rotulos, componentes):
    cores = np.zeros((len(componentes) + 1, 3), dtype=np.uint8)
    for c in componentes:
        n = c["label"]
        if c["kept"]:
            # Calculo a cor a partir do número do rótulo para que ela seja sempre a mesma, sem depender de valores aleatórios.
            cores[n] = ((n * 67) % 196 + 60, (n * 131) % 196 + 60, (n * 199) % 196 + 60)
        else:
            cores[n] = (90, 90, 90)
    imagem = cores[rotulos]
    for c in componentes:
        if c["kept"]:
            cv2.rectangle(imagem, (c["x"], c["y"]), (c["x"] + c["width"] - 1, c["y"] + c["height"] - 1), (255, 255, 255), 2)
    return imagem


def escrever_csv(componentes, caminho):
    try:
        with open(caminho, "w", encoding="utf-8", newline="") as arquivo:
            escritor = csv.DictWriter(arquivo, fieldnames=["label", "area", "x", "y", "width", "height", "cx", "cy", "kept"])
            escritor.writeheader()
            escritor.writerows(componentes)
    except OSError as erro:
        raise ErroPdi("falha ao gravar %s (%s)" % (caminho, erro))


def analisar(entrada, prefixo, conectividade, area_minima, texto_morfologia):
    etapas = ler_sequencia(texto_morfologia)
    inicial = ler_mascara(entrada)

# Mantenho a máscara original intacta e salvo o resultado de cada etapa em um arquivo separado.    gravar_imagem(inicial, prefixo + "_mask_0_inicial.png")
    final = inicial
    for numero, etapa in enumerate(etapas, start=1):
        final = aplicar_etapa(final, etapa)
        gravar_imagem(final, "%s_mask_%d_%s.png" % (prefixo, numero, etapa["operacao"]))

    _, componentes_inicial = rotular(inicial, conectividade, area_minima)
    rotulos_final, componentes_final = rotular(final, conectividade, area_minima)
    escrever_csv(componentes_inicial, prefixo + "_componentes_inicial.csv")
    escrever_csv(componentes_final, prefixo + "_componentes_final.csv")
    gravar_imagem(colorir(rotulos_final, componentes_final), prefixo + "_rotulos.png")

    resumo = {
        "entrada": entrada,
        "conectividade": conectividade,
        "min_area": area_minima,
        "criterio_filtro": "mantém componentes com area >= min_area (pixels)",
        "sequencia_morfologica": etapas,
        "antes": medir(inicial, conectividade, area_minima),
        "depois": medir(final, conectividade, area_minima),
    }
    try:
        with open(prefixo + "_resumo.json", "w", encoding="utf-8") as arquivo:
            json.dump(resumo, arquivo, indent=2, ensure_ascii=False)
    except OSError as erro:
        raise ErroPdi("falha ao gravar o resumo (%s)" % erro)

    for momento in ("antes", "depois"):
        m = resumo[momento]
        print("%s: %d componentes (4: %d, 8: %d), %d com area >= %d, %d px de primeiro plano"
              % (momento, m["brutos"], m["componentes_4"], m["componentes_8"], m["filtrados"], area_minima, m["area_primeiro_plano"]))
    return resumo
