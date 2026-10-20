# Laboratórios M2.1 e M2.2 — Segmentação e componentes conexos

**Disciplina:** Processamento de Imagens — 2026-02  
**Laboratórios:** M2.1 (máscara binária e segmentação) e M2.2 (componentes conexos e sequência morfológica)  
**Estudante:** Erick Lemos Barreto  
**Linguagem:** Python

## Visão geral

Para os laboratórios M2.1 e M2.2, desenvolvi o programa de linha de comando `pdi_lab`, seguindo o formato usado na M1, com os argumentos `--input`, `--output` e `--operation`.

O programa tem duas operações principais:

- `segment` (M2.1): recebe uma imagem e gera uma máscara binária, em que o fundo é representado por `0` e os objetos por `255`.
- `analyze` (M2.2): identifica e conta os componentes conexos da máscara, aplica uma sequência de operações morfológicas e faz uma nova contagem.

Para realizar essas etapas, usei funções do OpenCV para limiarização, seleção de cores em HSV, operações morfológicas e rotulação de componentes, conforme permitido pelo enunciado da M2.

## Dependências

O projeto precisa de Python 3.10 ou superior e das bibliotecas `opencv-python`, `numpy` e `pytest`. As versões utilizadas estão registradas no arquivo `requirements.txt`.

## Preparação do ambiente

```bash
python -m venv .venv
source .venv/Scripts/activate      # MSYS2 UCRT64 / Git Bash
# .venv\Scripts\activate           # PowerShell
# source .venv/bin/activate         # Linux / macOS
python -m pip install -r requirements.txt
python -m pdi_lab --help
```

Fiz os testes no Windows 11, usando Python 3.12 instalado pelo python.org e Git Bash. Não cheguei a testar no MSYS2 UCRT64. Caso o `pip` não consiga instalar o `opencv-python` nesse ambiente, uma alternativa é tentar a versão disponível pelo `pacman`:

```bash
pacman -S mingw-w64-ucrt-x86_64-python-opencv
```

## Testes

Para executar os testes automatizados, use:

```bash
python -m pytest
```

## Organização dos arquivos

```text
images/input/    tampas_papel_branco.webp, tampas_papel_amassado.webp (imagens originais)
images/output/   arquivos gerados: máscaras, sobreposições, CSVs, rótulos e resumos
src/pdi_lab/     código do programa
  __main__.py    entrada da linha de comando
  imagem.py      leitura, gravação e validação das máscaras
  segmentacao.py métodos de segmentação
  componentes.py análise dos componentes conexos
tests/           testes automatizados
```

## Como executar

### Operação `segment`

A operação `segment` gera uma máscara binária a partir de uma imagem. Ela oferece dois métodos: limiar fixo em tons de cinza e seleção de uma faixa de cores no espaço HSV.

```bash
python -m pdi_lab --input <imagem> --output <mascara.png> --operation segment --method fixed --threshold <0-255> [--invert] [--overlay <arquivo.png>]

python -m pdi_lab --input <imagem> --output <mascara.png> --operation segment --method hsv --hsv-min H,S,V --hsv-max H,S,V [--overlay <arquivo.png>]
```

- **`fixed`:** converte a imagem para tons de cinza e aplica `cv2.threshold`. Por padrão, pixels com valor maior que o limiar viram `255`, enquanto os pixels iguais ou abaixo dele viram `0`. Com `--invert`, o resultado é invertido, permitindo selecionar as regiões mais escuras. Usei essa opção neste trabalho porque as tampas são mais escuras que o papel.
- **`hsv`:** usa `cv2.inRange` para selecionar pixels dentro de uma faixa de cor no espaço HSV do OpenCV. Nesse espaço, H varia de `0` a `179`, e S e V variam de `0` a `255`. O valor mínimo de cada canal deve ser menor ou igual ao máximo. Faixas que atravessam o vermelho não são tratadas, mas isso não foi necessário para segmentar as tampas azuis.
- **`--overlay`:** é opcional e salva uma cópia da imagem original com os pixels selecionados destacados em vermelho.

A máscara de saída precisa estar no formato PNG. Depois de salvar o arquivo, o programa o abre novamente e verifica se a imagem mantém as mesmas dimensões da entrada, possui apenas um canal e contém somente os valores `0` e `255`. Ao final, também informa a quantidade e a proporção de pixels classificados como primeiro plano.

### Operação `analyze`

A operação `analyze` recebe uma máscara binária e realiza a contagem dos componentes conexos. Também permite aplicar operações morfológicas antes da análise final.

