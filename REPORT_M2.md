# Mini relatório técnico — Laboratórios M2.1 e M2.2

## 1. Identificação

- **Estudante:** Erick Lemos Barreto
- **Disciplina:** Processamento de Imagens — 2026-02
- **Laboratórios:** M2.1 — Máscara binária e segmentação; M2.2 — Componentes conexos e sequência morfológica
- **Linguagem:** Python 3.12 + OpenCV

## 2. Objetivo

A ideia era separar as tampas azuis do fundo em duas fotos (M2.1) e, depois, contar essas tampas como componentes conexos antes e depois de uma sequência morfológica (M2.2).

## 3. O que foi implementado

- **`segment`:** limiar fixo em cinza (`fixed`, com `--invert`) e faixa de cor em HSV (`hsv`). O programa grava a máscara em PNG, relê o arquivo e confere se o tamanho bate, se tem um canal só e se os valores são só `{0, 255}`. Opcionalmente também salva uma sobreposição em vermelho.
- **`analyze`:** rotulação com `cv2.connectedComponentsWithStats` (conectividade 4 e 8), filtro por área mínima, sequência morfológica configurável pela linha de comando, máscaras de cada etapa, CSVs, imagem de rótulos e um resumo em JSON.

## 4. Decisões de implementação

- **Máscara:** fundo = `0`, objeto = `255`, um canal, PNG.
- No `fixed`, pixel igual ao limiar vai para o fundo (regra do OpenCV). Como as tampas são mais escuras que o papel, usei `--invert`.
- O `analyze` recusa máscara que não seja `0/255` em vez de converter escondido.
- **Filtro:** mantém componente com `area >= min-area`; as contagens brutas e filtradas ficam gravadas separadas.
- Todas as saídas vão para `images/output/`.

# M2.1 — Segmentação

## 5. Imagens e alvo

O alvo eram as tampas azuis (6 em cada foto). As duas fotos são minhas e estão em `images/input/` sem nenhuma modificação.

| Imagem | Condição |
|---|---|
| `tampas_papel_branco.webp` (725 × 1076) | Favorável: fundo branco liso, iluminação uniforme; tem uma faixa de madeira nas bordas e sombras curtas ao lado das tampas |
| `tampas_papel_amassado.webp` (726 × 1076) | Difícil: papel pardo amassado, luz lateral forte, sombras longas e escuras, duas tampas quase encostadas |

## 6. Configurações

Usei as mesmas duas configurações nas duas fotos, sem pré-processamento:

| Configuração | Parâmetros |
|---|---|
| Fixo | cinza, `--threshold 100 --invert` (pixel ≤ 100 vira objeto) |
| HSV | `--hsv-min 95,120,30 --hsv-max 130,255,255` (matiz azul, saturação alta) |

A faixa HSV saiu de amostras que peguei na mão: as tampas ficaram em H ≈ 107–111 e S ≈ 236–255; o papel pardo e as sombras em H ≈ 13–15; o papel branco em S ≈ 20.

## 7. Resultados

| Imagem | Configuração | Primeiro plano (px) | Total (px) | Proporção |
|---|---:|---:|---:|---:|
| Papel branco | Fixo | 97.033 | 780.100 | 12,44% |
| Papel branco | HSV | 65.805 | 780.100 | 8,44% |
| Papel amassado | Fixo | 375.483 | 781.176 | 48,07% |
| Papel amassado | HSV | 77.382 | 781.176 | 9,91% |

### Sobreposições

| Imagem | Fixo (T = 100, invertido) | HSV |
|---|---|---|
| Papel branco | [branco_fixed_overlay.png](images/output/branco_fixed_overlay.png) | [branco_hsv_overlay.png](images/output/branco_hsv_overlay.png) |
| Papel amassado | [amassado_fixed_overlay.png](images/output/amassado_fixed_overlay.png) | [amassado_hsv_overlay.png](images/output/amassado_hsv_overlay.png) |

Máscaras: `images/output/*_fixed_mask.png` e `images/output/*_hsv_mask.png`.

Todas as máscaras passaram na verificação automática (PNG, um canal, mesmo tamanho da entrada, só `0` e `255`).

## 8. Comparação (olhando as imagens, sem máscara de referência)

- **Papel branco, fixo:** pega as tampas, mas também a sombra ao lado de cada uma e as faixas de madeira nas bordas (falsos positivos).
- **Papel branco, HSV:** só as tampas; a sombra e a madeira não são azuis.
- **Papel amassado, fixo:** falha feio. As sombras e dobras do papel são tão escuras quanto as tampas; quase metade da imagem virou objeto e as tampas se juntam às sombras.
- **Papel amassado, HSV:** separa bem as tampas da sombra, porque a sombra muda o brilho mas não a cor. Há falsos negativos na lateral de baixo de algumas tampas, que fica muito escura (V baixo), e alguns pontinhos isolados.

**Escolha para o M2.2:** a máscara HSV nas duas imagens, porque foi a única que não misturou sombra com tampa.

## 9. Perguntas

**Em quais casos o limiar fixo funcionou ou falhou?**  
Funcionou razoavelmente no papel branco, onde só as tampas e as sombras curtas são escuras. Falhou no papel amassado, onde as sombras têm o mesmo nível de cinza das tampas.

