import argparse
import sys

import numpy as np

from .componentes import analisar
from .imagem import ErroPdi, gravar_imagem, ler_imagem, ler_mascara
from .segmentacao import faixa_hsv, limiar_fixo, sobrepor


def tres_inteiros(texto):
    try:
        h, s, v = (int(parte) for parte in texto.split(","))
    except ValueError:
        raise argparse.ArgumentTypeError("use o formato H,S,V (ex.: 95,120,30)")
    return h, s, v


def criar_parser():
    parser = argparse.ArgumentParser(prog="pdi_lab", description="Laboratórios M2.1 e M2.2")
    parser.add_argument("--input", required=True, help="imagem de entrada (no analyze, a máscara)")
    parser.add_argument("--output", required=True, help="máscara PNG (segment) ou prefixo dos arquivos (analyze)")
    parser.add_argument("--operation", required=True, choices=("segment", "analyze"))

    parser.add_argument("--method", choices=("fixed", "hsv"), help="método do segment")
    parser.add_argument("--threshold", type=int, help="limiar do método fixed (0-255)")
    parser.add_argument("--invert", action="store_true", help="primeiro plano = região escura")
    parser.add_argument("--hsv-min", type=tres_inteiros, help="limite inferior H,S,V")
    parser.add_argument("--hsv-max", type=tres_inteiros, help="limite superior H,S,V")
    parser.add_argument("--overlay", help="grava também a sobreposição máscara + original")

    parser.add_argument("--connectivity", type=int, choices=(4, 8), default=8)
    parser.add_argument("--min-area", type=int, default=0, help="área mínima para manter um componente")
    parser.add_argument("--morph", default="open:ellipse:5:1,close:ellipse:5:1",
                        help="etapas operacao:forma:tamanho:iteracoes separadas por vírgula")
    return parser


def validar_segment(args):
    if args.method is None:
        raise ErroPdi("a operação segment exige --method")
    if not args.output.lower().endswith(".png"):
        raise ErroPdi("a máscara deve ser gravada em PNG (sem perdas)")
    if args.method == "fixed":
        if args.threshold is None or not 0 <= args.threshold <= 255:
            raise ErroPdi("o método fixed exige --threshold entre 0 e 255")
    else:
        if args.hsv_min is None or args.hsv_max is None:
            raise ErroPdi("o método hsv exige --hsv-min e --hsv-max")
        for minimo, maximo, limite in zip(args.hsv_min, args.hsv_max, (179, 255, 255)):
            if not 0 <= minimo <= maximo <= limite:
                raise ErroPdi("faixa HSV inválida (H 0-179, S e V 0-255, mínimo <= máximo)")


def executar_segment(args):
    validar_segment(args)
    bgr = ler_imagem(args.input)
    if args.method == "fixed":
        mascara = limiar_fixo(bgr, args.threshold, args.invert)
    else:
        mascara = faixa_hsv(bgr, args.hsv_min, args.hsv_max)
        if args.invert:
            mascara = 255 - mascara
    gravar_imagem(mascara, args.output)

    # confere o arquivo gravado, não só o array em memória
    altura, largura = bgr.shape[:2]
    ler_mascara(args.output, altura, largura)
    if args.overlay:
        gravar_imagem(sobrepor(bgr, mascara), args.overlay)

    frente = int(np.count_nonzero(mascara))
    print("primeiro plano: %d de %d pixels (%.2f%%)" % (frente, mascara.size, 100 * frente / mascara.size))


def executar(args):
    if args.operation == "segment":
        executar_segment(args)
    else:
        if args.min_area < 0:
            raise ErroPdi("--min-area deve ser um inteiro não negativo")
        analisar(args.input, args.output, args.connectivity, args.min_area, args.morph)


def main(argv=None):
    args = criar_parser().parse_args(argv)
    try:
        executar(args)
    except ErroPdi as erro:
        print("erro: %s" % erro, file=sys.stderr)
        return 1
    print("saída gravada em %s" % args.output)
    return 0


if __name__ == "__main__":
    sys.exit(main())
