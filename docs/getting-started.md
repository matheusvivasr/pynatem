# 🎯 Guia de Início

## Instalação

### Via pip (recomendado)

```bash
pip install pynatem
```

### Instalação em desenvolvimento

```bash
git clone https://github.com/MatheusVivas/ana-estatica.git
cd ana-estatica
pip install -e ".[dev,plt]"
```

## Seu Primeiro Caso

### 1. Criar um caso do zero

```python
from pynatem import CasoAnatem

# Criar caso vazio
caso = CasoAnatem()

# Configurar simulação
caso.dsim.tfim = 15.0      # Tempo final (segundos)
caso.dsim.delt = 0.01      # Passo de integração

# Configurar opções
caso.dopc.arq_sav = "rede.sav"
caso.dopc.arq_plt = "saidas.plt"

# Salvar
caso.exportar("meu_caso.stb")
print("Caso criado: meu_caso.stb")
```

### 2. Editar um arquivo existente

```python
from pynatem import CasoAnatem

# Carregar caso existente
caso = CasoAnatem.ler("caso_existente.stb")

# Modificar
caso.dsim.tfim = 20.0
caso.dsim.delt = 0.005

# Salvar
caso.exportar("caso_modificado.stb")
```

### 3. Adicionar eventos

```python
from pynatem import CasoAnatem
from pynatem.blocos import EventoAberturaRapida

caso = CasoAnatem.ler("base.stb")

# Adicionar evento de curto-circuito
caso.curto_barra(barra=1001, tempo_inicio=1.0, tempo_fim=0.1)

# Ou abertura de linha
caso.curto_circuito(
    barra_de=1201,
    barra_para=1202,
    circuito=1,
    tempo_inicio=1.0,
    tempo_fim=0.1
)

caso.exportar("caso_com_eventos.stb")
```

## Validação

```python
# Validar caso
avisos = caso.validar()

# Imprimir avisos
for aviso in avisos:
    print(f"⚠️ {aviso}")

# Validar contra SAV (ANAREDE)
inconsistencias = caso.validar_contra_sav("rede.sav")
```

## Próximos Passos

- Veja [Tutorial Completo](tutorial.md) para exemplos avançados
- Consulte [Referência da API](api.md) para documentação detalhada
- Explore exemplos em `examples/`
