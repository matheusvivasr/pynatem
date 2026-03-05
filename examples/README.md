# 📚 Exemplos de Uso — pyanatem

Coleção de exemplos práticos de uso da biblioteca pyanatem.

## Estrutura

| Arquivo | Descrição |
|---------|-----------|
| `01_basic_case_creation.py` | Criar um caso ANATEM do zero |
| `02_edit_existing_case.py` | Editar um caso existente |
| `03_batch_contingencies.py` | Executar lote de contingências |
| `04_validation.py` | Validar casos (STB ↔ SAV) |
| `05_postprocessing.py` | Analisar resultados (`.plt`, `.rela`) |
| `06_cdu_advanced.py` | Criar Controladores Definidos pelo Usuário |

## Como Executar

### Prerequisitos

```bash
pip install pyanatem
```

### Executar um exemplo

```bash
python examples/01_basic_case_creation.py
```

### Com seus próprios arquivos

Modifique os nomes de arquivo nos exemplos:

```python
# Antes
caso = CasoAnatem.ler("base.stb")

# Depois (seu arquivo)
caso = CasoAnatem.ler("seu_arquivo.stb")
```

## Exemplos Detalhados

### Exemplo 1: Criar Caso Básico
Mostra como criar um caso ANATEM do zero com:
- Configuração de simulação
- Adição de eventos
- Variáveis de saída
- Validação e exportação

### Exemplo 2: Editar Caso Existente
Demonstra:
- Carregar arquivo `.stb` existente
- Modificar parâmetros
- Adicionar eventos
- Salvar com novo nome

### Exemplo 3: Batch de Contingências
Ilustra:
- Criar múltiplas contingências
- Executar lotes
- Analisar resultados

### Exemplo 4: Validação Cruzada
Mostra:
- Validação interna (STB)
- Validação contra SAV (ANAREDE)
- Teste de roundtrip

### Exemplo 5: Pós-processamento
Demonstra:
- Ler arquivo `.plt` (saídas)
- Ler arquivo `.rela` (relatório)
- Análise de dados (com pandas)

### Exemplo 6: CDU Avançado
Ilustra:
- Criar controladores personalizados
- Adicionar blocos de controle
- Integração com caso

## Dicas

1. **Comece pelo Exemplo 1** se for iniciante
2. **Adapte os exemplos** para seus arquivos
3. **Use validação** antes de executar
4. **Consulte os docstrings** para mais detalhes

## Suporte

- 📖 [Documentação](../docs/)
- 📚 [Tutorial Completo](../docs/tutorial.md)
- 📋 [Referência da API](../docs/api.md)
- 💬 [GitHub Issues](https://github.com/MatheusVivas/ana-estatica/issues)

---

**Versão:** v0.15.0  
**Mantido por:** Matheus Vivas (USP)
