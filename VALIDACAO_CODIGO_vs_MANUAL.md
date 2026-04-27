# 🔬 Validação: Serializadores pyanatem × Manual ANATEM 12.10 Oficial

**Data:** 2026-07-11
**Método:** Reproduzir com a API do pyanatem os MESMOS dados dos exemplos oficiais
(fontes `.rst` do manual online, espaçamento exato) e comparar char-a-char.
**Baseline:** 263 testes passando — mas os testes codificam as mesmas expectativas
do código, então **não detectam** divergência contra o manual.

---

## Resultado: 6 de 6 códigos validados apresentam divergências

### 🔴 CRÍTICO 1 — DEVT: código de evento inexistente `ABLN`

`BlocoDEVT.abertura_linha()` emite evento **`ABLN`** — esse mnemônico **não existe
no manual oficial**. O correto é **`ABCI`** (abertura de circuito CA).
O ANATEM rejeitaria o deck.

```
oficial |ABCI      .25     2    3|
gerado  |ABLN      0.2500      2      3    1      0.0000      0.0000|
```

Também divergem: largura do campo Tempo (oficial: termina na col 13; gerado: col 16),
El/Pa/Nc deslocados, e campos zerados emitidos onde o oficial deixa em branco.

**Régua oficial (§46.31):**
```
(Tp) ( Tempo)( El )( Pa)Nc( Ex) ( % ) (ABS ) Gr Uni  (Bl)P ( Rc ) ( Xc ) ( Bc ) (Defas)
```

### 🔴 CRÍTICO 2 — DSIM: campos com semântica errada

Régua oficial: `( Tmax ) (Stp) ( P ) ( I ) ( F )` — Tmax, passo, intervalo de plotagem.
O pyanatem emite `tini, tfim, delt` (três floats de 10 casas) — **ordem e significado
não correspondem à régua oficial**.

```
oficial |   10.00  .005     5|
gerado  |    0.0000   10.0000    0.0050|
```

### 🟠 DMAQ (§46.41): larguras de campo deslocadas

Nb usa 6 colunas (oficial: 5); Mg/Mt/Mv/Me acumulam 1–2 colunas de deslocamento.
Em formato posicional fixo, o ANATEM leria valores errados.

```
oficial | 1432   10                751|
gerado  |  1432  10               751|
oficial | 3500   10  60  60   3    753     78    126    144u|
gerado  |  3500  10  60  60   3   753    78    126    144u|
```

### 🟠 DCAR (§46.14): parâmetros A/B/C/D fora das colunas fixas

A seleção (passada literal) fica correta, mas A/B/C/D devem começar em coluna fixa
(~53). O pyanatem os emite logo após a seleção. Também emite `Vmn=70` default onde
o oficial deixa em branco.

```
oficial |BARR     1 A BARR  9998                             100   0   0 100|
gerado  |BARR     1 A BARR  9998  100  0  0  100  70|
```

### 🟠 DLTC (§46.40): coluna extra Nc + caixa do flag 'u'

- Emite `Nc=1` default onde o oficial deixa em branco
- Flag CDU em maiúscula `U` (oficial usa `u` minúsculo — verificar se ANATEM aceita)
- Larguras deslocadas

```
oficial |    4       2         1               40|
gerado  |     4     2   1      1                   40|
oficial |    1       2      5300u               1|
gerado  |     1     2   1  5300U                    1|
```

### 🟡 DFLA (§46.33): 1 coluna de deslocamento + Nc default

```
oficial |  20 FRJ - Area RJ|          (NA em 4 colunas)
gerado  |   20  FRJ - Area RJ|        (NA em 5 colunas)
oficial |  385   149|                 (Nc em branco)
gerado  |   385   149  1|             (Nc=1 emitido)
```

---

## 📌 Diagnóstico

1. **Causa raiz:** as larguras de campo foram inferidas das transcrições markdown
   ANTES da correção das listagens — as transcrições antigas haviam **colapsado o
   espaçamento** dos exemplos, impossibilitando derivar as colunas corretas.
2. **Os 263 testes passam** porque foram escritos a partir do mesmo código —
   validam consistência interna, não conformidade com o manual.
3. Agora que os markdowns têm os exemplos oficiais com espaçamento exato
   (421 listagens corrigidas), é possível corrigir os serializadores com precisão.

## 🎯 Plano de correção sugerido (antes da v2.0)

| Prioridade | Item | Ação |
|-----------|------|------|
| 1 | DEVT `ABLN`→`ABCI` | Renomear mnemônico (bug funcional) |
| 2 | DSIM | Reescrever com campos oficiais (Tmax, Stp, P, I, F) |
| 3 | DEVT colunas | Ajustar régua (Tempo 8 col, El 6, Pa 5, Nc 2...) |
| 4 | DMAQ larguras | Nb=5, ajustar Mg/Mt/Mv/Me conforme régua oficial |
| 5 | DCAR colunas | A/B/C/D em colunas fixas; Vmn opcional |
| 6 | DLTC/DFLA | Campos opcionais em branco; larguras; flag 'u' |
| 7 | Testes | Atualizar expectativas para o formato oficial |
| 8 | Demais 46 serializadores | Auditar com o mesmo método (réguas oficiais em cache) |

**Infra pronta:** os fontes oficiais com espaçamento exato estão em cache
(`scratchpad/rst/`, 899 blocos) e o script de validação (`validar_serializadores.py`)
é reutilizável como teste de conformidade.
