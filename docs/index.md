# 🚀 pynatem

Biblioteca Python para geração, manipulação e execução automatizada de casos de simulação **ANATEM** (CEPEL).

## ✨ Características

- ✅ Lê e escreve arquivos `.stb` com garantia de roundtrip
- ✅ API fluente em Python para criar/editar casos programaticamente
- ✅ Suporte completo a CDU (Controladores Definidos pelo Usuário)
- ✅ Validação contra manual ANATEM v12.10
- ✅ Automação de lotes (contingências, ensaios paralelos)
- ✅ Pós-processamento de resultados (`.plt`, `.rela`, `.sav`)

## 📦 Instalação

```bash
pip install pynatem
```

## ⚡ Uso Rápido

### Criar um caso

```python
from pynatem import CasoAnatem

caso = CasoAnatem()
caso.dsim.tfim = 15.0
caso.exportar("novo_caso.stb")
```

### Editar um arquivo existente

```python
caso = CasoAnatem.ler("caso_existente.stb")
caso.dsim.tfim = 20.0
caso.exportar("caso_modificado.stb")
```

### Executar contingências

```python
from pynatem import EnsaioAnatem

ensaio = EnsaioAnatem.de_contingencias(
    caso_base="base.stb",
    contingencias=[("deslig_linha", "1201 1202 1")]
)
```

## 📚 Documentação

- [Guia de Início](getting-started.md)
- [Tutorial Completo](tutorial.md)
- [Referência da API](api.md)
- [Contribuindo](contributing.md)

## 📊 Status

**Versão:** v0.14.2 (Estável)
**Testes:** 163 testes
**Python:** 3.9+

**Licença:** MIT
