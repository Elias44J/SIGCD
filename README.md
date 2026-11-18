<div align="center"> <img src="handify_1024.png" alt="Ícone do Handify" width="128" height="128"> <h1>Handify</h1> </div> <p align="center"> Controle o computador com as mãos, usando só a webcam. </p> <p align="center"> <a href="#recursos">Recursos</a> · <a href="#instalação">Instalação</a> · <a href="#como-usar">Como usar</a> · <a href="#problemas-conhecidos">Problemas conhecidos</a> </p> <hr>

O Handify reconhece poses da sua mão com o MediaPipe e as transforma em ações: teclas, atalhos, sequências de comandos e até o controle completo do mouse (mover o cursor, clicar e rolar). Os gestos são todos personalizados: você grava a sua própria pose e escolhe o que ela faz.

## Recursos

- **Gestos personalizados:** grave 10 amostras de qualquer pose e associe a uma ação.
- **Ações de teclado:** tecla única, combinação (`ctrl+shift+esc`), sequência com pausas (`ctrl+c | delay:0.2 | ctrl+v`) e comando especial (captura de tela).
- **Modo mouse por gestos:** mova o cursor, faça clique esquerdo, do meio e direito, arraste e role a página.
- **Gesto de ativação:** segure uma pose por cerca de 1 segundo para ligar ou desligar o modo mouse. Os gestos de teclado ficam pausados enquanto o modo mouse está ligado.
- **Pré-visualização da mão:** o esqueleto da última amostra gravada aparece no painel lateral.
- **Confiança e cooldown por gesto:** evite disparos acidentais ajustando a confiança mínima e o tempo de espera entre execuções.

## Como funciona

1. A câmera captura cada frame e o MediaPipe Hand Landmarker detecta os 21 pontos da mão.
2. Os pontos são normalizados: o pulso vira a origem e o tamanho da mão é escalado. Assim o reconhecimento não depende de onde a mão está na imagem nem de quão perto ela está da câmera.
3. A pose atual é comparada com as amostras gravadas. A menor distância define o gesto e a confiança (distância acima de 0,32 não conta como gesto).
4. Se a confiança passar do mínimo configurado, a ação do gesto é executada.

## Requisitos

- Python 3.11 a 3.14 (o MediaPipe pode demorar a suportar versões muito novas; se a instalação falhar, use o 3.12)
- Uma webcam
- Linux, Windows ou macOS

Dependências principais: `PySide6`, `opencv-python`, `mediapipe` e `pyautogui`.

O executavel esta disponivel na aba Realeases do github logo a direita, basta baixa-lo e executa-lo para uso.

## Como usar

### Gestos de teclado

1. Na aba **Teclado**, clique em **Novo gesto** e dê um nome.
2. Mostre a mão à câmera e clique em **Capturar amostra do gesto atual**. Depois de uma contagem de 5 segundos, o app coleta 10 amostras. Repita com pequenas variações de ângulo para o reconhecimento ficar mais robusto.
3. Escolha a ação (tecla, combinação, sequência ou comando especial), ajuste a confiança mínima e o cooldown, e clique em **Salvar configuração**.
4. Use **Testar ação** para conferir se a ação funciona sem precisar fazer o gesto.

### Modo mouse

1. Na aba **Mouse**, grave o gesto de **Ativação do modo mouse**.
2. Grave os gestos de **Mover cursor (embreagem)**, **Clique esquerdo**, **Clique do meio**, **Clique direito** e **Rolagem**.
3. Segure o gesto de ativação até o selo no painel da câmera mostrar **Modo mouse: LIGADO**. Para desligar, segure o gesto de ativação de novo.

Com o modo ligado:

| Gesto | O que faz |
|---|---|
| Embreagem | O cursor acompanha o movimento da mão. Ao soltar a pose, você pode reposicionar a mão sem mover o cursor, como levantar um mouse físico. |
| Clique esquerdo | Um clique ao soltar a pose. Se a pose for mantida por mais de 0,45 s, inicia um arraste. |
| Clique do meio / direito | Um clique ao entrar na pose. |
| Rolagem | Mover a mão para cima rola a página para cima, e mover para baixo rola para baixo. O cursor fica parado durante a rolagem. |

Em **Cursor e cliques** dá para ajustar ganho, zona morta, suavização, margem da câmera, sensibilidade da rolagem, tempo de arraste, tempo para ativar e confiança mínima.

## Onde ficam os dados

Os gestos e as configurações são arquivos JSON:

| Arquivo | Conteúdo |
|---|---|
| `keyboard.json` | Gestos de teclado e suas ações |
| `mouse.json` | Gestos do mouse e ajustes |
| `hand_landmarker.task` | Modelo do MediaPipe |

A pasta depende de como o app é executado:

- **AppImage:** `handify_config/`, ao lado do arquivo `.AppImage` (ou `~/.config/handify` se a pasta não for gravável).
- **Executável do PyInstaller:** `handify_config/`, ao lado do executável.

Esses arquivos têm as amostras da sua mão e não devem ir para o repositório. Mantenha `handify_config/` no `.gitignore`.

## Instalação

Em caso de desenvolvimento

```bash
git clone https://github.com/EliasTrindadeLJr/SIGCD.git
cd SIGCD

python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

pip install -r requirements.txt
python main.py
```

Na primeira execução, o app baixa o modelo `hand_landmarker.task` do MediaPipe e o guarda na pasta de configuração. É preciso internet só nessa vez.

## Problemas conhecidos

- **Wayland:** o `pyautogui` controla o mouse e o teclado pelo X11. No Wayland, ele só funciona com janelas executadas via XWayland, e o cursor, os cliques e a rolagem podem não ter efeito em aplicativos nativos do Wayland. Se possível, use uma sessão X11.
- **Ícone no Wayland:** o ícone da janela só aparece se existir um arquivo `.desktop` com o mesmo nome do app (`handify`).
- **Poses parecidas:** se dois gestos forem muito semelhantes, o reconhecimento pode confundi-los. Grave poses bem distintas e aumente a confiança mínima.
- **Iluminação:** pouca luz ou a mão parcialmente fora do quadro reduzem a confiança do reconhecimento.
