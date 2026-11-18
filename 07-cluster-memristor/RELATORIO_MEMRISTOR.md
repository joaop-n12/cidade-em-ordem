# Memória resistiva para registrar impactos de buracos: simulação de memristor no Falstad

**Cluster Computing, Computação Neuromórfica e Supercomputadores** · Global Solution 2026.2
**Projeto CitizenTech:** Cidade em Ordem

| Integrante | RM |
|---|---|
| João Pedro de Souza Nunes | RM567318 |
| Guilherme Nakamura | RM567460 |

## 1. Vínculo com o desafio

**Problema:** buracos só são consertados depois que alguém reclama. Em 2025, a Prefeitura de São Paulo recebeu
113,1 mil pedidos de tapa-buraco, e um mesmo buraco gera vários chamados. No Cidade em Ordem, os caminhões de
coleta levam um sensor (acelerômetro) que detecta o impacto ao passar por um buraco.

**Evento escolhido:** *impacto vertical acima do limiar (1,5 g) no mesmo trecho de rua.*

**Por que lembrar a ocorrência:** um impacto isolado pode ser uma lombada ou uma tampa de bueiro. **Impactos repetidos
no mesmo ponto** indicam um buraco real que está piorando. Hoje essa "memória" fica no servidor. Um memristor por
trecho de rota permitiria que o próprio sensor acumulasse a quantidade de impactos de forma **analógica, com baixo
consumo e sem perder o registro se a energia cair**. Isso é útil num equipamento embarcado num caminhão, que liga e
desliga várias vezes por dia.

**Função prevista para o registro:** a resistência do memristor funciona como um contador analógico. Quanto mais
impactos, menor a resistência. Quando a resistência cai abaixo de um limiar, o ponto é marcado como "buraco
confirmado" e enviado na próxima conexão MQTT. Depois do reparo, um pulso reverso zera o registro.

## 2. Circuito e configuração

**Topologia:** fonte de tensão DC V1 (representa o pulso gerado pelo sensor hipotético) → memristor M1 → resistor de
medição R_s = 100 Ω → terra. O estado é acompanhado pela **resistência do memristor** (valor R exibido pelo Falstad
ao passar o mouse sobre M1), junto com a corrente I e a tensão Vd no memristor.

![Circuito no Falstad](prints/etapa0.png)

| Componente | Parâmetro | Valor usado | Unidade |
|---|---|---|---|
| V1 (fonte DC, ajustada a cada ensaio) | Tensão | 0 / +1 / +3 / −3 | V |
| M1 (memristor) | Resistência mínima (R_on) | 100 | Ω |
| M1 | Resistência máxima (R_off) | 16.000 | Ω |
| M1 | Largura inicial da região dopada (w₀) | 0 | nm |
| M1 | Largura total (D) | 10 | nm |
| M1 | Mobilidade dos dopantes (μ) | 100 µm²/(s·V) = 1×10⁻¹⁰ | m²/(s·V) |
| R_s | Resistência | 100 | Ω |
| Simulação | Passo de tempo | 5×10⁻⁶ | s |

Com w₀ = 0, o memristor começa em R_off (16 kΩ), ou seja, **nenhum impacto registrado**.

## 3. Ensaios

Cada etapa durou alguns segundos de simulação. Os valores foram lidos no painel de informações do Falstad (prints
em `prints/etapa0.png` a `prints/etapa7.png`).

| Etapa | Estímulo | Significado | Corrente I | Tensão no memristor Vd | R do memristor |
|---|---|---|---|---|---|
| 0 | 0 V | estado inicial | 0 A | 0 V | **16 kΩ** |
| 1 | +1 V | **Condição A:** impacto moderado | 5 mA | 500 mV | **100 Ω** |
| 2 | 0 V | tensão retirada | 0 A | 0 V | **100 Ω** |
| 3 | +1 V | 2º impacto no mesmo ponto | 5 mA | 500 mV | 100 Ω |
| 3b | 0 V | tensão retirada | 0 A | 0 V | 100 Ω |
| 4 | +3 V | **Condição B:** impacto severo | 15 mA | 1,5 V | 100 Ω |
| 5 | 0 V | tensão retirada | 0 A | 0 V | **100 Ω** |
| 6 | −3 V | reparo (reset) | 186,3 µA | 2,981 V | **16 kΩ** |
| 7 | 0 V | tensão retirada | 0 A | 0 V | **16 kΩ** |

**Comparação A × B:** as duas condições levaram o memristor ao **mesmo estado final (100 Ω = R_on)**. A diferença
apareceu só na corrente durante o pulso: 5 mA com +1 V e 15 mA com +3 V, ou seja, três vezes maior. Como o
dispositivo já estava saturado depois da condição A, a condição B não tinha mais para onde levar a resistência.

