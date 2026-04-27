#!/usr/bin/env python3
"""
Exemplo 11: Modos de Análise v1.8 — Integrado

Demonstra:
- v1.8.1: Análise de Contingência (N-1)
- v1.8.2: Multi-infeed (EAMI/EAIF)
- v1.8.3: Séries Temporais (TIME/DSTO)
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from pynatem.analise_v18 import (
    # v1.8.1
    Contingencia, AnalisadorContingencia,
    # v1.8.2
    AnalisadorMultiInfeed, TipoAnaliseMultiInfeed,
    # v1.8.3
    Timestamp, CenarioEstocastico, AnaliseSerieTemporal,
)

print("=" * 80)
print("EXEMPLO 11: Modos de Análise v1.8 — Integrado")
print("=" * 80)

# ============================================================================
# v1.8.1: Análise de Contingência (N-1)
# ============================================================================
print("\n[v1.8.1] ANÁLISE DE CONTINGÊNCIA (N-1, §7.3)")
print("-" * 80)

analisador_ctg = AnalisadorContingencia(
    caso_base_path=Path("casos/base_2026_07.stb"),
    historico_path=Path("dados/hist_2026.his"),
    caso_numero=1,
    identificador="contingencia_SIN_2026_07",
    processos_paralelos=4,
)

# Contingências típicas de rede
contingencias = [
    Contingencia(
        ident="CT_LT_230_01",
        titulo="Desligamento de LT 230kV Rio-Brasília (principal)",
        eventos=["0.10  3  1  2  1  0.0  0.0  0.0"],  # Formato DEVT simplificado
    ),
    Contingencia(
        ident="CT_LT_345_01",
        titulo="Desligamento de LT 345kV Brasília-Sul (backup)",
        eventos=["0.10  3  1  3  1  0.0  0.0  0.0"],
    ),
    Contingencia(
        ident="CT_GER_01",
        titulo="Perda de Gerador Síncrono em Brasília",
        eventos=["0.05  4  1  1  0  0.0  0.0  0.0"],  # Desligamento máquina
    ),
]

for ctg in contingencias:
    analisador_ctg.adicionar_contingencia(ctg)

# Validar configuração
valido, erros = analisador_ctg.validar_configuracao()
if not valido:
    print(f"Erros na configuração: {erros}")
else:
    print(f"✓ Configuração válida")
    print(f"✓ {len(analisador_ctg.contingencias)} contingências carregadas")
    print(f"✓ Paralelização: {analisador_ctg.processos_paralelos} processos")
    print(f"\nArquivo de contingências será gerado em:")
    print(f"  {analisador_ctg.identificador}/contingencias.txt")

print("\nExemplo de contingência gerada:")
print(analisador_ctg.contingencias[0].serializar_contingencia())

# ============================================================================
# v1.8.2: Análise Multi-infeed
# ============================================================================
print("=" * 80)
print("[v1.8.2] ANÁLISE MULTI-INFEED (§36-37)")
print("-" * 80)

# Modo 1: EAMI automático (elos HVDC LCC)
print("\n1. EAMI — Cálculo Automático MIIF (elos HVDC LCC)")
analisador_eami = AnalisadorMultiInfeed(
    tipo=TipoAnaliseMultiInfeed.EAMI,
    peco_enabled=True,
    exportar_csv=True,
)
print(analisador_eami.resumo_analise())

# Modo 2: EAIF (interação fontes renováveis)
print("2. EAIF — Interação Fontes Shunt Controladas (Eólica/Solar)")
analisador_eaif = AnalisadorMultiInfeed(
    tipo=TipoAnaliseMultiInfeed.EAIF,
    peco_enabled=True,
    exportar_csv=True,
)
print(analisador_eaif.resumo_analise())

# Modo 3: Manual com barras específicas
print("3. DMIF — Especificação Manual de Barras")
analisador_dmif = AnalisadorMultiInfeed(
    tipo=TipoAnaliseMultiInfeed.MANUAL,
)
analisador_dmif.adicionar_barra(1)
analisador_dmif.adicionar_barra(2)
analisador_dmif.adicionar_barra(3)
print(f"Barras selecionadas: {analisador_dmif.barras}")
print("\nBloco DMIF gerado:")
print(analisador_dmif.gerar_blocos_dmif())

# ============================================================================
# v1.8.3: Séries Temporais
# ============================================================================
print("\n" + "=" * 80)
print("[v1.8.3] ANÁLISE COM SÉRIES TEMPORAIS (§46.72, §46.60)")
print("-" * 80)

# Timestamp: Quando ocorre a simulação
print("\n1. TIMESTAMP (TIME, §46.72)")
timestamp = Timestamp(
    ano=2026, mes=7, dia=10,
    hora=14, minuto=30, segundo=0,
    utc_offset="UTC -03:00"
)
valido, erros = timestamp.validar()
print(f"Timestamp: 2026/07/10 14:30:00 UTC -03:00")
print(f"Válido: {valido}")

# Cenário Estocástico: Qual série hidrológica usar
print("\n2. CENÁRIO ESTOCÁSTICO (DSTO, §46.60)")
cenario = CenarioEstocastico(
    tipo="HIDRO",
    serie=1984,  # Série histórica 1984 (enchente)
    patamar=1,   # Patamar 1 (seco)
)
valido, erros = cenario.validar()
print(f"Tipo: HIDRO")
print(f"Série: 1984 (enchente)")
print(f"Patamar: 1 (seco)")
print(f"Válido: {valido}")

# Integração completa: TIME + DSTO + USIHID
print("\n3. ANÁLISE INTEGRADA — TIME + DSTO + Série Temporal")
analise_st = AnaliseSerieTemporal(
    timestamp=timestamp,
    cenario=cenario,
    arquivo_usihid=Path("dados/usihid.csv"),
)

valido, erros = analise_st.validar()
print(f"Configuração válida: {valido}")
if not valido:
    print(f"Erros: {erros}")

print("\nBlocos gerados para arquivo STB:")
print(analise_st.gerar_blocos())

# ============================================================================
# Resumo Integrado
# ============================================================================
print("\n" + "=" * 80)
print("RESUMO — ETAPA v1.8 COMPLETA")
print("=" * 80)
print(f"""
v1.8.1 — Análise de Contingência (N-1):
  ✓ {len(analisador_ctg.contingencias)} contingências definidas
  ✓ Paralelização: {analisador_ctg.processos_paralelos} processos
  ✓ Formato: CONTINGENCIA / IDENT / TITULO / DEVT / FIMCTG / FIM

v1.8.2 — Análise Multi-infeed:
  ✓ EAMI: Cálculo automático MIIF (elos HVDC LCC)
  ✓ EAIF: Interação fontes shunt controladas (Eólica/Solar)
  ✓ DMIF: Especificação manual de barras
  ✓ Saída: Índices em OUT ou CSV (MIIF)

v1.8.3 — Séries Temporais:
  ✓ TIME: Timestamp da análise (YYYY/MM/DD HH:MM:SS formato)
  ✓ DSTO: Cenário estocástico (série hidrológica + patamar)
  ✓ USIHID: Arquivo de séries externas
  ✓ SERIET: Integração com Bloco SERIET no CDU

CASOS DE USO:
  1. Contingência N-1: Avaliar severidade de desligamentos
  2. Multi-infeed: Robustez de sistemas com múltiplos HVDC/renováveis
  3. Séries Temporais: Variabilidade hidrológica + temporal

PRÓXIMAS VERSÕES:
  v1.9 — Algoritmos de Pós-Falta (estabilidade transitória)
  v2.0 — Cobertura total Manual ANATEM 12.10
""")
