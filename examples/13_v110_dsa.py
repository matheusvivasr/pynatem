#!/usr/bin/env python3
"""
Exemplo 13: Controle Dinâmico Adaptativo v1.10 — DSA

Demonstra:
- v1.10.1: Avaliação de Segurança Dinâmica (DSA)
- v1.10.2: Recomendações Preventivas
- v1.10.3: Análise Multi-caso com Snapshots
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from pynatem.dsa_v110 import (
    # v1.10.1
    ElementoSeguranca, TipoElementoSeguranca, StatusSeguranca, AvaliadorDSA,
    # v1.10.2
    AcaoPreventiva, TipoAcaoPreventiva, RecomendadorDSA,
    # v1.10.3
    CasoMultiplesDSA,
)

print("=" * 80)
print("EXEMPLO 13: Controle Dinâmico Adaptativo v1.10 — DSA")
print("=" * 80)

# ============================================================================
# v1.10.1: Avaliação de Segurança Dinâmica (DSA, §47.101 RSEG)
# ============================================================================
print("\n[v1.10.1] AVALIAÇÃO DE SEGURANÇA DINÂMICA (DSA)")
print("-" * 80)

# Sistema de transmissão: Caso Brasília
dsa_brasilia = AvaliadorDSA(
    nome_caso="Contingencia_DES_LT_500kV_Rio-Brasilia",
    tempo_simulacao=3.0,
)

# Elementos críticos: Circuitos de transmissão
print("Circuitos de Transmissão:")
circuitos = [
    ("LT_500kV_Rio-Brasilia", 110.0),
    ("LT_500kV_Brasilia-Sul", 105.0),
    ("LT_230kV_Rio-Brasilia", 95.0),
]
for nome, limite in circuitos:
    dsa_brasilia.adicionar_elemento(
        ElementoSeguranca(
            tipo=TipoElementoSeguranca.CIRCUITO,
            identificacao=nome,
            limite_emergencia=limite,
        )
    )
    print(f"  • {nome}: Limite {limite:.0f}%")

# Barras críticas
print("\nBarras Críticas:")
barras = [
    ("Barra_Brasilia_500kV", 110.0, 100.0),
    ("Barra_Rio_500kV", 115.0, 105.0),
]
for nome, limite, alerta in barras:
    dsa_brasilia.adicionar_elemento(
        ElementoSeguranca(
            tipo=TipoElementoSeguranca.BARRA,
            identificacao=nome,
            limite_emergencia=limite,
            limite_alerta=alerta,
        )
    )
    print(f"  • {nome}: Limite {limite:.0f}% / Alerta {alerta:.0f}%")

# Geração
print("\nGeração:")
geracao = [
    ("Gen_Itaipu_Norte_Reativo", 200.0),
    ("Gen_Itaipu_Sul_Reativo", 200.0),
]
for nome, limite in geracao:
    dsa_brasilia.adicionar_elemento(
        ElementoSeguranca(
            tipo=TipoElementoSeguranca.GERACAO,
            identificacao=nome,
            limite_emergencia=limite,
        )
    )
    print(f"  • {nome}: Limite {limite:.0f} MVar")

print("\n" + "-" * 80)
print("Avaliação Pós-Falta:")

# Valores observados na simulação após falta
valores_picos = [105.0, 112.0, 90.0, 108.0, 98.0, 195.0, 188.0]

print("Valores no pico do distúrbio:")
resultados_dsa = dsa_brasilia.avaliar_sistema_completo(valores_picos)

violacoes = 0
alertas = 0
seguros = 0

for elem_id, (status, msg, margem) in sorted(resultados_dsa.items()):
    print(f"  [{status.value:<10}] {msg} (margem: {margem:>7.1f}%)")
    if status == StatusSeguranca.VIOLACAO:
        violacoes += 1
    elif status == StatusSeguranca.ALERTA:
        alertas += 1
    else:
        seguros += 1

print(f"\nResumo: {seguros} SEGURO, {alertas} ALERTA, {violacoes} VIOLAÇÃO")

# ============================================================================
# v1.10.2: Recomendações Preventivas
# ============================================================================
print("\n" + "=" * 80)
print("[v1.10.2] RECOMENDAÇÕES PREVENTIVAS")
print("-" * 80)

recomendador = RecomendadorDSA(margem_seguranca_minima=5.0)

# Gerar recomendações baseado em violações/alertas
recomendacoes = recomendador.recomendar_acoes(resultados_dsa)

if recomendacoes:
    print(recomendador.gerar_relatorio_recomendacoes(recomendacoes))
else:
    print("Nenhuma ação preventiva necessária — Sistema dentro dos limites.")

# ============================================================================
# v1.10.3: Análise Multi-caso com Snapshots
# ============================================================================
print("\n" + "=" * 80)
print("[v1.10.3] ANÁLISE MULTI-CASO COM SNAPSHOTS")
print("-" * 80)

multicaso = CasoMultiplesDSA(
    nome_caso_base="Caso_Base_Brasilia",
    arquivo_snapshot=Path("snapshots/caso_base.sav"),
)

# Contingências a analisar
contingencias = [
    "CTG_DES_LT_500kV_Rio-Brasilia",
    "CTG_DES_LT_500kV_Brasilia-Sul",
    "CTG_PERDA_GER_ITAIPU_NORTE",
    "CTG_DES_TRAFO_GRANDE_500kV",
]

print(f"Contingências a simular ({len(contingencias)}):")
for ctg in contingencias:
    multicaso.adicionar_contingencia(ctg)
    print(f"  • {ctg}")

print("\nFluxo de Análise DSA Multi-caso:")
print("-" * 80)
print("1. Gravar snapshot do caso base (inicializado)")
print("2. Para cada contingência:")
print("   a. Restaurar snapshot")
print("   b. Executar simulação (EXSI)")
print("   c. Gerar relatório DSA (RSEG)")
print("3. Comparar resultados entre contingências")
print("4. Identificar cenários críticos")
print("5. Recomendar ações preventivas por cenário")

# ============================================================================
# Resumo Integrado
# ============================================================================
print("\n" + "=" * 80)
print("RESUMO — ETAPA v1.10 (Controle Dinâmico Adaptativo - DSA)")
print("=" * 80)
print(f"""
v1.10.1 — Avaliação de Segurança Dinâmica (§47.101 RSEG):
  ✓ Monitora: Circuitos (carregamento), Barras (tensão), Geração (reativo)
  ✓ Compara: Valores simulados vs. Limites de emergência (Anarede)
  ✓ Status: SEGURO, ALERTA, VIOLAÇÃO, CRÍTICO
  ✓ Calcula: Margens de segurança para cada elemento
  ✓ Relatório: RSEG com listagem de elementos e status

