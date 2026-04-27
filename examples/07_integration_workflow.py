"""
Exemplo 07: Workflow Integrado (Completo)

Exemplo avançado que demonstra um workflow completo:
1. Carregar caso base
2. Gerar contingências
3. Executar simulações
4. Processar resultados
5. Gerar relatório
"""

from pathlib import Path
from pynatem import CasoAnatem, EnsaioAnatem
from pynatem.posprocessamento import LeitorPLT

def workflow_completo(
    arquivo_base,
    contingencias_lista,
    diretorio_saida="resultados_workflow"
):
    """
    Execute um workflow completo de análise de contingências.

    Args:
        arquivo_base: Caminho do caso base (.stb)
        contingencias_lista: Lista de tuplas (nome, descricao_contingencia)
        diretorio_saida: Diretório para salvar resultados
    """

    print("=" * 70)
    print("🚀 WORKFLOW INTEGRADO DE ANÁLISE DE CONTINGÊNCIAS")
    print("=" * 70)

    diretorio = Path(diretorio_saida)
    diretorio.mkdir(exist_ok=True)

    # Fase 1: Validação do caso base
    print("\n📋 Fase 1: Validação do Caso Base")
    print("-" * 70)

    try:
        caso_base = CasoAnatem.ler(arquivo_base)
        print(f"✅ Caso carregado: {arquivo_base}")

        avisos = caso_base.validar()
        if avisos:
            print("⚠️  Avisos encontrados:")
            for aviso in avisos:
                print(f"   - {aviso}")
        else:
            print("✅ Caso válido (sem avisos)")
    except Exception as e:
        print(f"❌ Erro ao carregar caso: {e}")
        return

    # Fase 2: Preparação de contingências
    print("\n⚙️  Fase 2: Preparação de Contingências")
    print("-" * 70)

    print(f"Preparando {len(contingencias_lista)} contingências:")
    for i, (nome, desc) in enumerate(contingencias_lista, 1):
        print(f"  {i}. {nome}: {desc}")

    # Fase 3: Execução
    print("\n▶️  Fase 3: Execução de Simulações")
    print("-" * 70)

    try:
        ensaio = EnsaioAnatem.de_contingencias(
            caso_base=arquivo_base,
            contingencias=contingencias_lista,
            diretorio_saida=str(diretorio)
        )

        print(f"Executando {len(contingencias_lista)} casos...")
        resultados = ensaio.executar_contingencias(paralelo=False)

        sucessos = sum(1 for r in resultados.values() if r.sucesso)
        falhas = len(resultados) - sucessos

        print(f"\n✅ Execução concluída")
        print(f"   Sucessos: {sucessos}/{len(resultados)}")
        print(f"   Falhas: {falhas}/{len(resultados)}")

    except Exception as e:
        print(f"❌ Erro na execução: {e}")
        return

    # Fase 4: Processamento de resultados
    print("\n📊 Fase 4: Processamento de Resultados")
    print("-" * 70)

    try:
        # Exemplo: processar arquivo .plt do primeiro caso
        plt_file = diretorio / "saidas.plt"

        if plt_file.exists():
            leitor = LeitorPLT()
            dados = leitor.ler(str(plt_file))

            try:
                df = dados.como_dataframe()
                print(f"✅ Dados carregados: {len(df)} registros")

                # Análise simples
                if not df.empty:
                    print(f"   Colunas: {len(df.columns)}")
            except ImportError:
                print("⚠️  pandas não disponível para análise detalhada")
        else:
            print("⚠️  Arquivo .plt não encontrado")

    except Exception as e:
        print(f"⚠️  Erro ao processar resultados: {e}")

    # Fase 5: Relatório final
    print("\n📈 Fase 5: Relatório Final")
    print("-" * 70)

    print(f"📁 Diretório de saída: {diretorio.absolute()}")
    print(f"📊 Arquivos gerados:")

    for arquivo in sorted(diretorio.glob("*")):
        tamanho = arquivo.stat().st_size / 1024  # KB
        print(f"   - {arquivo.name} ({tamanho:.1f} KB)")

    print("\n" + "=" * 70)
    print("✅ WORKFLOW CONCLUÍDO COM SUCESSO!")
    print("=" * 70)

if __name__ == "__main__":
    # Exemplo de uso
    contingencias = [
        ("Caso_Base", "Sem contingências (controle)"),
        ("Deslig_Linha_1", "1201 1202 1"),
        ("Deslig_Linha_2", "1301 1302 1"),
        ("Deslig_Gerador", "1001"),
    ]

    workflow_completo(
        arquivo_base="base.stb",
        contingencias_lista=contingencias,
        diretorio_saida="resultados_workflow"
    )
