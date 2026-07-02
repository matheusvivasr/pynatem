# Plano de Trabalho — v2.1.0 Pós-processamento Consolidado

**Objetivo:** Completar a narrativa v1.4 (nunca formalizada). Integrar leitura de
resultados binários e estruturados do ANATEM.

**Status:** Em Andamento 🚀

---

## v2.1.1 — Leitor `.plt` Binário

**Meta:** Engenharia reversa completa de `plt_binario.py` (107 linhas, 79% cobertura)

### Tarefas

- [x] **T2.1.1.1** Analisar `plt_binario.py` — estrutura de bytes, formatação de floats ✅ (2026-07-12)
- [x] **T2.1.1.2** Criar testes com exemplos oficiais (`.plt` binário real do CEPEL) ✅ (2026-07-12)
  - 4 testes de parser (assinatura, filename, header, variáveis)
- [ ] **T2.1.1.3** Parser de cabeçalho — validar dimensões e metadados
- [ ] **T2.1.1.4** Parser de corpo — série temporal, valores numéricos, precisão (FASE 2)
- [ ] **T2.1.1.5** Integração com `LeitorPLT` — `ler_binario()` funcional
- [ ] **T2.1.1.6** Testes de roundtrip — binário → DataFrame (pandas)
- [ ] **T2.1.1.7** Documentação — formato binário ANATEM em TEORIA.md

**Deps:** `plt_binario.py` (79% cobertura), `posprocessamento_v2.py`, exemplos oficiais

**Status Atual:**
- ✅ Arquivo de exemplo localizado e analisado (1.6 MB, assinatura PLTx válida)
- ✅ `ler_assinatura()`, `ler_filename()`, `ler_header()` funcionais
- 4/7 tarefas concluídas (57%)

**Resultado esperado:** 
- `LeitorPLT.ler_binario(path)` com suporte completo a série temporal
- 15+ testes de conformidade (atualmente: 4 + 11 de integração)
- Cobertura `plt_binario.py` → 90%+

---

## v2.1.2 — Relatórios Estruturados (`.rel` + `.out`)

**Meta:** Análise de `posprocessamento_v2.py` (230 linhas, 0% cobertura) e integração

### Tarefas

- [ ] **T2.1.2.1** Analisar `posprocessamento_v2.py` — estrutura esperada
- [ ] **T2.1.2.2** Criar testes com `.rel` / `.out` oficiais do CEPEL
- [ ] **T2.1.2.3** Parser de `.rel` estruturado (seções, convergência, eventos)
- [ ] **T2.1.2.4** Parser de `.out` (resultados numéricos por seção)
- [ ] **T2.1.2.5** `LeitorRelatorio` estendido — `.rel` vs `.out`
- [ ] **T2.1.2.6** Análise de status de execução (sucesso/falha/avisos)
- [ ] **T2.1.2.7** Testes de conformidade contra exemplos reais

**Deps:** `posprocessamento_v2.py`, exemplos `.rel` / `.out`

**Resultado esperado:**
- `LeitorRelatorio.ler_out(path)` + `.ler_rel_estruturado()`
- 10+ testes de conformidade
- Cobertura `posprocessamento_v2.py` → 100%

---

## v2.1.3 — Snapshots + Sinal Externo (SNAP, DAVS)

**Meta:** Estados intermediários e sinais de análise

### Tarefas

- [ ] **T2.1.3.1** Analisar formato SNAP (manual Cap. 31)
- [ ] **T2.1.3.2** Criar `BlocoSNAP` — salvamento de estados
- [ ] **T2.1.3.3** Parser de snapshot — restaurar estado anterior
- [ ] **T2.1.3.4** Analisar DAVS (Sinal Externo, Cap. 32)
- [ ] **T2.1.3.5** Criar `BlocoDAVS` — sincronização com medições externas
- [ ] **T2.1.3.6** Integração com `CasoAnatem` — `gerar_snapshot()`, `restaurar_snapshot()`
- [ ] **T2.1.3.7** Testes de roundtrip (salvar → restaurar)

**Deps:** Manual ANATEM Cap. 31–32, exemplos de snapshot

**Resultado esperado:**
- `CasoAnatem.gerar_snapshot()` e `.restaurar_snapshot(path)`
- 8+ testes de conformidade
- Documentação (TEORIA.md Cap. 31–32)

---

## Critério de Aceite (v2.1.0)

- [ ] 320+ testes (295 → 320+)
- [ ] 100% cobertura `plt_binario.py` + `posprocessamento_v2.py`
- [ ] CI verde (pytest, mypy, ruff)
- [ ] Documentação atualizada (README, TEORIA.md, docs/)
- [ ] CHANGELOG.md — v2.1.0 e patches documentados
- [ ] Nenhum warning/lint

---

## Timeline Estimada

| Patch | Estimativa | Início |
|-------|---|---|
| v2.1.1 | 3–4 dias | — |
| v2.1.2 | 2–3 dias | após v2.1.1 |
| v2.1.3 | 2–3 dias | após v2.1.2 |
| **Total** | **7–10 dias** | — |

---

## Próximos Passos

1. ✅ Roadmap atualizado (ROADMAP.md)
2. ▶️ **Começar T2.1.1.1** — análise de `plt_binario.py`
3. Procurar exemplos oficiais `.plt` binário no CEPEL ou repositórios públicos
4. Iniciar estrutura de testes em `tests/test_v2_1_posprocessamento.py`
