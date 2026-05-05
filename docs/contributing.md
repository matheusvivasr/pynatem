# 🤝 Contribuindo para pynatem

Obrigado por seu interesse em contribuir! Este documento explica como participar do projeto.

## Como Começar

1. **Fork o repositório** no GitHub
2. **Clone seu fork**: `git clone https://github.com/seu-usuario/ana-estatica.git`
3. **Crie uma branch**: `git checkout -b feature/minha-feature`
4. **Faça suas mudanças** e commit: `git commit -am 'Adiciona minha feature'`
5. **Push para seu fork**: `git push origin feature/minha-feature`
6. **Abra um Pull Request** na branch `main`

## Desenvolvimento Local

### Instalar em modo desenvolvimento

```bash
pip install -e ".[dev,plt]"
```

### Rodar testes

```bash
pytest tests/ -v
```

### Verificar type hints

```bash
mypy pynatem/
```

### Formatar código

```bash
black pynatem/ tests/
isort pynatem/ tests/
```

## Diretrizes de Contribuição

### Código

- ✅ Use type hints em todas as funções
- ✅ Mantenha cobertura de testes > 90%
- ✅ Siga [PEP 8](https://www.python.org/dev/peps/pep-0008/)
- ✅ Use `black` para formatação automática
- ✅ Adicione testes para novo código

### Testes

Cada feature deve ter testes:

```python
def test_minha_feature():
    caso = CasoAnatem()
    # ... seu teste ...
    assert caso.alguma_propriedade == esperado
```

### Documentação

- Documente funções públicas (docstring)
- Atualize `docs/` para mudanças significativas
- Mantenha `README.md` atualizado

### Commit Messages

Use padrão semântico:

- `feat: Adiciona nova feature`
- `fix: Corrige bug em X`
- `docs: Atualiza documentação`
- `test: Adiciona testes para X`
- `refactor: Refatora módulo Y`

## Reportar Bugs

Use [GitHub Issues](https://github.com/MatheusVivas/ana-estatica/issues) com:

- ✅ Descrição clara
- ✅ Passos para reproduzir
- ✅ Código mínimo exemplo
- ✅ Versão de Python/pynatem
- ✅ Traceback (se houver)

## Sugerir Features

Abra uma [Issue com tag `enhancement`](https://github.com/MatheusVivas/ana-estatica/issues/new?labels=enhancement):

- ✅ Descrição da necessidade
- ✅ Exemplo de uso esperado
- ✅ Alternativas consideradas

## Revisão de Código

Todas as PRs serão revisadas por maintainers. Feedback pode incluir:

- Mudanças de design
- Melhorias de performance
- Testes adicionais
- Documentação

## Comunidade

- 💬 Faça perguntas em [Discussions](https://github.com/MatheusVivas/ana-estatica/discussions)
- 📧 Contate: <vivas.matheus@usp.br>
- 📚 Leia [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)

## Licença

Ao contribuir, você concorda que seu código será licenciado sob MIT License.

---

Obrigado por ajudar a melhorar pynatem! 🎉
