import cv2
import numpy as np


# No THRESH_BINARY, só os pixels acima do limiar viram 255; os iguais ou abaixo ficam em 0.
# Se eu inverter o resultado, os pixels escuros (menores ou iguais ao limiar) viram primeiro plano.
def limiar_fixo(bgr, limiar, inverter=False):
    cinza = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    tipo = cv2.THRESH_BINARY_INV if inverter else cv2.THRESH_BINARY
    _, mascara = cv2.threshold(cinza, limiar, 255, tipo)
    return mascara


# No OpenCV, H vai de 0 a 179, enquanto S e V vão de 0 a 255.
def faixa_hsv(bgr, minimo, maximo):
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    return cv2.inRange(hsv, np.array(minimo), np.array(maximo))


# Marco o primeiro plano em vermelho, com 50% de transparência, para conseguir ver a imagem original por baixo.
def sobrepor(bgr, mascara):
    vermelho = np.zeros_like(bgr)
    vermelho[:, :] = (0, 0, 255)
    misturada = cv2.addWeighted(bgr, 0.5, vermelho, 0.5, 0)
    saida = bgr.copy()
    saida[mascara == 255] = misturada[mascara == 255]
    return saida
