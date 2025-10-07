"""
Exemplo 04: Validação cruzada (STB ↔ SAV)

Demonstra como validar um caso STB contra um arquivo SAV do ANAREDE.
"""

from pyanatem import CasoAnatem

def validar_caso_contra_sav(arquivo_stb, arquivo_sav):
    # Carregar caso
    caso = CasoAnatem.ler(arquivo_stb)
    
    print(f"📋 Validando: {arquivo_stb}")
    print(f"   Contra: {arquivo_sav}\n")
    
    # 1. Validação interna
    print("🔍 1. Validação Interna (STB):")
    avisos = caso.validar()
    
    if not avisos:
        print("   ✅ Nenhum aviso")
    else:
        for aviso in avisos:
            print(f"   ⚠️  {aviso}")
    
    # 2. Validação cruzada (STB ↔ SAV)
    print("\n🔍 2. Validação Cruzada (STB ↔ SAV):")
    try:
        inconsistencias = caso.validar_contra_sav(arquivo_sav)
        
        if not inconsistencias:
            print("   ✅ Nenhuma inconsistência")
        else:
            for incon in inconsistencias:
                print(f"   ❌ {incon}")
    except Exception as e:
        print(f"   ⚠️  Não foi possível validar contra SAV: {e}")
    
    # 3. Teste de roundtrip
    print("\n🔍 3. Teste de Roundtrip:")
    print("   Exportando → Relendo → Comparando...")
    
    try:
        caso_original = caso
        caso.exportar("temp_roundtrip.stb")
        caso_recarregado = CasoAnatem.ler("temp_roundtrip.stb")
        
        if caso_original == caso_recarregado:
            print("   ✅ Roundtrip OK (sem perdas)")
        else:
            print("   ⚠️  Diferenças detectadas no roundtrip")
    except Exception as e:
        print(f"   ❌ Erro no roundtrip: {e}")

if __name__ == "__main__":
    validar_caso_contra_sav("base.stb", "sistema.sav")
