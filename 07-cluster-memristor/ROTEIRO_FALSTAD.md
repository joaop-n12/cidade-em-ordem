# Roteiro da simulação no Falstad (cerca de 30 minutos)

Site: https://www.falstad.com/circuit/circuitjs.html

## Ideia do experimento
O memristor é um resistor com **memória**: a resistência muda conforme a carga que passou por ele e
**continua no novo valor quando a tensão é retirada**. No Cidade em Ordem, cada vez que o caminhão passa por um
buraco, o sensor gera um pulso elétrico. O memristor "acumula" esses impactos e guarda a informação mesmo sem
energia. Ele funciona como um contador analógico de quantas vezes aquele trecho deu problema.

- Pulso **positivo** = impacto detectado (a resistência **cai**, de R_off em direção a R_on)
- Retirar a tensão = caminhão saiu do buraco (a resistência **deve ficar** onde parou: memória)
- Pulso **negativo** = buraco consertado, o registro é "zerado" (a resistência volta a subir)

## Montagem (manual, mais segura)
1. Abra o link acima. Menu **File → New Blank Circuit**.
2. **Draw → Inputs and Sources → Add DC Voltage Source** (fonte V1). Coloque na vertical à esquerda.
3. **Draw → Passive Components → Add Memristor**. Ligue o polo + da fonte ao memristor.
4. **Draw → Passive Components → Add Resistor** (R_s = 100 Ω, resistor de medição de corrente). Ligue em série depois do memristor.
5. Feche o circuito com fios (**Draw → Add Wire**) até o polo − da fonte e adicione **Draw → Outputs and Labels → Add Ground** no polo −.
6. Clique duas vezes no memristor e anote os parâmetros. Padrão esperado: R_on = 100 Ω, R_off = 16 kΩ, largura total
   10 nm, mobilidade 1e-10 m²/(s·V). Se forem diferentes, anote os valores que aparecerem.
7. Clique com o botão direito no memristor e escolha **View in Scope**. Depois, no escopo, clique com o botão direito e
   ative a exibição de **tensão** e **corrente**.
8. Passe o mouse sobre o memristor: no canto inferior direito aparecem **I, Vd e R** (resistência atual).
   **É esse R que vamos registrar.**

### Alternativa: importar pronto
**File → Import From Text**, cole o texto abaixo e clique OK. Se der erro, use a montagem manual acima.
```
$ 1 0.000005 10.20027730826997 50 5 43 5e-11
v 128 352 128 176 0 0 40 0 0 0 0.5
m 128 176 320 176 0 100 16000 0 1e-8 1e-10
r 320 176 320 352 0 100
w 320 352 128 352 0
g 128 352 128 384 0 0
```

## Ensaios (a tensão é mudada clicando duas vezes na fonte V1 → "Voltage")
Para cada linha, ajuste a tensão, espere cerca de 2 segundos de simulação e **anote R** passando o mouse no memristor.
Tire **print** de cada etapa.

| Etapa | Tensão V1 | Significado no CitizenTech | O que observar |
|---|---|---|---|
| 0 | 0 V | Rua sem buraco, estado inicial | R inicial (deve estar perto de R_off) |
| 1 | +1 V por ~1 s, depois 0 V | **Condição A:** impacto moderado | R durante o pulso e **R depois de voltar a 0 V** |
| 2 | 0 V por ~3 s | Caminhão já passou | R continua igual? (**persistência**) |
| 3 | +1 V por ~1 s, depois 0 V | 2ª passagem pelo mesmo buraco | R cai mais? (acúmulo) |
| 4 | +3 V por ~1 s, depois 0 V | **Condição B:** impacto severo | R cai mais rápido/mais que no +1 V? |
| 5 | 0 V por ~3 s | Sem estímulo | R permanece? |
| 6 | −3 V por ~1 s, depois 0 V | Buraco consertado (reset) | R volta a subir em direção a R_off? |

Dica: se a resistência mudar rápido demais e saturar logo em R_on, use pulsos menores (+0,3 V e +1 V) ou aumente a
"total width" do memristor para 1e-7. Se mudar devagar demais, aumente a tensão ou o tempo. **Anote o que mudar.**

## Exportar para o relatório
- **File → Export As Link**: copie o link e cole no relatório (campo "Reprodução").
- **File → Export As Text**: salve como `circuito_memristor.txt` nesta pasta.
- Prints: salve em `prints/` (etapa0.png, etapa1.png...).
