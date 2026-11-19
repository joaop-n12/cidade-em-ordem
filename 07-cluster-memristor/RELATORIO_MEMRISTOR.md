# Memristor para registrar impactos de buracos: simulação no Falstad

**Cluster Computing, Computação Neuromórfica e Supercomputadores** · Global Solution 2026.2
**Projeto CitizenTech:** Cidade em Ordem · **Integrantes:** João Pedro de Souza Nunes (RM567318) e Guilherme Nakamura (RM567460)

## 1. Vínculo com o desafio
**Problema:** em 2025 a Prefeitura de São Paulo recebeu 113,1 mil pedidos de tapa-buraco, e o conserto depende de
alguém reclamar. No Cidade em Ordem, o caminhão de coleta leva um sensor (acelerômetro) que detecta o impacto ao
passar por um buraco.

**Evento escolhido:** impacto vertical acima do limiar (1,5 g) num trecho da rota.

**Função prevista para o registro:** o equipamento do caminhão liga e desliga várias vezes por dia e pode perder a
conexão. Um memristor por trecho de rota guardaria o evento "impacto registrado" **sem energia**, até ser
transmitido. Depois do reparo, um pulso reverso apaga o registro.

## 2. Circuito e configuração
Fonte DC V1 (representa o pulso do sensor hipotético) → memristor M1 → resistor de medição R_s = 100 Ω → terra.
O estado é acompanhado pela resistência R do memristor, lida no painel de informações do Falstad.

*Figura 1: circuito no Falstad e leitura inicial do memristor (R = 16 kΩ). Ver o PDF do relatório.*

| Componente | Parâmetro | Valor |
|---|---|---|
| V1 | Tensão (ajustada a cada ensaio) | 0 / +1 / +3 / −3 V |
| M1 | Resistência mínima (R_on) | 100 Ω |
| M1 | Resistência máxima (R_off) | 16 kΩ |
| M1 | Largura inicial da região dopada (w₀) | 0 nm (começa em R_off: nenhum impacto registrado) |
| M1 | Largura total (D) | 10 nm |
| M1 | Mobilidade (μ) | 100 µm²/(s·V) = 1×10⁻¹⁰ m²/(s·V) |
| R_s | Resistência | 100 Ω |
| Simulação | Passo de tempo | 5 µs |

## 3. Ensaios
Duas condições de entrada (**A: +1 V**, impacto moderado; **B: +3 V**, impacto severo), cada uma seguida da retirada da
tensão, e um pulso reverso (−3 V) representando o reparo.

| Etapa | Estímulo | Significado | I | R do memristor |
|---|---|---|---|---|
| 0 | 0 V | estado inicial | 0 | **16 kΩ** |
| 1 | +1 V | condição A | 5 mA | **100 Ω** |
| 2 | 0 V | após A | 0 | **100 Ω** (manteve) |
| 3 | +1 V e depois 0 V | 2º impacto | 5 mA / 0 | 100 Ω / 100 Ω |
| 4 | +3 V | condição B | 15 mA | 100 Ω |
| 5 | 0 V | após B | 0 | **100 Ω** (manteve) |
| 6 | −3 V | reparo (reset) | 186 µA | **16 kΩ** |
| 7 | 0 V | após reset | 0 | **16 kΩ** (manteve) |

*Figura 2: ensaios no Falstad: (a) condição A; (b) memória após retirar a tensão; (c) condição B; (d) reset. Ver o PDF do relatório.*

**Comparação A × B:** as duas condições terminaram no mesmo estado (100 Ω). Só a corrente durante o pulso foi
diferente (5 mA e 15 mA), porque o dispositivo já estava no valor mínimo depois da condição A. Os valores conferem com
a lei de Ohm: com 100 Ω no memristor e 100 Ω em R_s, 1 V / 200 Ω = 5 mA. No reset, 3 V / 16,1 kΩ ≈ 186 µA.

## 4. Análise e conclusão
No modelo do HP Labs usado pelo Falstad, R(w) = R_on·(w/D) + R_off·(1 − w/D), e a fronteira da região dopada se move
com a corrente: dw/dt = μ·R_on·i/D. Isso explica o observado:
- **corrente positiva** aumenta w e **reduz R** (etapa 1);
- **sem corrente**, dw/dt = 0 e **o estado fica parado** (etapas 2, 5 e 7). Essa é a memória não volátil;
- **corrente negativa** reduz w e **R volta a subir** (etapa 6).

**Por que saturou no primeiro pulso:** μ·R_on/D = 1 m/(s·A). Com cerca de 62 µA no início (1 V sobre 16,1 kΩ), a
região dopada atravessa os 10 nm em cerca de 0,16 ms, e cada etapa durou segundos. Por isso o comportamento
observado foi **binário** (registrado ou não), e não uma contagem gradual. Contar impactos exigiria pulsos de
microssegundos ou um dispositivo mais lento. Isso não foi demonstrado aqui.

**Limites da simulação:** o modelo é ideal (sem ruído, variação entre dispositivos ou perda lenta de estado); o
estímulo é uma fonte manual, e não o sinal do acelerômetro; a leitura também passa corrente e precisaria de tensão
baixa para não alterar o estado. Não foi construído hardware.

**Contribuição ao Cidade em Ordem:** a simulação mostrou que o memristor muda de estado com o estímulo, **mantém o
estado sem energia** e pode ser **zerado**. Na forma testada, ele serve como **marcador de "impacto registrado / reparo
feito"** para cada trecho de rua. Isso complementa o módulo IoT, porque preserva o evento mesmo que o equipamento do
caminhão desligue antes de transmitir pelo MQTT.

## 5. Reprodução
**Link do circuito no Falstad (abre pronto para simular):**
https://www.falstad.com/circuit/circuitjs.html?ctz=DwYwlgTgBAZgvAIgIwKgFwM6IAwDpsEECsqYIiSeATAVQOx0DM2AHFQGwCcndqIARojotUAB0EIALI1QA3CIhJQAtpkUBTALRIUAPgBQUKMFlQAHhSosojIlShIrDuu1TwE2VAHd3nlQEMzWRwEAHoDI2Blc0trJBcbGmdXWBCoCAB7ADsKAlRM9yR2QlQAEwy0tArkLREVaqQtSjCI42gLBEYk+PZE7Bs7NzSFZDzww2MvGM6k23tHazmhjxaJ4ABzaYWB+adGFkllz3HgUPAIAyA

Para repetir os ensaios, altere a tensão da fonte em cada etapa (clique duplo → *Voltage*) e leia R passando o mouse
sobre o memristor. Alternativa sem o link: *File → Import From Text* com o texto abaixo. Os prints dos ensaios estão no PDF do relatório.
```
$ 1 0.000005 10.20027730826997 50 5 43 5e-11
v 128 352 128 176 0 0 40 0 0 0 0.5
m 128 176 320 176 0 100 16000 0 1e-8 1e-10
r 320 176 320 352 0 100
w 320 352 128 352 0
g 128 352 128 384 0 0
```
