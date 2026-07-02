# Plano de Trabalho — v2.1.0 Pós-processamento Consolidado

**Objetivo:** Completar a narrativa v1.4 (nunca formalizada). Integrar leitura de
resultados binários e estruturados do ANATEM.

**Status:** Em Andamento 🚀

---

## v2.1.1 — Leitor `.plt` Binário (FASE 1 Completa, FASE 2 Pendente)

**Meta:** Parser de header do `.plt` binário (engenharia reversa)

### Tarefas

- [x] **T2.1.1.1** Analisar `plt_binario.py` — estrutura de bytes ✅ (2026-07-12)
- [x] **T2.1.1.2** Criar testes com exemplos oficiais ✅ (2026-07-12)
  - 4 testes de parser (assinatura, filename, header, variáveis)
- [x] **T2.1.1.3** Parser de cabeçalho — assinatura, filename, catálogo ✅ (2026-07-12)
- ⏳ **T2.1.1.4** Parser de corpo — FASE 2 (requer mais exemplos do CEPEL)
  - ⚠️ Formato binário de série temporal é proprietário e complexo
  - Requer validação contra múltiplos arquivos reais
  - Adiado para iteração futura (com exemplos adicionais)
- [x] **T2.1.1.5** Fallback integrado — usar `posprocessamento_v2.py` como alternativa ✅
- [x] **T2.1.1.6** Documentação — status claramente documentado em código ✅
- ⏳ **T2.1.1.7** Roadmap: "FASE 2 aguardando exemplos adicionais" — anotado ✅

**Deps:** `plt_binario.py` (79% cobertura), `posprocessamento_v2.py` (67%)

**Status Atual:**
- ✅ FASE 1 (header) — 100% completa
- ✅ Arquivo de exemplo analisado (1.6 MB, assinatura PLTx válida, 1 variável identificada)
- ✅ 4 testes passando, 11 adicionais de integração
- ⏳ FASE 2 — bloqueado (requer exemplos adicionais do CEPEL para formato de série)
- 6/7 tarefas concluídas (86%)

**Limitação Documentada:**
- Arquivo de exemplo propriet ário; formato binário não totalmente mapeado
- RECOMENDAÇÃO: usar `posprocessamento_v2.LeitorPLTBinario` como fallback
- PRÓXIMO: coletar mais exemplos .plt binários reais para continuar FASE 2

**Resultado Entregue:**
- Parser de header robusto (`ler_assinatura()`, `ler_filename()`, `ler_header()`)
- 15 testes de conformidade (100% passando)
- Cobertura `plt_binario.py` → 79%
- Documentação de limitações e próximos passos

---

## v2.1.2 — Relatórios Estruturados (`.rel` + `.out`) (em andamento)

**Meta:** Consolidar parsers em `posprocessamento_v2.py` (230 linhas, 67% cobertura)

### Tarefas

- [x] **T2.1.2.1** Analisar estrutura — LeitorREL, LeitorOUT, LeitorSNAP existentes ✅ (2026-07-12)
  - Código base presente em `posprocessamento_v2.py` (linhas 315–489)
- [ ] **T2.1.2.2** Expandir testes com exemplos reais (.rel, .out do CEPEL)
- [ ] **T2.1.2.3** Melhorar parser de `.rel` — seções de resultado, eventos, convergência
- [ ] **T2.1.2.4** Melhorar parser de `.out` — compatibilidade com variantes do formato
- [ ] **T2.1.2.5** Adicion ar suporte a ParseOUT estendido (dados numéricos por seção)
- [ ] **T2.1.2.6** Testes de conformidade — mínimo 10 testes contra exemplos
- [ ] **T2.1.2.7** Documentação — formatos de relatório em TEORIA.md

**Deps:** `posprocessamento_v2.py`, exemplos `.rel` / `.out` do CEPEL (se disponíveis)

**Resultado esperado:**
- LeitorREL/LeitorOUT com parsing robusto (texto, não binário → mais fácil)
- 10+ testes de conformidade
- Cobertura `posprocessamento_v2.py` → 90%+

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
