# 📖 Teoria — Simulação de Estabilidade Transitória com ANATEM

**Documento complementar ao README:** explicações teóricas sobre estabilidade, eventos, modelos, CDU e simulação.

---

## 📚 Índice

1. [Simulação de Estabilidade Transitória](#simulação-de-estabilidade-transitória)
2. [Estrutura de um Arquivo .stb](#estrutura-de-um-arquivo-stb)
3. [Eventos e Perturbações](#eventos-e-perturbações)
4. [Modelos Dinâmicos de Máquinas](#modelos-dinâmicos-de-máquinas)
5. [Controladores Definidos pelo Usuário (CDU)](#controladores-definidos-pelo-usuário-cdu)
6. [FACTS e HVDC](#facts-e-hvdc)
7. [Pipeline de Simulação](#pipeline-de-simulação)
8. [Validação e Pós-Processamento](#validação-e-pós-processamento)

---

## Simulação de Estabilidade Transitória

### O que é?

**Estabilidade transitória** é a capacidade de um sistema de potência manter o sincronismo após uma **perturbação severa** (como um curto-circuito ou perda de linha).

A simulação transitória resolve as **equações dinâmicas** do sistema em pequenos passos de tempo:

$$\frac{dx}{dt} = f(x, u, t)$$

Onde:
- **x** = estado do sistema (ângulo, velocidade, tensão, etc.)
- **u** = entrada (referência de controle, demanda de carga)
- **t** = tempo

### Por que é importante?

1. **Segurança operacional** — Verifica se o sistema se recupera após falhas
2. **Dimensionamento de controles** — Testa estabilizadores e reguladores
3. **Planejamento de expansão** — Avalia impacto de novas linhas/geradores
4. **Operação em tempo real** — Previne apagões em cascata

### Escala Temporal

| Evento | Duração | Fenômeno |
|--------|---------|----------|
| **Transitório rápido** | 0–2 segundos | Oscilaçõeseletromecânicas, desconexão de linhas |
| **Transitório médio** | 2–10 segundos | Atuação de controladoras (PSS, AVR) |
| **Transitório lento** | 10–60 segundos | Recuperação de voltagem, resposta de carga |

---

## Estrutura de um Arquivo .stb

Um arquivo `.stb` contém 10 blocos principais:

### 1. DARQ (Data ARQuivos)
Associa arquivos externos:
```
 DARQ
 'rede.sav'                         / Arquivo SAV (ANAREDE)
 'resultado.plt'                    / Arquivo PLT (saídas)
 'resultado.rela'                   / Arquivo RELA (relatório)
 'controladores.cdu'                / Arquivo CDU (controladores)
```

### 2. DOPC (Dados de OPção de Cálculo)
Opções globais de simulação:
```
 DOPC
 0    0    0.0                       / FREQ=60Hz, BASE=100MVA
```

### 3. DSIM (Dados de SIMulação)
Parâmetros da simulação:
```
 DSIM
 0.0   30.0   0.01   0.1   1000   10    / tfim=30s, delt=0.01s
```

### 4. DEVT (Dados de EVenTo)
Eventos durante a simulação:
```
 DEVT
 1   1001   1.0    0.1   99.0   0.0    / Curto em barra 1001 (t=1.0s, duracao=0.1s)
 2   1201   1202   1   2.0    0.1     / Abertura linha 1201-1202 (t=2.0s)
```

### 5. DPLT (Dados de PLotagem)
Variáveis para saída:
```
 DPLT
 T  1001    0    0    0    0   / Tensão em barra 1001
 A  1001    1    0    0    0   / Ângulo gerador unidade 1 na barra 1001
 P  1201 1202    1    0    0   / Potência ativa na linha 1201-1202
```

### 6. DMDG (Dados de Modelo DinâmicoGerador)
Modelos predefinidos (MD01, MD02, MD03):
```
 DMDG
 'MD01'  MD01_1   ...  / Modelo MD01 com parâmetros
```

### 7. DMAQ (Dados de MAQuina)
Associação máquina ↔ modelo:
```
 DMAQ
 1001   1    'MD01_1'   ...   / Máquina barra 1001, unidade 1, modelo MD01_1
```

### 8. DFAC (Dados de FACTS)
Controladores FACTS (SVC, TCSC, STATCOM):
```
 DFAC
 SVC   1001   ...   / SVC em barra 1001
```

### 9. DHVD (Dados de HVDC)
Elos de transmissão HVDC:
```
 DHVD
 'LINK1'   1001   2001   ...  / Elo HVDC entre barras
```

### 10. DCDU (Dados de CDU)
Controladores definidos pelo usuário:
```
 DCDU
 'AVR1'    ...   / Regulador de voltagem personalizado
 'PSS1'    ...   / Estabilizador de potência personalizado
```

---

## Eventos e Perturbações

### Tipos de Eventos Suportados

#### 1. Curto-Circuito (IFAULT = 1)
```python
caso.curto_barra(barra=1001, tempo_inicio=1.0, tempo_fim=1.1)
```
**Física:** Reduz tensão em uma barra a ~0, aplicando impedância de falta

#### 2. Abertura de Linha (IFAULT = 2)
```python
caso.curto_circuito(de=1201, para=1202, circuito=1, 
                    tempo_inicio=2.0, tempo_fim=2.1)
```
**Física:** Remove linha (abre disjuntor), isolando barra remota

#### 3. Chaveamento de Impedância (IFAULT = 5)
**Física:** Muda resistência/reatância (ex: insert reactor em linha)

#### 4. Step em Referência (IFAULT = 7)
**Física:** Muda setpoint de controle (ex: aumento de demanda)

---

## Modelos Dinâmicos de Máquinas

### MD01 — Máquina Síncrona Clássica
**Parâmetros essenciais:**
- **H** = Inércia (constante de tempo)
- **KD** = Amortecimento
- **Xd, X'd** = Reatâncias de eixo direto
- **Tdo'** = Constante de tempo transitória

**Equações (simplificadas):**
$$2H \frac{d\omega}{dt} = P_m - P_e - D(\omega - \omega_0)$$

Onde:
- **ω** = velocidade angular
- **Pm** = potência mecânica (turbina)
- **Pe** = potência elétrica
- **D** = coeficiente de amortecimento

### MD02 — Máquina com Regulador Automático de Voltagem (AVR)
Adiciona dinâmica do excitador:
$$\frac{dE'}{dt} = \frac{1}{T_e}(V_{ref} - V_{terminal} - E')$$

### MD03 — Máquina com AVR + Estabilizador de Potência (PSS)
Adiciona feedback de velocidade para melhorar amortecimento:
$$V_{PSS} = K_{PSS} \cdot (\omega - \omega_0)$$

---

## Controladores Definidos pelo Usuário (CDU)

### O que é CDU?

**CDU** = código que descreve um controlador personalizado (AVR, PSS, controle de FACTS, etc.)

### Blocos Básicos

#### 1. IMPORT
```
IMPORT input_1 input_2
```
Lê sinais do sistema (voltagem, corrente, velocidade, etc.)

#### 2. EXPORT
```
EXPORT output_1 output_2
```
Envia sinais de controle (referência de tensão, reativo, etc.)

#### 3. LOGIC (operações lógicas)
```
IF (sinal_1 > limite) THEN saida = 1 ELSE saida = 0
```

#### 4. COMPAR (comparadores)
```
COMPAR sinal_1 sinal_2
saida = 1 se sinal_1 > sinal_2
```

#### 5. INPUT (ganho/filtro)
```
INPUT sinal_entrada
saida = K * sinal_entrada
```

#### 6. SERIET (atraso de tempo)
```
SERIET sinal
saida = sinal com atraso de 0.1s
```

### Exemplo Prático: Regulador Automático de Voltagem (AVR)

```python
from pyanatem.cdu import ControladorCDU

avr = ControladorCDU(numero=1, nome="AVR_SIMPLES")

# Ler tensão terminal
avr.bloco_import(101, "V_TERMINAL")

# Regulador proporcional
avr.bloco_ganho(201, "REGULADOR", ganho=100)

# Limitar saída entre -1 e +1
avr.bloco_limiter(301, "LIMITE_AVR", vmin=-1, vmax=1)

# Enviar para campo da máquina
avr.bloco_export(401, "EFD")
```

---

## FACTS e HVDC

### FACTS (Flexible AC Transmission Systems)

#### SVC (Static Var Compensator)
- **Função:** Injetar/absorver reativo para controlar tensão
- **Equação:** Q = G*V² + B*V (barrrado)
- **Dinâmica:** Rápida (< 100ms)

#### TCSC (Thyristor-Controlled Series Capacitor)
- **Função:** Alterar impedância de linha série
- **Equação:** X_efetiva = X_nominal * (1 - β)
- **Dinâmica:** Rápida (< 50ms)

#### STATCOM (Static Compensator)
- **Função:** Fonte de corrente para controlar tensão/ângulo
- **Equação:** I_d = K*V_error
- **Dinâmica:** Muito rápida (< 20ms)

### HVDC (High Voltage Direct Current)

**Característica principal:** Permite fluxo de potência controlável entre dois pontos

**Controles:**
1. **Lado transmissão:** Injetor de corrente (I_dc = referência)
2. **Lado recepção:** Controlador de tensão (V_dc = referência)

**Vantagem:** Amortecimento rápido de oscilações (< 100ms)

---

## Pipeline de Simulação

### Passo 1: Preparação
```python
caso = CasoAnatem.ler("base.stb")
caso.validar()  # Verifica consistência
caso.exportar("caso_simulacao.stb")
```

### Passo 2: Execução
```bash
anatem.exe caso_simulacao.stb
# Resolve equações dinâmicas:
# - Fluxo de potência no t=0 (condição inicial)
# - Integração stepwise: dt = 0.01s
# - Aplica eventos (curtos, aberturas, etc.)
# - Sampl variáveis de saída
```

### Passo 3: Análise de Resultados
```python
from pyanatem.posprocessamento import LeitorPLT

plt = LeitorPLT.ler("resultado.plt")
tensoes = plt.valores("V", barra=1001)
angles = plt.valores("A", barra=1001, unidade=1)

# Critério de estabilidade:
# Se ângulo volta a estabilizar após 30s → estável
# Se ângulo diverge → instável
```

---

## Validação e Pós-Processamento

### Validações Automáticas

1. **Consistência de eventos**
   - Tempo final (tfim) deve ser ≥ tempo de último evento

2. **Compatibilidade máquina-modelo**
   - Cada máquina em DMAQ deve ter modelo definido em DMDG

3. **Arquivos associados**
   - SAV deve existir
   - PLT/RELA devem ser caminhos válidos

4. **Encoding**
   - Todos os caracteres em latin-1 (sem acentuação especial)

### Pós-Processamento

#### Extrair Variável Específica
```python
plt = LeitorPLT.ler("resultado.plt")
v_1001 = plt.valores("T", barra=1001)  # Tensão na barra 1001
```

#### Exportar para DataFrame (pandas)
```python
df = plt.para_dataframe()
# Colunas: tempo, variavel_1, variavel_2, ...
df.plot(x="tempo", y=["T_1001", "A_1001"])
```

#### Análise de Estabilidade
```python
# Critério: ângulo deve permanecer < 90° durante falta
for angulo in angles:
    if abs(angulo) > 90:
        print("⚠️ INSTÁVEL!")
        break
else:
    print("✅ ESTÁVEL")
```

---

## Exemplo Completo: Análise de Estabilidade

```python
from pyanatem import CasoAnatem, EnsaioAnatem
from pyanatem.posprocessamento import LeitorPLT

# Passo 1: Preparar caso base
caso = CasoAnatem.ler("sistema_original.stb")
caso.dsim.tfim = 30.0  # Simular 30 segundos

# Passo 2: Adicionar curto-circuito na barra crítica
caso.curto_barra(barra=2001, tempo_inicio=1.0, tempo_fim=1.1)

# Passo 3: Adicionar saídas de interesse
caso.dplt.tensao_barra(2001)
caso.dplt.angulo_maquina(2001, unidade=1)

# Passo 4: Validar e exportar
erros = caso.validar()
if erros:
    print("AVISO:", erros)
else:
    caso.exportar("analise_estabilidade.stb")

# Passo 5: Executar ANATEM
import subprocess
subprocess.run(["anatem.exe", "analise_estabilidade.stb"])

# Passo 6: Analisar resultados
plt = LeitorPLT.ler("resultado.plt")
tensoes = plt.valores("T", barra=2001)
angulos = plt.valores("A", barra=2001, unidade=1)

# Critério: voltagem deve recuperar para > 0.95 pu dentro de 5s
tempo_critico = 5.0
if max(tensoes[:int(tempo_critico/0.01)]) > 0.95:
    print("✅ Sistema estável!")
else:
    print("❌ Sistema instável!")
```

---

## Glossário

| Termo | Significado |
|-------|------------|
| **Barra** | Nó da rede elétrica |
| **Circuito** | Linha entre duas barras (pode haver múltiplas) |
| **Evento** | Perturbação (curto, abertura, step) |
| **Roundtrip** | Ler → modificar → escrever sem perda |
| **Convergência** | Sistema encontra novo equilíbrio |
| **Instabilidade** | Ângulo/voltagem divergem indefinidamente |
| **AVR** | Automatic Voltage Regulator |
| **PSS** | Power System Stabilizer |
| **CDU** | Controlador Definido pelo Usuário |
| **FACTS** | Flexible AC Transmission Systems |
| **HVDC** | High Voltage Direct Current |

---

## Referências

1. **Manual ANATEM v12.10** (CEPEL)
   - Capítulo 8: Estrutura de eventos
   - Capítulo 25-27: FACTS e HVDC
   - Capítulo 29: CDU (Controladores)

2. **Textos Clássicos:**
   - Kundur, P. *Power System Stability and Control* (McGraw-Hill)
   - Sauer, P. W. *Power System Dynamics and Stability* (Prentice Hall)

3. **Padrões IEC:**
   - IEC 61000-4-27: Robustez de equipamentos a variações de voltagem

---

**Última atualização:** 2026-07-10  
**Versão:** v1.0.0  
**Licença:** MIT
