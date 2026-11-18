# Memória resistiva para registrar impactos de buracos: simulação de memristor no Falstad

**Cluster Computing, Computação Neuromórfica e Supercomputadores** · Global Solution 2026.2
**Projeto CitizenTech:** Cidade em Ordem

| Integrante | RM |
|---|---|
| João Pedro de Souza Nunes | RM567318 |
| Guilherme Nakamura | RM567460 |

> **Atenção:** os campos marcados com ⬜ devem ser preenchidos com os valores observados na simulação feita pelo
> grupo (ver `ROTEIRO_FALSTAD.md`). Não preencha com valores esperados: o enunciado avalia evidências reais e
> pede que, se o modelo não se comportar como esperado, isso seja descrito.

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

**Topologia:** fonte de tensão V1 (representa o pulso gerado pelo sensor hipotético) → memristor M1 → resistor de
medição R_s = 100 Ω → terra. O estado é acompanhado pela **resistência do memristor** (valor R exibido pelo Falstad
ao passar o mouse sobre M1) e pela corrente no escopo.

⬜ **Captura do circuito:** inserir print legível do Falstad.

| Componente | Parâmetro | Valor usado | Unidade |
|---|---|---|---|
| V1 (fonte DC, ajustada a cada ensaio) | Tensão | 0 / +1 / +3 / −3 | V |
| M1 (memristor) | R_on | ⬜ | Ω |
| M1 | R_off | ⬜ | Ω |
| M1 | Largura total (D) | ⬜ | m |
| M1 | Mobilidade dos dopantes (μ) | ⬜ | m²/(s·V) |
| R_s | Resistência | 100 | Ω |
| Simulação | Passo de tempo | ⬜ | s |

## 3. Ensaios

| Etapa | Estímulo | Significado | R antes (Ω) | R durante (Ω) | R após retirar a tensão (Ω) |
|---|---|---|---|---|---|
| 0 | 0 V | estado inicial | ⬜ | – | – |
| 1 | +1 V, ~1 s | **Condição A:** impacto moderado | ⬜ | ⬜ | ⬜ |
| 2 | 0 V, ~3 s | sem estímulo (persistência) | ⬜ | – | ⬜ |
| 3 | +1 V, ~1 s | 2º impacto no mesmo ponto | ⬜ | ⬜ | ⬜ |
| 4 | +3 V, ~1 s | **Condição B:** impacto severo | ⬜ | ⬜ | ⬜ |
| 5 | 0 V, ~3 s | sem estímulo (persistência) | ⬜ | – | ⬜ |
| 6 | −3 V, ~1 s | reparo (reset) | ⬜ | ⬜ | ⬜ |

⬜ Prints das etapas 1, 2, 4 e 6 (escopo de tensão e corrente e o valor R).

**Comparação A × B:** ⬜ (descrever: a variação de R no pulso de +3 V foi maior ou mais rápida que no de +1 V? Quanto?)

## 4. Análise e conclusão

### Explicação física (base para comparar com o observado)
No modelo de memristor do HP Labs, usado pelo Falstad, o dispositivo é uma camada fina de TiO₂ de largura D com uma
região dopada de largura w. A resistência total é

  R(w) = R_on·(w/D) + R_off·(1 − w/D)

e a fronteira entre as regiões se move com a corrente: dw/dt = μ·R_on·i(t)/D.

Consequências esperadas:
- **Corrente positiva** aumenta w, a região de baixa resistência cresce e **R cai**.
- **Tensão maior** gera corrente maior e w se move **mais rápido**. Por isso a condição B deve alterar R mais que a A no mesmo tempo.
- **Sem corrente** (V = 0), dw/dt = 0 e **w fica parado**: a resistência é mantida. Essa é a memória não volátil.
- **Corrente negativa** move w de volta e **R sobe** (reset).
- R fica limitado entre R_on e R_off: pulsos sucessivos acumulam até **saturar**.

⬜ **Interpretação do que foi observado:** comparar as medições com o comportamento esperado acima. Se a resistência
**não** se manteve ao retirar a tensão, ou se saturou logo no primeiro pulso, descrever isso e explicar a provável causa
(parâmetros, passo de tempo, modelo ideal).

### Contribuição para o Cidade em Ordem
- **Contador de impactos sem energia:** cada trecho da rota teria uma célula de memória que acumula impactos. Se o
  caminhão desligar ou perder conexão, o registro continua.
- **Filtro de falso positivo na borda:** só quando R cai abaixo de um limiar (vários impactos) o ESP32 envia o evento de
  "buraco confirmado". Isso reduz mensagens MQTT e falsos alarmes de lombadas.
- **Reset após reparo:** o pulso negativo "esquece" o buraco quando a ordem de serviço é concluída.

### Limites da simulação × implementação real
- O Falstad usa o modelo **ideal** do HP, sem ruído, variação entre dispositivos nem perda lenta de estado (*drift*), que
  existem em memristores reais.
- O estímulo é uma fonte elétrica, não um sensor. Num protótipo real, um circuito condicionaria o sinal do
  acelerômetro (amplitude proporcional ao impacto) antes do memristor.
- Seriam necessárias uma célula por trecho de rota (matriz *crossbar*) e um circuito de leitura com tensão baixa, para que
  a própria leitura não altere o estado.
- **Não foi construído hardware.** Esta é uma avaliação da contribuição potencial, como pede o enunciado.

⬜ **Conclusão do grupo** (escrever com suas palavras: o que funcionou, o que não funcionou e se a ideia faz sentido
para o projeto).

## 5. Reprodução
- ⬜ Link do circuito (Falstad → File → Export As Link):
- Arquivo de texto do circuito: `circuito_memristor.txt` (exportar pelo Falstad → File → Export As Text)
- Passo a passo completo: `ROTEIRO_FALSTAD.md`
