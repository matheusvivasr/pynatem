# Contributing to pynatem

Obrigado por considerar contribuir! 🎉

## Setup Rápido

```bash
git clone https://github.com/matheusvivasr/pynatem.git
cd pynatem
git checkout -b feature/sua-feature

pip install -e ".[dev]"
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
