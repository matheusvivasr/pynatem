# Contributing to pynatem

Obrigado por considerar contribuir! 🎉

## Setup Rápido

```bash
git clone https://github.com/matheusvivasr/pynatem.git
cd pynatem
git checkout -b feature/sua-feature

pip install -e ".[dev]"
```

## Fluxo de Branches e Versionamento (postulado)

O projeto usa duas branches com papéis fixos:

| Branch | Papel |
|--------|-------|
| `main` | **Somente publicações.** Recebe merge apenas em lançamento de versão **MAJOR** (vX.0.0), seguido de tag e publicação no PyPI. |
| `vivas` | Branch de construção (trabalho interno). Todo desenvolvimento acontece aqui. |

Regras por nível de versão (SemVer):

- **PATCH (vX.Y.Z)** → permite **commit** na `vivas` (meta concreta entregue
  com testes passando).
- **MINOR (vX.Y.0)** → indica **`git push`** da `vivas` para `origin/vivas`
  (etapa temática fechada, progresso publicado no remoto).
- **MAJOR (vX.0.0)** → **merge na `main`** + tag `vX.0.0` + lançamento no PyPI
  (o workflow `pypi.yml` publica automaticamente ao receber a tag).

Antes de qualquer merge na `main`, a suíte completa deve estar verde:

```bash
pytest tests/ && black --check pynatem/ tests/ && isort --check-only pynatem/ tests/ && flake8 pynatem/ tests/ && mypy pynatem/ --ignore-missing-imports
```

## Rodar Testes

```bash
pytest tests/ -v
pytest tests/ --cov=pynatem --cov-report=html
```

## Code Quality

```bash
black pynatem/ tests/
isort pynatem/ tests/
flake8 pynatem/ tests/ --max-line-length=100
mypy pynatem/ --ignore-missing-imports
```

## Antes de Submeter

- [ ] Código segue style guide (black, isort, flake8)
- [ ] Type hints completos (mypy check)
- [ ] Testes passam
- [ ] Documentação atualizada
- [ ] Commit messages descritivas

## Reportar Bugs

Abra uma [Issue](https://github.com/matheusvivasr/pynatem/issues/new?template=bug_report.md) com:

- Descrição clara
- Passos para reproduzir
- Seu ambiente (Python, OS, versão)
- Traceback completo

## Sugerir Features

Use [Discussions](https://github.com/matheusvivasr/pynatem/discussions) com:

- Descrição do caso de uso
- Exemplo de código desejado
- Alternativas consideradas

## Padrões de Código

- **Python 3.9+**
- **Type hints** obrigatórios para funções públicas
- **Docstrings** formato Google
- **PEP 8** (black para enforce)

## Git Workflow

```
Branch: feature/nome-descritivo
Commit: [FEATURE] Add new capability
PR description: Describe what & why
```

Obrigado por melhorar pynatem! 🙌
