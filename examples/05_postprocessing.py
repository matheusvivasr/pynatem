"""
Exemplo 05: Pós-processamento e análise de resultados

Demonstra como ler arquivos de saída (.plt, .rela) e analisar resultados.
"""

from pynatem.posprocessamento import LeitorPLT, LeitorRelatorio

def analisar_resultados(arquivo_plt, arquivo_rela):
    print("📊 Análise de Resultados ANATEM\n")

    # 1. Ler arquivo .rela (relatório de execução)
    print("1️⃣  Lendo relatório de execução...")
    try:
        leitor_rel = LeitorRelatorio()
        relatorio = leitor_rel.ler(arquivo_rela)

        print(f"   ✅ Simulação: {'Sucesso' if relatorio.sucesso else 'FALHOU'}")
        print(f"   Tempo de execução: {relatorio.tempo_execucao:.2f}s")

        if not relatorio.sucesso:
            print(f"   Erro: {relatorio.mensagem_erro}")
    except Exception as e:
        print(f"   ⚠️  Erro ao ler relatório: {e}")

    # 2. Ler arquivo .plt (variáveis de saída)
    print("\n2️⃣  Lendo arquivo de plotagem...")
    try:
        leitor_plt = LeitorPLT()
        dados = leitor_plt.ler(arquivo_plt)

        # Como DataFrame (requer pandas)
        try:
            df = dados.como_dataframe()
            print(f"   ✅ Dados carregados: {len(df)} linhas")
            print(f"   Colunas: {list(df.columns)[:5]}...")

            # Exemplo: encontrar tensão máxima
            if "tensao" in str(df.columns).lower():
                max_tensao = df["tensao"].max() if "tensao" in df.columns else None
                if max_tensao:
                    print(f"\n   Tensão máxima: {max_tensao:.3f} pu")

        except ImportError:
            print("   ⚠️  pandas não instalado. Use: pip install pandas")

    except Exception as e:
        print(f"   ⚠️  Erro ao ler arquivo .plt: {e}")

if __name__ == "__main__":
    # Usar seus próprios arquivos de resultado
    analisar_resultados("saidas.plt", "relatorio.rela")
