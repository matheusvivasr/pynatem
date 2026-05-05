#!/usr/bin/env python3
"""
Exemplo 08: Pós-processamento v1.4 — Leitura .OUT + .PLT + Plotagem Python

Demonstra:
1. Leitura de arquivo .OUT (relatório de simulação)
2. Leitura de arquivo .PLT binário (extração de metadados)
3. Plotagem de séries temporais com matplotlib
4. Correlação de eventos com resultados
"""

import sys
from pathlib import Path

# Adicionar parent ao path para importar pynatem
sys.path.insert(0, str(Path(__file__).parent.parent))

from pynatem.posprocessamento_v2 import LeitorOUT, LeitorPLTBinario, PlotadorSerie

# Diretório de exemplos
exemplo_dir = Path(__file__).parent / "treinamentoWP"

print("=" * 70)
print("EXEMPLO 08: Pós-processamento ANATEM (v1.4)")
print("=" * 70)

# ============================================================================
# PASSO 1: Leitura de arquivo .OUT
# ============================================================================
print("\n[1/3] Lendo relatório .OUT...")
out_path = exemplo_dir / "TREINAMENTO_5_BARRAS.OUT"
resultado_out = LeitorOUT.ler(out_path)

print(f"  Versão ANATEM: {resultado_out['versao_anatem']}")
print(f"  Título: {resultado_out['titulo_caso']}")
print(f"  Tempo CPU: {resultado_out['tempo_cpu']:.2f}s")
print(f"  Eventos executados: {len(resultado_out['eventos_executados'])}")
for evt in resultado_out['eventos_executados']:
    print(f"    • T={evt['tempo']:.1f}s: {evt['descricao'][:50]}")

# ============================================================================
# PASSO 2: Leitura de arquivo .PLT binário
# ============================================================================
print("\n[2/3] Lendo arquivo .PLT binário...")
plt_path = exemplo_dir / "TREINAMENTO_5_BARRAS.PLT"
resultado_plt = LeitorPLTBinario.ler(plt_path)

caso_nome = ''.join(c if ord(c) < 128 else '?' for c in resultado_plt.titulo_caso)
print(f"  Caso: {caso_nome[:40]}")
print(f"  Pontos de tempo: {len(resultado_plt.tempo_global)}")
print(f"  Tempo final: {resultado_plt.tempo_final:.1f}s")
print(f"  Passo: {resultado_plt.passo:.6f}s")
print(f"  Variáveis: {len(resultado_plt.variaveis)}")

# ============================================================================
# PASSO 3: Plotagem das séries temporais
# ============================================================================
print("\n[3/3] Gerando gráficos...")
caminho_saida = Path(__file__).parent.parent / "resultado_simulacao.png"

try:
    fig = PlotadorSerie.plotar(
        resultado_plt,
        titulo="Simulação ANATEM — Treinamento 5 Barras",
        salvar_em=caminho_saida,
        mostrar=False  # Não mostrar em ambiente headless
    )
    print(f"  Gráfico salvo em: {caminho_saida}")
except Exception as e:
    print(f"  Aviso: Plotagem não disponível ({e})")

print("\n" + "=" * 70)
print("Pós-processamento concluído!")
print("=" * 70)
