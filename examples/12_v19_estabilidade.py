#!/usr/bin/env python3
"""
Exemplo 12: Algoritmos de Pós-Falta v1.9 — Estabilidade Transitória

Demonstra:
- v1.9.1: Critérios de Estabilidade (Tensão, Reativo, Carregamento, Relés, Angular)
- v1.9.2: Perda de Sincronismo (Loss of Synchronism)
- v1.9.3: Recuperação de Frequência
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from pyanatem.estabilidade_v19 import (
    # v1.9.1
    CriterioTensao, CriterioReativoGER, CriterioReativoCER,
    CriterioCarregamento, CriterioReles, CriterioAngular,
    AnalisadorEstabilidade,
    # v1.9.2
    IndicadorSincronismo, MonitorSincronismo,
    # v1.9.3
    AlgoritmoRecuperacaoFrequencia,
)

print("=" * 80)
print("EXEMPLO 12: Algoritmos de Pós-Falta v1.9 — Estabilidade Transitória")
print("=" * 80)

# ============================================================================
# v1.9.1: Critérios de Estabilidade Transitória
# ============================================================================
print("\n[v1.9.1] CRITÉRIOS DE ESTABILIDADE TRANSITÓRIA (§7.4)")
print("-" * 80)

# Criar analisador com múltiplos critérios
analisador = AnalisadorEstabilidade()

# Critérios de tensão (5 tipos)
print("\nCritérios de Tensão:")
print("  1. Primeira oscilação: Vmin = 85%")
analisador.adicionar_criterio_tensao(
    CriterioTensao(
        tipo=1,
        vmin_percentual=85.0,
        alerta_1=90.0,
        alerta_2=85.0,
    )
)

print("  2. Segunda oscilação: Vmin = 80% (500kV: 90%)")
analisador.adicionar_criterio_tensao(
    CriterioTensao(
        tipo=2,
        vmin_percentual=80.0,
        vmin_500kv=90.0,
    )
)

print("  3. Oscilações posteriores: Amplitude máxima @ t > 3s")
analisador.adicionar_criterio_tensao(
    CriterioTensao(
        tipo=3,
        tverif=3.0,
        amax=0.05,  # 5% de amplitude máxima
    )
)

print("  4. Variação final de tensão: ΔV máximo = 2%")
analisador.adicionar_criterio_tensao(
    CriterioTensao(
        tipo=4,
        var_maxima=2.0,
    )
)

# Reativo
print("\nCritérios de Reativo:")
print("  • Gerador (GER): Habilitado — verifica limites DBAR")
analisador.definir_reativo_ger(CriterioReativoGER())

print("  • Compensador (CER): Habilitado — verifica limites DCER")
analisador.definir_reativo_cer(CriterioReativoCER())

# Carregamento
print("\nCritério de Carregamento:")
print("  • Circuitos: 90% de limite de emergência")
analisador.definir_carregamento(
    CriterioCarregamento(percentual_limite=90.0)
)

# Relés
print("\nCritério de Relés:")
print("  • Impedância, Sub/Sobtensão, Sobrecorrente, Subfrequência")
analisador.definir_reles(CriterioReles())

# Validar
print("\n" + "-" * 80)
valido, erros = analisador.validar()
if valido:
    print(f"[OK] Configuração de critérios validada")
    print(analisador.resumo_analise())
else:
    print(f"[ERRO] Erros de configuração:")
    for erro in erros:
        print(f"  - {erro}")

# ============================================================================
# v1.9.2: Perda de Sincronismo
# ============================================================================
print("\n" + "=" * 80)
print("[v1.9.2] PERDA DE SINCRONISMO (Loss of Synchronism)")
print("-" * 80)

monitor = MonitorSincronismo()

# Máquinas síncronas do sistema
maquinas = [
    ("GEN_BRASILIA", 1, 360.0),  # (nome, ncdu, ângulo_max)
    ("GEN_SUL", 2, 360.0),
    ("GER_ITAIPU_NORTE", 3, 360.0),
    ("GER_ITAIPU_SUL", 4, 360.0),
]

print("Máquinas monitoradas:")
for nome, ncdu, ang_max in maquinas:
    monitor.adicionar_indicador(
        IndicadorSincronismo(ncdu=ncdu, nome=nome, angulo_max_graus=ang_max)
    )
    print(f"  • {nome} (NCDU={ncdu}, limite={ang_max}°)")

# Simular falha: desligamento de linha e observar ângulos
print("\nSimulação: Desligamento de LT 500kV Rio-São Paulo")
print("Ângulos observados no pico do distúrbio:")

angulos_criticos = {
    1: 120.0,   # Estável
    2: 155.0,   # Próximo ao limite
    3: 195.0,   # Crítico (> 180°) — PERDA DE SÍNCRONO
    4: 85.0,    # Estável
}

print("-" * 80)
resultados = monitor.avaliar_sistema(angulos_criticos)
for ncdu in sorted(resultados.keys()):
    estavel, msg = resultados[ncdu]
    status = "[OK]" if estavel else "[FALHA]"
    print(f"{status} GER {ncdu}: {msg}")

# ============================================================================
# v1.9.3: Recuperação de Frequência
# ============================================================================
print("\n" + "=" * 80)
print("[v1.9.3] RECUPERAÇÃO DE FREQUÊNCIA")
print("-" * 80)

alg_freq = AlgoritmoRecuperacaoFrequencia(
    frecuencia_nominal=60.0,  # Brasil
    df_max_admitida=2.0,  # Máxima queda permitida
    tempo_recuperacao=5.0,  # Tempo máximo para retornar
    margem_estabilidade=0.5,  # Margem de segurança
)

print("Parâmetros de Recuperação de Frequência:")
print(f"  • Frequência nominal: {alg_freq.frecuencia_nominal} Hz")
print(f"  • ΔF máxima admitida: {alg_freq.df_max_admitida} Hz")
print(f"  • Tempo máx. recuperação: {alg_freq.tempo_recuperacao} s")
print(f"  • Margem segurança: {alg_freq.margem_estabilidade} Hz")

print("\n" + "-" * 80)
print("Cenários de Distúrbio:")

cenarios = [
    ("Distúrbio Pequeno", 59.5, 1.2, True),
    ("Distúrbio Médio", 58.5, 3.2, True),
    ("Distúrbio Grande (queda excessiva)", 57.0, 2.0, False),
    ("Distúrbio Grande (recuperação lenta)", 59.0, 6.5, False),
]

for descricao, f_min, t_rec, esperado in cenarios:
    estavel, msg = alg_freq.avaliar_recuperacao(f_min, t_rec)
    status = "[OK]" if estavel else "[FALHA]"
    resultado = "ESPERADO" if estavel == esperado else "INESPERADO"
    print(f"{status} {descricao}: {msg} ({resultado})")

# ============================================================================
# Resumo Integrado
# ============================================================================
print("\n" + "=" * 80)
print("RESUMO — ETAPA v1.9 (Algoritmos de Pós-Falta)")
print("=" * 80)
print(f"""
v1.9.1 — Critérios de Estabilidade Transitória:
  ✓ Tensão: 5 critérios (primeira oscilação, segunda, posteriores, variação, limite)
  ✓ Reativo: GER (gerador) + CER (compensador)
  ✓ Carregamento: Circuitos em relação a limites emergência
  ✓ Relés: Impedância, Sub/Sobtensão, Sobrecorrente, Subfrequência
  ✓ Angular: Específico para Tucuruí-Paulo Afonso (Norte-Nordeste)
  ✓ Níveis de alerta: OK, Alerta 1 (médio), Alerta 2 (severo)

v1.9.2 — Perda de Sincronismo:
  ✓ IndicadorSincronismo: Monitora ângulo máximo de máquina síncrona
  ✓ Limite crítico: 180° (perda irrecuperável)
  ✓ Opção PECO: Transforma erro em aviso se > 1000°
  ✓ MonitorSincronismo: Avalia múltiplas máquinas

v1.9.3 — Recuperação de Frequência:
  ✓ Frequência nominal (60 Hz para Brasil)
  ✓ ΔF máxima admitida (limite de queda)
  ✓ Tempo máximo recuperação (retorno a nominal)
  ✓ Margem de estabilidade (buffer de segurança)
  ✓ Avaliação de cenários de distúrbio

ESPECIFICAÇÃO:
  • §7.4 (Pós-processamento): Critérios e análise de severidade
  • §5 (Execução): Monitoração de perda de síncrono
  • Manual ANATEM 12.10: Rigorosamente conforme

PRÓXIMAS VERSÕES:
  v1.10 — Controle Dinâmico Adaptativo (DSA - Dynamic Security Assessment)
  v2.0 — Cobertura total Manual ANATEM 12.10
""")
