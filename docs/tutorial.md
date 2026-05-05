# 📖 Tutorial Completo

## Parte 1: Fundamentos

### Estrutura de um Caso ANATEM

Um arquivo `.stb` (STudy Base) contém:

- **DARQ** — Associação de arquivos (SAV, PLT, RELA, DCDU)
- **DOPC** — Opções globais de execução
- **DSIM** — Parâmetros de simulação (tempo final, passo, etc.)
- **DEVT** — Eventos (curtos, aberturas, chaveamentos)
- **DPLT** — Variáveis de saída/plotagem
- **DMDG** — Modelos predefinidos de geradores
- **DMAQ** — Associação máquina ↔ modelo
- **DCDU** — Controladores Definidos pelo Usuário (opcional)
- **DFAC** — FACTS (SVC, TCSC, STATCOM) (opcional)
- **DHVD** — Elo HVDC (opcional)

### Criando um Caso Completo

```python
from pynatem import CasoAnatem
from pynatem.blocos import BlocoDSIM, BlocoDOPC, BlocoDARQ

# 1. Criar caso
caso = CasoAnatem()

# 2. Configurar simulação
caso.dsim.tfim = 30.0          # Tempo final: 30s
caso.dsim.delt = 0.01          # Passo: 10ms
caso.dsim.tini = 0.0

# 3. Associar arquivos
caso.darq.arq_sav = "rede.sav"        # Rede de ANAREDE
caso.darq.arq_plt = "saidas.plt"      # Saídas de plotagem
caso.darq.arq_rela = "relatorio.rela" # Relatório de execução

# 4. Adicionar evento: curto em barra
caso.curto_barra(
    barra=1001,
    tempo_inicio=1.0,
    tempo_fim=1.1,  # 100ms de duração
)

# 5. Adicionar variáveis de saída
caso.dplt.tensao_barra(barra=1001)
caso.dplt.potencia_circuito(de=1201, para=1202, circuito=1)

# 6. Salvar
caso.exportar("meu_caso_completo.stb")
print("✅ Caso criado com sucesso!")
```

## Parte 2: Eventos Avançados

### Tipos de Eventos Suportados

```python
from pynatem import CasoAnatem

caso = CasoAnatem.ler("base.stb")

# 1. Curto-circuito em barra
caso.curto_barra(barra=1001, tempo_inicio=1.0, tempo_fim=0.1)

# 2. Curto-circuito em linha (3 fases)
caso.curto_circuito(
    barra_de=1201,
    barra_para=1202,
    circuito=1,
    tempo_inicio=1.0,
    tempo_fim=0.1
)

# 3. Abertura de linha
caso.devt.abertura_rapida(
    barra_de=1201,
    barra_para=1202,
    circuito=1,
    tempo=0.5
)

# 4. Mudança de impedância
caso.devt.mudanca_impedancia(
    barra_de=1201,
    barra_para=1202,
    circuito=1,
    tempo=2.0,
    r=0.01,
    x=0.1
)

caso.exportar("caso_eventos_avancados.stb")
```

## Parte 3: CDU (Controladores Definidos pelo Usuário)

### Criar um Controlador Simples

```python
from pynatem import CasoAnatem
from pynatem.cdu import ControladorCDU

caso = CasoAnatem.ler("base.stb")

# Criar controlador
cdu = ControladorCDU(numero=1, nome="Meu CDU")

# Adicionar blocos (exemplo simplificado)
cdu.bloco_import(codigo=101, nome="Import1", arquivo="entrada.txt")
cdu.bloco_output(codigo=201, nome="Output1")

# Adicionar ao caso
caso.dcdu.adicionar_controlador(cdu)

caso.exportar("caso_com_cdu.stb")
```

## Parte 4: Execução de Lotes (Contingências)

### Executar Múltiplas Contingências

```python
from pynatem import EnsaioAnatem

# Definir caso base e contingências
ensaio = EnsaioAnatem.de_contingencias(
    caso_base="base.stb",
    contingencias=[
        ("deslig_linha_1", "1201 1202 1"),
        ("deslig_linha_2", "1301 1302 1"),
        ("deslig_gerador", "1001"),
    ],
    diretorio_saida="resultados/"
)

# Executar em paralelo (se ANATEM suportar)
resultados = ensaio.executar_contingencias(paralelo=True, num_workers=4)

# Analisar resultados
for contingencia, resultado in resultados.items():
    if resultado.sucesso:
        print(f"✅ {contingencia}: OK")
    else:
        print(f"❌ {contingencia}: FALHOU")
        print(f"   Erro: {resultado.mensagem_erro}")
```

## Parte 5: Pós-processamento

### Ler e Analisar Resultados

```python
from pynatem.posprocessamento import LeitorPLT, LeitorRelatorio

# 1. Ler arquivo .plt (variáveis de plotagem)
leitor_plt = LeitorPLT()
dados = leitor_plt.ler("saidas.plt")

# Acessar como DataFrame
df = dados.como_dataframe()
print(df.head())

# Filtrar dados específicos
tensao_barra_1001 = df[df["codigo"] == "T 1001"]
print(f"Tensão máxima na barra 1001: {tensao_barra_1001.max():.2f} pu")

# 2. Ler relatório de execução
leitor_rel = LeitorRelatorio()
relatorio = leitor_rel.ler("relatorio.rela")

print(f"Simulação completada em {relatorio.tempo_execucao}s")
if relatorio.sucesso:
    print("✅ Simulação bem-sucedida")
else:
    print(f"❌ Erro: {relatorio.mensagem_erro}")
```

## Parte 6: Validação e Boas Práticas

### Validar Casos Antes de Executar

```python
from pynatem import CasoAnatem

caso = CasoAnatem.ler("caso.stb")

# 1. Validação interna
avisos = caso.validar()
for aviso in avisos:
    print(f"⚠️ {aviso}")

# 2. Validação contra SAV (ANAREDE)
inconsistencias = caso.validar_contra_sav("rede.sav")
for incon in inconsistencias:
    print(f"❌ Inconsistência: {incon}")

# 3. Verificar roundtrip (exportar → ler → comparar)
caso_original = caso
caso.exportar("temp.stb")
caso_recarregado = CasoAnatem.ler("temp.stb")

if caso_original == caso_recarregado:
    print("✅ Roundtrip verificado com sucesso")
else:
    print("⚠️ Diferenças detectadas no roundtrip")
```

## Dicas Importantes

1. **Sempre validar** antes de executar simulações
2. **Use roundtrip** para garantir integridade dos dados
3. **Documente contingências** com nomes descritivos
4. **Backup** de arquivos `.stb` importantes
5. **Versionamento** Git para rastrear mudanças

## Referências

- [Guia de Início Rápido](getting-started.md)
- [Referência da API](api.md)
- Manual ANATEM v12.10 (incluído em `markdowns_reference/`)