v1.10.2 — Recomendações Preventivas:
  ✓ Tipos: REDUCAO_CARGA, AUMENTO_GERACAO, DESLIGAMENTO_CIRCUITO, etc
  ✓ Criticidade: Recomendação, Desejável, Crítica
  ✓ Geração automática: Análise de violações/alertas
  ✓ Magnitude: Magnitude recomendada da ação
  ✓ Tempo: Instante ideal para executar ação
  ✓ Relatório: Listagem de ações por criticidade

v1.10.3 — Análise Multi-caso com Snapshots:
  ✓ Snapshot: Gravação/restauração de estado inicial (§46.71 SNAP)
  ✓ Multi-caso: Executar vários cenários de contingência
  ✓ Reutilização: Inicialização eficiente via snapshot
  ✓ Economia: Reduz tempo de CPU (não reinicializa cada caso)
  ✓ Sequência: Comandos automatizados para EXSI + RSEG

ESPECIFICAÇÃO:
  • §47.101 (RSEG): Monitoração critérios segurança dinâmica
  • §46.71 (SNAP): Gravação/restauração snapshots
  • §7.4 (Pós-processamento): Critérios de severidade
  • Manual ANATEM 12.10: Rigorosamente conforme

CASOS DE USO:
  1. DSA Online: Monitorar segurança dinâmica em tempo real
  2. Análise Offline: Avaliar contingências críticas
  3. Recomendações: Gerar sugestões preventivas automáticas
  4. Multi-caso: Executar múltiplos cenários eficientemente

PRÓXIMAS VERSÕES:
  v1.11 — Modelos de Máquina Avançados (Phase-Locked Loop, VSC-HVDC)
  v2.0 — Cobertura total Manual ANATEM 12.10 (200+ blocos, 10 versões)
""")
