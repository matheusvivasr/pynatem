"""Benchmarks de performance para operações centrais do pynatem.

Uso:
    python benchmarks/bench_core.py

Mede o tempo de criação, exportação, leitura e validação de casos.
Não requer dependências além da stdlib.
"""

import time
import tempfile
from pathlib import Path

from pYnatem import CasoAnatem


def _cronometrar(descricao, repeticoes, funcao):
    inicio = time.perf_counter()
    for _ in range(repeticoes):
        funcao()
    decorrido = time.perf_counter() - inicio
    por_op_ms = decorrido / repeticoes * 1000
    print(f"  {descricao:<32} {decorrido:6.3f}s total  |  {por_op_ms:7.3f} ms/op ({repeticoes}x)")


def bench_criacao(repeticoes=1000):
    _cronometrar("Criar caso vazio", repeticoes, lambda: CasoAnatem())


def bench_exportacao(repeticoes=200):
    caso = CasoAnatem()
    caso.dsim.tfim = 30.0
    for i in range(10):
        caso.curto_barra(1000 + i, 1.0 + i, 0.1)

    with tempfile.TemporaryDirectory() as tmp:
        destino = str(Path(tmp) / "bench.stb")
        _cronometrar("Exportar caso (10 eventos)", repeticoes, lambda: caso.exportar(destino))


def bench_leitura(repeticoes=200):
    caso = CasoAnatem()
    caso.dsim.tfim = 30.0
    for i in range(10):
        caso.curto_barra(1000 + i, 1.0 + i, 0.1)

    with tempfile.TemporaryDirectory() as tmp:
        destino = str(Path(tmp) / "bench.stb")
        caso.exportar(destino)
        _cronometrar("Ler caso (10 eventos)", repeticoes, lambda: CasoAnatem.ler(destino))


def bench_validacao(repeticoes=500):
    caso = CasoAnatem()
    caso.dsim.tfim = 30.0
    for i in range(10):
        caso.curto_barra(1000 + i, 1.0 + i, 0.1)
    _cronometrar("Validar caso (10 eventos)", repeticoes, lambda: caso.validar())


def main():
    print("=" * 70)
    print("pynatem — Benchmarks de performance (operações centrais)")
    print("=" * 70)
    bench_criacao()
    bench_exportacao()
    bench_leitura()
    bench_validacao()
    print("=" * 70)
    print("Concluído.")


if __name__ == "__main__":
    main()
