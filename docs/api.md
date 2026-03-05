# 📚 Referência da API

## CasoAnatem

Classe principal para manipular casos de simulação ANATEM.

### Criar e Carregar

```python
from pyanatem import CasoAnatem

# Criar caso vazio
caso = CasoAnatem()

# Carregar arquivo .stb existente
caso = CasoAnatem.ler("arquivo.stb")

# Carregar do texto
caso = CasoAnatem.ler_string(texto_stb)
```

### Atributos Principais

| Atributo | Tipo | Descrição |
|----------|------|-----------|
| `darq` | `BlocoDARQ` | Associação de arquivos |
| `dopc` | `BlocoDOPC` | Opções globais |
| `dsim` | `BlocoDSIM` | Parâmetros de simulação |
| `devt` | `BlocoDEVT` | Eventos |
| `dplt` | `BlocoDPLT` | Variáveis de saída |
| `dmdg` | `BlocoDMDG` | Modelos de geradores |
| `dmaq` | `BlocoDMAQ` | Máquinas |
| `dcdu` | `BlocoDCDU` | Controladores |
| `dfac` | `BlocoDFAC` | FACTS (opcional) |
| `dhvd` | `BlocoDHVD` | HVDC (opcional) |

### Métodos Principais

#### `exportar(arquivo_saida: str) -> None`
Salva o caso em arquivo `.stb`.

```python
caso.exportar("meu_caso.stb")
```

#### `validar() -> List[str]`
Retorna lista de avisos de consistência.

```python
avisos = caso.validar()
for aviso in avisos:
    print(aviso)
```

#### `curto_barra(barra: int, tempo_inicio: float, tempo_fim: float)`
Adiciona evento de curto-circuito em barra.

```python
caso.curto_barra(barra=1001, tempo_inicio=1.0, tempo_fim=0.1)
```

#### `curto_circuito(barra_de: int, barra_para: int, circuito: int, tempo_inicio: float, tempo_fim: float)`
Adiciona evento de curto-circuito em linha.

```python
caso.curto_circuito(1201, 1202, 1, tempo_inicio=1.0, tempo_fim=0.1)
```

---

## EnsaioAnatem

Classe para automação de lotes de simulação.

### Criar Ensaio

```python
from pyanatem import EnsaioAnatem

# De contingências
ensaio = EnsaioAnatem.de_contingencias(
    caso_base="base.stb",
    contingencias=[
        ("deslig_linha_1", "1201 1202 1"),
        ("deslig_linha_2", "1301 1302 1"),
    ],
    diretorio_saida="resultados/"
)
```

### Métodos Principais

#### `executar_contingencias(paralelo: bool = False, num_workers: int = 1)`
Executa todas as contingências.

```python
resultados = ensaio.executar_contingencias(paralelo=True, num_workers=4)
```

---

## BlocoDPLT

Gerenciar variáveis de saída/plotagem.

### Métodos Comuns

```python
# Tensão em barra
caso.dplt.tensao_barra(barra=1001)

# Potência em circuito
caso.dplt.potencia_circuito(de=1201, para=1202, circuito=1)

# Corrente em circuito
caso.dplt.corrente_circuito(de=1201, para=1202, circuito=1)

# Potência em máquina
caso.dplt.potencia_maquina(maquina=1001)

# Velocidade em máquina
caso.dplt.velocidade_maquina(maquina=1001)
```

---

## BlocoDCDU

Gerenciar Controladores Definidos pelo Usuário.

### Adicionar Controlador

```python
from pyanatem.cdu import ControladorCDU

cdu = ControladorCDU(numero=1, nome="Meu CDU")
caso.dcdu.adicionar_controlador(cdu)
```

---

## Pós-processamento

### LeitorPLT

Ler arquivo de saídas `.plt`.

```python
from pyanatem.posprocessamento import LeitorPLT

leitor = LeitorPLT()
dados = leitor.ler("saidas.plt")

# Como DataFrame
df = dados.como_dataframe()
print(df)

# Acessar por variável
tensoes = dados.obter_variavel("T", 1001)
```

### LeitorRelatorio

Ler arquivo de relatório `.rela`.

```python
from pyanatem.posprocessamento import LeitorRelatorio

leitor = LeitorRelatorio()
relatorio = leitor.ler("relatorio.rela")

print(f"Sucesso: {relatorio.sucesso}")
print(f"Tempo: {relatorio.tempo_execucao}s")
```

---

## Validação

### Validar Contra SAV (ANAREDE)

```python
inconsistencias = caso.validar_contra_sav("rede.sav")
```

---

## Exceções

| Exceção | Descrição |
|---------|-----------|
| `ErroParsingSTB` | Erro ao fazer parsing do arquivo `.stb` |
| `ErroValidacao` | Validação falhou |
| `ErroEncoding` | Problema com encoding de caracteres |

---

## Mais Informações

Para documentação completa, consulte o docstring de cada classe:

```python
from pyanatem import CasoAnatem
help(CasoAnatem)
```
