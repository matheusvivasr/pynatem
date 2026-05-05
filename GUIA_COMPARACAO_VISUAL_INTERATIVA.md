# 📊 Guia Interativo de Comparação Visual — PDF vs Markdowns

**Objetivo:** Você fornece screenshots do PDF e eu comparo com os markdowns  
**Status:** 🟡 Aguardando seus prints/screenshots do PDF  
**Formato:** Passo a passo com templates prontos

---

## 🎯 Qual é o Objetivo?

Você quer validar se os **exemplos de código** (Listagens 46.X, etc) nos markdowns correspondem visualmente ao PDF original do Manual ANATEM 12.10.

**Razão:** Detectar se há erros de interpretação/OCR na transcrição.

---

## 📋 Processo de Comparação

### Passo 1: Identifique uma Listagem no PDF

**Você faz:**
1. Abra o PDF Manual ANATEM 12.10
2. Localize uma "Listagem 46.X" (ex: Listagem 46.1, Listagem 46.14)
3. Faça um screenshot da listagem
4. Envie para mim

**Que eu faço:**
- Localizo a mesma listagem nos markdowns
- Comparo lado a lado
- Identifico discrepâncias

---

## 🖼️ Exemplo de Screenshot Ideal

```
┌─────────────────────────────────────────────┐
│ Manual ANATEM Release 12.10        [PDF]    │
├─────────────────────────────────────────────┤
│                                             │
│ Listagem 46.1: Exemplo ACDE                │
│                                             │
│ 1 (=============                            │
│ 2 ( IMPORTACAO DOS ARQUIVOS                │
│ 3 (=============                            │
│ 4 ACDE                                      │
│ 5 (---- Nome do Arquivo                    │
│ 6 .\Modelos\HVDC\CONTROLADOR.cde           │
│ 7 .\Empreendimentos\Eolicas\ITUMB.cde      │
│ 8 999999                                    │
│                                             │
└─────────────────────────────────────────────┘
```

---

## 📌 Checklist do Que Procurar no PDF

Ao fazer o screenshot, verifique:

- [ ] **Numeração:** Como as linhas são numeradas? (1, 2, 3... ou nada?)
- [ ] **Formatação:** Há itálico, negrito ou sublinhado?
- [ ] **Espaçamento:** As linhas estão separadas ou juntas?
- [ ] **Caracteres especiais:** Há parênteses, backticks ou underscores?
- [ ] **Alinhamento:** O código está alinhado à esquerda ou indentado?
- [ ] **Fonte:** Qual é a fonte usada? (monospace, sans-serif, etc)

---

## 🔍 Templates de Análise

### Template A: Análise de Linha

```
┌─ PDF (Original)
│  Linha 1: "( IMPORTACAO DOS ARQUIVOS"
│  Linha 2: "( DO CÓDIGO DCDU"
│
└─ Markdown (Atual)
   Linha 1: "1 _`( IMPORTACAO DOS ARQUIVOS`_"
   Linha 2: "2 _`( DO CÓDIGO DCDU`_"

DIFERENÇAS:
✋ Números de linha adicionados
✋ Itálico (_..._) adicionado
✋ Backticks adicionados
✋ Espaçamento alterado

CONCLUSÃO: ❌ Não corresponde
```

### Template B: Análise de Formatação

```
ELEMENTO          | PDF       | Markdown  | Match?
───────────────────────────────────────────────
Comentário (      | Não       | _`(_      | ❌
Números (1, 2...) | Não       | Sim       | ❌
Itálico           | Não       | Sim       | ❌
Backticks         | Não       | Sim       | ❌
Espaçamento       | Separado  | Junto     | ❌
```

---

## 📸 Como Enviar Screenshots

**Opção 1: Descrever Visualmente**
```
Listagem 46.1 no PDF aparece assim:

( COMENTARIO
CODIGO
PARAMETRO
999999

Sem números de linha, sem itálico, sem backticks
```

**Opção 2: Enviar Screenshot**
- Tire screenshot da Listagem no PDF
- Cole na próxima mensagem
- Diga qual é a Listagem (46.1, 46.14, etc)

**Opção 3: Descrever o Padrão**
```
PDF Listagem 46.X:
- Linhas separadas? SIM/NÃO
- Numeradas 1, 2, 3...? SIM/NÃO
- Tem itálico? SIM/NÃO
- Comentários têm "("? SIM/NÃO
```

---

## 🎯 Exemplos de Possíveis Erros

### Erro Tipo A: Concatenação

**PDF (correto):**
```
1 ( COMENTARIO
2 CODIGO
3 999999
```

**Markdown (errado):**
```
1 _`( COMENTARIO`_ 2 `CODIGO` 3 `999999`
```

### Erro Tipo B: Formatação Extra

**PDF (correto):**
```
DCDU
100 CDU_EXEMPLO
```

**Markdown (errado):**
```
`DCDU`
_`100 CDU_EXEMPLO`_
```

### Erro Tipo C: Quebra de Linha

**PDF (correto):**
```
( DEFINICAO DO MODELO
( REPRESENTANDO O CONTROLE
```

**Markdown (errado):**
```
_`( DEFINICAO DO MODELO`_ _`( REPRESENTANDO O CONTROLE`_
```

---

## 📊 Matriz de Decisão

Após comparar PDF vs Markdown, use esta matriz:

```
┌─ Formato nas Linhas
│  ├─ Idêntico? → ✅ OK, nenhuma ação
│  └─ Diferente?
│     ├─ Formatação extra (_`...`_)? → ❌ Erro de transcrição
│     ├─ Linhas concatenadas? → ❌ Erro de OCR
│     ├─ Números adicionados? → ❌ Erro de interpretação
│     └─ Espaçamento alterado? → ⚠️ Menor, mas corrigir
│
└─ Se encontrou diferenças?
   ├─ Corrigir markdowns
   └─ Aplicar mesmo padrão a todas as Listagens 46.X
```

---

## 🔧 Próximos Passos

**Você:**
1. Abra PDF Manual ANATEM 12.10
2. Localize Listagem 46.1 (ACDE) — é a primeira
3. Compare com `markdowns_reference/22_cap46_codigos_execucao_geral.md` linha ~51
4. Descreva as diferenças (use template acima)

**Eu:**
1. Recebo sua análise
2. Crio script de correção se necessário
3. Aplico a TODOS os exemplos nos markdowns
4. Valido resultado

---

## 💡 Dica Rápida

Se não tiver o PDF à mão, pode descrever assim:

```
"Listagem 46.1 no PDF:
- Tem linhas numeradas? [SIM/NÃO]
- Estão separadas? [SIM/NÃO]
- Tem itálico/negrito? [SIM/NÃO]
- Comentários começam com '('? [SIM/NÃO]"
```

E eu já identifiquei o padrão de erro!

---

## 📋 Checklist Final

- [ ] Tenho acesso ao PDF Manual ANATEM 12.10
- [ ] Localizei Listagem 46.1 (ACDE)
- [ ] Tirei screenshot ou descrevi o formato
- [ ] Comparei com markdown
- [ ] Identifiquei diferenças

**Se sim em tudo acima → Envie sua análise!**

---

**Status:** ⏳ Aguardando seus prints/descrição do PDF para proceder com comparação visual
