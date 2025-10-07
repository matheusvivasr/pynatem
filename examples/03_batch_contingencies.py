"""
Exemplo 03: Executar um lote de contingências

Demonstra como gerar e executar múltiplas contingências a partir
de um caso base.
"""

from pyanatem import EnsaioAnatem

def executar_contingencias():
    # Definir contingências a simular
    contingencias = [
        ("Deslig_Linha_1201-1202", "1201 1202 1"),
        ("Deslig_Linha_1301-1302", "1301 1302 1"),
        ("Deslig_Gerador_1001", "1001"),
        ("Deslig_Linha_1401-1402", "1401 1402 1"),
    ]
    
    print(f"🔧 Preparando {len(contingencias)} contingências...")
    
    # Criar ensaio
    ensaio = EnsaioAnatem.de_contingencias(
        caso_base="base.stb",
        contingencias=contingencias,
        diretorio_saida="resultados_contingencias/"
    )
    
    # Executar (sequencial por enquanto)
    print("▶️  Executando simulações...")
    resultados = ensaio.executar_contingencias(paralelo=False)
    
    # Analisar resultados
    print("\n📊 Resultados:")
    print("-" * 60)
    
    sucessos = 0
    falhas = 0
    
    for contingencia, resultado in resultados.items():
        if resultado.sucesso:
            print(f"✅ {contingencia}: OK")
            sucessos += 1
        else:
            print(f"❌ {contingencia}: FALHOU")
            print(f"   Erro: {resultado.mensagem_erro}")
            falhas += 1
    
    print("-" * 60)
    print(f"📈 Total: {sucessos} sucessos, {falhas} falhas")

if __name__ == "__main__":
    executar_contingencias()
