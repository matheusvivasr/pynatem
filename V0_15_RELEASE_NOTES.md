# 🎉 v0.15.0 — Community & Documentation Release

**Data de Lançamento:** 2026-07-09  
**Status:** ✅ Completo

---

## 🎯 Objetivos Alcançados

### ✅ Community & DevOps (100%)

- ✅ **GitHub Actions CI/CD** — Pipeline automatizado com:
  - Testes em Python 3.9, 3.10, 3.11, 3.12
  - Verificação de type hints (mypy)
  - Formatação de código (black, isort)
  - Linting (flake8)
  - Upload automático de cobertura para Codecov

- ✅ **Issue Templates** — Templates pré-configurados:
  - Bug Report 🐛
  - Feature Request ✨
  - Question ❓
  - Config GitHub Issue

- ✅ **Codecov Integration** — Rastreamento contínuo:
  - Coverage reports em cada PR
  - Configuração `codecov.yml` pronta
  - Target: >90% para v1.0

- ✅ **Release Automation** — Pipeline PyPI:
  - Trigger: `git tag v0.15.x`
  - Build, test, e publish automático
  - Integração com `twine` para PyPI

### ✅ Documentação (100%)

- ✅ **GitHub Pages (mkdocs)**
  - Site completo em `docs/`
  - Theme Material Dark/Light
  - Navegação estruturada
  - Pronto para deploy em GitHub Pages

- ✅ **Tutorial Completo (PT)**
  - 6 partes estruturadas:
    1. Fundamentos da estrutura STB
    2. Criação de casos completos
    3. Eventos avançados
    4. CDU (Controladores)
    5. Execução de lotes
    6. Pós-processamento
  - Exemplos de código prontos para executar

- ✅ **Exemplos Avançados (7 arquivos)**
  1. `01_basic_case_creation.py` — Criar caso do zero
  2. `02_edit_existing_case.py` — Editar caso existente
  3. `03_batch_contingencies.py` — Lote de contingências
  4. `04_validation.py` — Validação STB ↔ SAV
  5. `05_postprocessing.py` — Análise de resultados
  6. `06_cdu_advanced.py` — CDU avançado
  7. `07_integration_workflow.py` — Workflow integrado
  + `examples/README.md` — Guia dos exemplos

---

## 📂 Estrutura de Arquivos Criados

```
ana-estatica/
├── .github/
│   ├── workflows/
│   │   ├── tests.yml              ✅ CI/CD (testes + code quality)
│   │   ├── lint.yml               ✅ Linting
│   │   └── release.yml            ✅ Release automation
│   └── ISSUE_TEMPLATE/
│       ├── bug_report.md          ✅
│       ├── feature_request.md     ✅
│       ├── question.md            ✅
│       └── config.yml             ✅
│
├── docs/                           ✅ GitHub Pages (mkdocs)
│   ├── index.md                    ✅ Página inicial
│   ├── getting-started.md          ✅ Guia de início
│   ├── tutorial.md                 ✅ Tutorial completo
│   ├── api.md                      ✅ Referência de API
│   └── contributing.md             ✅ Guia de contribuição
│
├── examples/                        ✅ Exemplos avançados (7)
│   ├── 01_basic_case_creation.py
│   ├── 02_edit_existing_case.py
│   ├── 03_batch_contingencies.py
│   ├── 04_validation.py
│   ├── 05_postprocessing.py
│   ├── 06_cdu_advanced.py
│   ├── 07_integration_workflow.py
│   └── README.md
│
├── mkdocs.yml                      ✅ Configuração mkdocs
├── codecov.yml                     ✅ Configuração Codecov
└── V0_15_RELEASE_NOTES.md         ✅ Este arquivo
```

---

## 🚀 Como Usar (v0.15)

### 1. Configurar CI/CD

```bash
# Commits para main acionam testes automáticos
git push origin main

# Tags acionam release para PyPI
git tag v0.15.0
git push origin v0.15.0
```

### 2. Executar Testes Localmente

```bash
# Install dev dependencies
pip install -e ".[dev,plt]"

# Run tests
pytest tests/ -v

# Check coverage
pytest tests/ --cov=pyanatem
```

### 3. Usar Exemplos

```bash
# Exemplo básico
python examples/01_basic_case_creation.py

# Exemplo avançado
python examples/07_integration_workflow.py
```

### 4. Deploy GitHub Pages

```bash
# Install mkdocs
pip install mkdocs mkdocs-material

# Build locally
mkdocs build

# Deploy (automático com GitHub Actions)
mkdocs gh-deploy
```

---

## 📊 Métricas

| Item | Antes | Depois |
|------|-------|--------|
| Exemplos | 0 | 7 |
| Docs | Mínimo | Completo |
| CI/CD | Nenhum | 2 workflows |
| Cobertura rastreada | Não | Sim (Codecov) |
| Release automatizado | Manual | Automático |
| GitHub Pages | Não | Pronto |

---

## 🔄 Próximas Etapas (v1.0)

### Focus: Estabilidade & Qualidade

- [ ] Aumentar cobertura para >90%
- [ ] Adicionar 200+ testes
- [ ] Documentação EN (bilíngue)
- [ ] Benchmarks e performance
- [ ] Release oficial no PyPI
- [ ] Announcement público

**ETA:** Setembro 2026

---

## 📚 Referências Rápidas

### Documentação
- 📖 [Guia de Início](docs/getting-started.md)
- 📚 [Tutorial Completo](docs/tutorial.md)
- 📋 [Referência da API](docs/api.md)
- 🤝 [Guia de Contribuição](docs/contributing.md)

### Exemplos
- 💡 [7 Exemplos Avançados](examples/)

### Configuração
- ⚙️ [mkdocs.yml](mkdocs.yml) — Configuração docs
- 🔧 [codecov.yml](codecov.yml) — Configuração coverage
- 🚀 [.github/workflows/](./github/workflows/) — Automação

---

## ✨ Destaques da v0.15

✅ **Pronto para Produção** — Infraestrutura sólida  
✅ **Documentação Completa** — Guias + exemplos + API  
✅ **Automação Total** — CI/CD + Release + Coverage  
✅ **Comunidade-Ready** — Issue templates + Contributing  
✅ **7 Exemplos Práticos** — De básico a integrado  

---

## 🎓 Licença

MIT License — veja [LICENSE](LICENSE)

---

**Mantido por:** Matheus Vivas (USP)  
**Email:** vivas.matheus@usp.br  
**Repositório:** https://github.com/MatheusVivas/ana-estatica

---

## 🙏 Agradecimentos

Especial agradecimento a todos que contribuíram para a v0.15!

---

**Status:** ✅ COMPLETO E TESTADO  
**Próximo Milestone:** v1.0 (Setembro 2026)
