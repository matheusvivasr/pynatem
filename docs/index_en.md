# 🚀 pyanatem

Python library for ANATEM simulator case generation, manipulation, and automated execution (CEPEL — Electric Energy Research Center).

## ✨ Features

- ✅ Read and write `.stb` files with roundtrip guarantee
- ✅ Fluent Python API for case creation/editing
- ✅ Full CDU (Custom Defined Controllers) support
- ✅ ANATEM v12.10 manual validation
- ✅ Batch automation (contingencies, parallel tests)
- ✅ Results postprocessing (`.plt`, `.rela`, `.sav`)

## 📦 Installation

```bash
pip install pyanatem
```

## ⚡ Quick Start

### Create a case

```python
from pyanatem import CasoAnatem

caso = CasoAnatem()
caso.dsim.tfim = 15.0
caso.exportar("new_case.stb")
```

### Edit existing file

```python
caso = CasoAnatem.ler("existing_case.stb")
caso.dsim.tfim = 20.0
caso.exportar("modified_case.stb")
```

### Run contingencies

```python
from pyanatem import EnsaioAnatem

ensaio = EnsaioAnatem.de_contingencias(
    caso_base="base.stb",
    contingencias=[("line_1", "1201 1202 1")]
)
results = ensaio.executar_contingencias()
```

## 📚 Documentation

- [Getting Started](getting-started_en.md)
- [Complete Tutorial](tutorial_en.md)
- [API Reference](api_en.md)
- [Contributing](contributing_en.md)

## 📊 Status

**Version:** v1.0  
**Tests:** 212+ passing  
**Coverage:** 87%+  
**Python:** 3.9+

**License:** MIT
