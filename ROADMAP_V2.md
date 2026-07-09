# Plano Integrado: v2.1.3 → v2.5.3

**Objetivo:** Implementar narrativas temáticas faltantes (v1.4–v1.9) como v2.1–v2.5.

**Estratégia:** Integração iterativa de código base existente + testes + documentação.

**Timeline Estimada:** 12–17 dias de trabalho intensivo.

---

## v2.1.3 — Snapshots + Sinal Externo (1–2 dias)

**Código Base:** `posprocessamento_v2.py` (LeitorSNAP: 62 linhas)

**Tarefas:**
- [ ] Expandir `ResultadoSnapshot` com serialização
- [ ] Implementar `CasoAnatem.gerar_snapshot(tempo)` → `.snap`
- [ ] Implementar `CasoAnatem.restaurar_snapshot(path)` ← `.snap`
- [ ] Adicionar `BlocoDAVS` (Sinal Externo)
- [ ] 10+ testes de conformidade

**Saída:** v2.1.3 completa (23 testes → 33+ testes)

---

## v2.2 — CDU Avançado Integrado (3–4 dias)

**Código Base:** `cdu_v17.py` (29.5 KB, 0% cobertura)

**Patches:**

### v2.2.1 — Inicialização de Modelos CDU (1 dia)
- Integrar `DefvalCDU`, `DefvdfCDU`, `DefpltCDU` com `ControladorCDU`
- Construtores tipados + validação de valores iniciais
- 8+ testes

### v2.2.2 — Topologia e Controladores Genéricos (1 dia)
- Integrar `DtduCDU` (topologia), `AcduCDU` (CDU isolada)
- Desambiguação de controladores não-específicos
- 8+ testes

### v2.2.3 — Relés e SEP (1 dia)
- Novo `BlocoREL` para relés de proteção
- Integração com esquemas de proteção (SEP)
- 8+ testes

### v2.2.4 — Mensagens e OTM (0.5 dias)
- Integrar `DmsgCDU`, `OTMx` (malha inativa)
- 6+ testes

**Saída:** v2.2.0 completa (33+ testes → 60+ testes, 0% → 50%+ cdu_v17.py)

---

## v2.3 — Modos de Análise Estruturados (3–4 dias)

**Código Base:** `analise_v18.py` (17.2 KB, 35% cobertura)

**Patches:**

### v2.3.1 — Contingência N-1 (1 dia)
- Integrar `AnalisadorContingencia` com API fluente
- Geração automática de cenários
- 8+ testes

### v2.3.2 — Análise de CDU Isolada (0.5 dias)
- Testar controlador sem rede (`ACDU`)
- 6+ testes

### v2.3.3 — Multi-Infeed (1 dia)
- Integrar `DMIF`/`EAMI` (interação múltiplos infeedores)
- 8+ testes

### v2.3.4 — Interação Shunts (0.5 dias)
- Integrar `EAIF` (acoplamento dinâmico)
- 6+ testes

### v2.3.5 — Séries Temporais (1 dia)
- Integrar `DSTR`/`DSTO` (varredura paramétrica)
- 10+ testes

**Saída:** v2.3.0 completa (60+ testes → 90+ testes)

---

## v2.4 — Opções de Execução & Seleção (2–3 dias)

**Código Base:** Disperso (Cap. 42 + Cap. 47 do manual)

**Patches:**

### v2.4.1 — Opções de Controle (1 dia)
- Expandir `BlocoOPC` para ~112 opções (Cap. 47)
- Construtores tipados + validação
- 12+ testes

### v2.4.2 — Linguagem de Seleção (1 dia)
- Novo `ParserSelecao` (Cap. 42)
- Associação com `DCAR` estruturada
- 10+ testes

### v2.4.3–v2.4.4 — Automação + Diagnóstico (0.5 dias)
- Geração automática de caminhos (`GeradorCaminhos`)
- Diagnóstico de convergência (`AnalisadorConvergencia`)
- 8+ testes

**Saída:** v2.4.0 completa (90+ testes → 120+ testes)

---

## v2.5 — Algoritmos de Estabilidade Integrados (2–3 dias)

**Código Base:** `estabilidade_v19.py` (20.1 KB, 0% cobertura)

**Patches:**

### v2.5.1 — Critérios de Pós-Falta (1 dia)
- Integrar cálculo de ângulo máximo, tempo de recuperação, amortecimento
- Validação contra simulações do CEPEL
- 10+ testes

### v2.5.2 — Sincronismo Pós-Falta (0.5 dias)
- Detecção de coerência entre máquinas
- Clustering + velocidade de recuperação
- 8+ testes

### v2.5.3 — Análise de Frequência (1 dia)
- Novo `AnalisadorFrequencia`
- Modos eletromecânicos, ROCOF
- 10+ testes

**Saída:** v2.5.0 completa (120+ testes → 150+ testes)

---

## Critério de Aceite Global (v2.1.3 → v2.5.3)

- [ ] ≥150 testes (318 → 468+)
- [ ] Cobertura ≥80%
- [ ] CI verde (pytest, mypy, ruff)
- [ ] Documentação completa (CHANGELOG, ROADMAP, TEORIA.md)
- [ ] Commits incrementais + claros

---

## Estrutura de Commits

Cada patch será um commit separado:
```
feat(v2.1.3): snapshots + DAVS — fechamento de pós-processamento
feat(v2.2.1): CDU — inicialização de modelos (DEFVAL/DEFVDF/DEFPLT)
feat(v2.2.2): CDU — topologia e controladores genéricos (DTDU/ACDU)
... (etc)
feat(v2.5.3): análise de frequência e modos eletromecânicos
```

---

## Dependências de Código

```
v2.1.3 → posprocessamento_v2.py (67%)
v2.2.x → cdu_v17.py (0%)
v2.3.x → analise_v18.py (35%)
v2.4.x → código novo (Cap. 42/47)
v2.5.x → estabilidade_v19.py (0%)
```

---

## Próximas Ações

1. ✅ Criar este plano integrado
2. ▶️ Começar v2.1.3 (hoje)
3. ▶️ Continuar v2.2–v2.5 iterativamente
4. Finalizar com CHANGELOG consolidado e release notes