**Conferência dos valores:** com R = 100 Ω no memristor e 100 Ω no resistor de medição, a fonte de 1 V se divide
igualmente: Vd = 0,5 V e I = 1 V / 200 Ω = 5 mA, como o Falstad mostrou. No reset, com R = 16 kΩ,
I = 3 V / 16,1 kΩ ≈ 186 µA, também igual ao observado.

## 4. Análise e conclusão

### Explicação física
No modelo de memristor do HP Labs, usado pelo Falstad, o dispositivo é uma camada fina de largura D com uma região
dopada de largura w. A resistência é

  R(w) = R_on·(w/D) + R_off·(1 − w/D)

e a fronteira entre as regiões se move com a corrente: dw/dt = μ·R_on·i(t)/D.

**O que se confirmou na simulação:**
- **Corrente positiva reduz R** (etapa 1: 16 kΩ para 100 Ω).
- **Sem corrente, o estado não muda** (etapas 2, 5 e 7). Como i = 0, dw/dt = 0 e a resistência fica parada. Essa é a
  **memória não volátil**: o registro continua mesmo sem energia.
- **Corrente negativa desfaz o registro** (etapa 6: 100 Ω para 16 kΩ), e o reset também se mantém (etapa 7).

**Por que saturou no primeiro pulso:** com os parâmetros usados, a velocidade da fronteira é
μ·R_on/D = (1×10⁻¹⁰ · 100) / 1×10⁻⁸ = 1 m/(s·A). No início, com 1 V sobre cerca de 16,1 kΩ, a corrente é de
aproximadamente 62 µA, e w percorre os 10 nm em cerca de **0,16 ms**. À medida que R cai, a corrente sobe e a troca
acelera. Como cada etapa durou segundos, o memristor foi de R_off a R_on quase instantaneamente. Por isso a
simulação mostrou um comportamento **binário** (registrado ou não registrado), e não uma contagem gradual de
impactos. Para observar acúmulo, seria preciso usar pulsos de microssegundos ou um dispositivo mais lento (menor
mobilidade ou maior largura).

### Contribuição para o Cidade em Ordem
Com o comportamento observado, o memristor funciona como um **sinalizador não volátil de evento**:
- **Registro do impacto sem energia:** o primeiro impacto acima do limiar "marca" o trecho de rota (R cai para
  100 Ω), e a marca continua se o equipamento do caminhão desligar ou perder a conexão.
- **Leitura simples:** basta medir a resistência com uma tensão baixa. Um valor perto de 100 Ω indica que há evento
  registrado naquele trecho, e o ESP32 envia o evento na próxima conexão MQTT.
- **Reset após o reparo:** o pulso negativo "apaga" o registro quando a ordem de serviço é concluída (etapa 6).
- Para **contar** impactos (por exemplo, confirmar o buraco só depois de 3 passagens), seriam necessários pulsos muito
  curtos ou um dispositivo com troca mais lenta, além de calibração. Isso não foi demonstrado nesta simulação.

### Limites da simulação × implementação real
- O Falstad usa o modelo **ideal** do HP, sem ruído, variação entre dispositivos nem perda lenta de estado (*drift*), que
  existem em memristores reais.
- O estímulo é uma fonte elétrica manual, não um sensor. Num protótipo real, um circuito transformaria o sinal do
  acelerômetro num pulso de amplitude e duração controladas.
- A leitura do estado também passa corrente pelo memristor. Seria preciso ler com tensão bem baixa e por pouco
  tempo, para não alterar o registro.
- **Não foi construído hardware.** Esta é uma avaliação da contribuição potencial, como pede o enunciado.

### Conclusão
A simulação demonstrou as duas propriedades que interessam ao projeto: o memristor **muda de estado com o estímulo**
e **mantém esse estado sem energia**, além de poder ser **zerado** com um pulso reverso. Com os parâmetros padrão, a
mudança foi completa já no primeiro pulso. Por isso, na forma testada, o dispositivo serve como um marcador de
"impacto registrado / reparo feito" para cada trecho de rua, e não como contador de impactos, que exigiria pulsos mais
curtos e calibração. Como sinalizador, ele complementa o módulo IoT do Cidade em Ordem, porque preserva o evento
mesmo que o equipamento do caminhão desligue antes de transmitir.

## 5. Reprodução
- Circuito em texto (Falstad → File → Import From Text):
```
$ 1 0.000005 10.20027730826997 50 5 43 5e-11
v 128 352 128 176 0 0 40 0 0 0 0.5
m 128 176 320 176 0 100 16000 0 1e-8 1e-10
r 320 176 320 352 0 100
w 320 352 128 352 0
g 128 352 128 384 0 0
```
- Para cada etapa: clicar duas vezes na fonte, alterar *Voltage* e ler R passando o mouse sobre o memristor.
- Passo a passo completo: `ROTEIRO_FALSTAD.md`
- ⬜ Link do circuito (Falstad → File → Export As Link), opcional