```bash
python -m pdi_lab --input <mascara.png> --output <prefixo> --operation analyze [--connectivity 4|8] [--min-area N] [--morph etapas]
```

Os principais parâmetros são:

- **`--connectivity`:** define a conectividade usada na rotulação. Pode ser `4` ou `8`; o padrão é `8`.
- **`--min-area`:** define a área mínima para manter um componente. Aceita inteiros maiores ou iguais a zero e mantém componentes com `area >= N`. O padrão é `0`.
- **`--morph`:** define as operações morfológicas a executar, usando o formato `operacao:forma:tamanho:iteracoes`. É possível informar várias etapas separadas por vírgulas.

As operações disponíveis são `open`, `close`, `erode` e `dilate`, e os elementos estruturantes podem ter formato `rect` ou `ellipse`. A sequência padrão é:

```text
open:ellipse:5:1,close:ellipse:5:1
```

A entrada também precisa ser uma máscara binária de um canal, contendo apenas `0` e `255`. Se o arquivo não atender a esses requisitos, o programa o rejeita em vez de convertê-lo automaticamente.

### Arquivos gerados pelo `analyze`

Por exemplo, usando `--output images/output/branco`, o programa gera arquivos com o prefixo `branco`:

| Arquivo | Conteúdo |
|---|---|
| `branco_mask_0_inicial.png`, `branco_mask_1_open.png`, `branco_mask_2_close.png` | Máscara original e resultado de cada etapa morfológica |
| `branco_componentes_inicial.csv`, `branco_componentes_final.csv` | Dados dos componentes: `label,area,x,y,width,height,cx,cy,kept`, sem incluir o fundo |
| `branco_rotulos.png` | Componentes finais coloridos e com caixas delimitadoras; componentes removidos pelo filtro aparecem em cinza |
| `branco_resumo.json` | Configurações usadas, conectividade, filtro, sequência morfológica e estatísticas antes e depois |

## Como reproduzir os resultados do relatório

Os comandos abaixo executam a segmentação das duas imagens pelos métodos fixo e HSV e, em seguida, analisam as máscaras HSV geradas.

### M2.1 — Segmentação

```bash
python -m pdi_lab --input images/input/tampas_papel_branco.webp --output images/output/branco_fixed_mask.png --operation segment --method fixed --threshold 100 --invert --overlay images/output/branco_fixed_overlay.png

python -m pdi_lab --input images/input/tampas_papel_branco.webp --output images/output/branco_hsv_mask.png --operation segment --method hsv --hsv-min 95,120,30 --hsv-max 130,255,255 --overlay images/output/branco_hsv_overlay.png

python -m pdi_lab --input images/input/tampas_papel_amassado.webp --output images/output/amassado_fixed_mask.png --operation segment --method fixed --threshold 100 --invert --overlay images/output/amassado_fixed_overlay.png

python -m pdi_lab --input images/input/tampas_papel_amassado.webp --output images/output/amassado_hsv_mask.png --operation segment --method hsv --hsv-min 95,120,30 --hsv-max 130,255,255 --overlay images/output/amassado_hsv_overlay.png
```

### M2.2 — Componentes conexos

Os comandos seguintes usam as máscaras HSV criadas na etapa anterior:

```bash
python -m pdi_lab --input images/output/branco_hsv_mask.png --output images/output/branco --operation analyze --connectivity 8 --min-area 1000 --morph open:ellipse:5:1,close:ellipse:5:1

python -m pdi_lab --input images/output/amassado_hsv_mask.png --output images/output/amassado --operation analyze --connectivity 8 --min-area 1000 --morph open:ellipse:5:1,close:ellipse:5:1
```

## Códigos de saída

O programa utiliza os seguintes códigos para indicar como terminou a execução:

- `0`: execução concluída com sucesso.
- `1`: erro tratado durante a execução, como arquivo inexistente ou inválido, parâmetro inválido, máscara não binária ou falha ao salvar um arquivo.
- `2`: erro nos argumentos da linha de comando, como operação, método ou conectividade não permitidos, ou argumento obrigatório ausente.

## Limitações

- Como não tenho uma máscara de referência, a identificação de falsos positivos e falsos negativos foi feita por inspeção visual. Por isso, não foi possível calcular métricas como precisão e revocação.
- Os parâmetros de segmentação foram escolhidos para as duas imagens utilizadas no laboratório e podem precisar de ajustes em outras fotos.
- Quando duas tampas ficam conectadas na máscara, a operação de fechamento pode uni-las em um único componente. Nesse caso, a contagem de componentes deixa de corresponder diretamente à quantidade real de tampas.