**Qual parâmetro foi mais sensível?**  
O limiar do fixo: o mesmo `T = 100` marcou 12,44% da foto no papel branco e 48,07% no amassado, porque depende da iluminação. No HSV, o mínimo de V decide se a lateral escura das tampas entra ou não.

**Quais erros podem prejudicar a contagem no M2.2?**  
Sombra ligada à tampa (no fixo), tampas encostadas virando uma região só, pontinhos isolados contados como objetos e tampas com a borda cortada.

# M2.2 — Componentes conexos

## 10. Conectividade 4 × 8

| Máscara inicial (HSV) | Conectividade 4 | Conectividade 8 |
|---|---:|---:|
| Papel branco | 6 | 6 |
| Papel amassado | 53 | 36 |

No papel amassado, a diferença está só nos pontinhos (todos com até 36 px): pixels que se tocam pela quina contam juntos na conectividade 8 e separados na conectividade 4. Com o filtro de 1000 px, as duas dão 6 componentes. O teste com dois pixels na diagonal confirma a regra (4 → 2, 8 → 1).

Escolhi conectividade 8, porque não muda a contagem das tampas e não parte um pontinho em vários.

## 11. Sequência morfológica

Comando: `--morph open:ellipse:5:1,close:ellipse:5:1`, igual nas duas imagens, com `--min-area 1000`.

| Etapa | Operação | Elemento | Iterações | Para quê |
|---|---|---|---:|---|
| 1 | Abertura | elipse 5 × 5 | 1 | Tirar os pontinhos isolados do papel amassado |
| 2 | Fechamento | elipse 5 × 5 | 1 | Fechar frestas e buracos pequenos na borda das tampas |

O filtro de 1000 px fica bem abaixo da menor tampa (cerca de 10.400 px) e acima do maior pontinho (47 px).

### Evolução das máscaras

| Imagem | Inicial | Abertura | Fechamento | Rótulos finais |
|---|---|---|---|---|
| Papel branco | [branco_mask_0_inicial.png](images/output/branco_mask_0_inicial.png) | [branco_mask_1_open.png](images/output/branco_mask_1_open.png) | [branco_mask_2_close.png](images/output/branco_mask_2_close.png) | [branco_rotulos.png](images/output/branco_rotulos.png) |
| Papel amassado | [amassado_mask_0_inicial.png](images/output/amassado_mask_0_inicial.png) | [amassado_mask_1_open.png](images/output/amassado_mask_1_open.png) | [amassado_mask_2_close.png](images/output/amassado_mask_2_close.png) | [amassado_rotulos.png](images/output/amassado_rotulos.png) |

### Antes e depois (de `*_resumo.json`)

| Métrica | Branco antes | Branco depois | Amassado antes | Amassado depois |
|---|---:|---:|---:|---:|
| Componentes brutos (8) | 6 | 6 | 36 | 8 |
| Com área ≥ 1000 | 6 | 6 | 6 | 5 |
| Área de primeiro plano (px) | 65.805 | 65.778 | 77.382 | 76.702 |

## 12. Observações

- **Papel amassado:** a abertura limpou o ruído: de 36 componentes brutos sobraram 8; os 3 que não são tampa têm 17, 17 e 47 px, e o filtro remove.
- **Papel branco:** quase nada mudou: a máscara HSV já estava limpa; a área caiu só 27 px (contorno suavizado).
- **Efeito indesejado:** a abertura apagou a borda listrada e escura de baixo da tampa do canto superior direito do papel amassado (11.947 → 11.616 px).
- **Onde prejudica (regiões em contato):** no papel amassado, o fechamento ligou as duas tampas que estavam quase encostadas. Elas eram componentes separados (11.864 e 12.802 px) e viraram um só de 24.446 px; a contagem filtrada caiu de 6 para 5.
- **Onde ajuda:** a abertura resolveu o ruído do papel amassado sem precisar de filtro (36 → 8 brutos).

## 13. Componentes × objetos reais

Componente conexo não é a mesma coisa que objeto. No papel amassado o resultado final tem 5 componentes grandes para 6 tampas, porque duas tampas encostadas viraram um componente. Sem o filtro de área, seriam 8, por causa dos pontinhos. Só no papel branco a contagem (6) bate com o número de tampas.

## 14. Testes

`python -m pytest` — **37 testes, todos passando**. Cobrem: pixel abaixo, igual e acima do limiar; inversão; faixa HSV; verificação da máscara; as duas configurações nas duas fotos; pixels na diagonal (4 × 8); abertura removendo ruído; fechamento fechando furo; objeto na borda; filtro de área e fundo fora do CSV; máscara vazia; entradas inválidas; erros de leitura e gravação; e as duas fotos de ponta a ponta, conferindo que a soma das áreas do CSV é igual aos pixels de primeiro plano.

## 15. Limitações

- Sem máscara de referência, então não dá para calcular acurácia, precisão ou revocação.
- Faixa HSV e limiar escolhidos para estas duas fotos.
- A morfologia não separa tampas encostadas.

## 16. Declaração de uso de IA

Ver `AI_USAGE.md`.

## 17. Referências

- Enunciados dos Laboratórios M2.1 e M2.2 — Processamento de Imagens, 2026-02.
- Contrato técnico e rubrica dos Laboratórios da M1.
- Documentação do OpenCV: `threshold`, `cvtColor`, `inRange`, `morphologyEx`, `connectedComponentsWithStats`.
