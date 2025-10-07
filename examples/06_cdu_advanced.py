"""
Exemplo 06: Controladores Definidos pelo Usuário (CDU)

Demonstra como criar e usar CDU (Controladores Definidos pelo Usuário)
em um caso ANATEM.
"""

from pyanatem import CasoAnatem
from pyanatem.cdu import ControladorCDU

def criar_cdu_avancado():
    # Carregar caso base
    caso = CasoAnatem.ler("base.stb")
    
    print("🎮 Criando Controladores Definidos pelo Usuário (CDU)\n")
    
    # Exemplo 1: Controlador simples
    print("1️⃣  Criando CDU#1: Regulador de Velocidade")
    cdu1 = ControladorCDU(numero=1, nome="REGULADOR_VELOCIDADE")
    
    # Adicionar blocos (sintaxe simplificada)
    # Nota: A sintaxe exata depende da implementação
    try:
        cdu1.bloco_import(101, "ENTRADA_RPM", arquivo="entrada.txt")
        cdu1.bloco_logic(201, "LOGICA_CONTROLE")
        cdu1.bloco_output(301, "SAIDA_ATUADOR")
        
        # Adicionar ao caso
        caso.dcdu.adicionar_controlador(cdu1)
        print("   ✅ CDU#1 criado e adicionado")
    except Exception as e:
        print(f"   ⚠️  Erro ao criar CDU#1: {e}")
    
    # Exemplo 2: Controlador mais complexo
    print("\n2️⃣  Criando CDU#2: Amortecedor de Oscilações")
    cdu2 = ControladorCDU(numero=2, nome="AMORTECEDOR")
    
    try:
        cdu2.bloco_import(102, "ENTRADA_POTENCIA")
        cdu2.bloco_logic(202, "FILTRO_PASSA_BAIXAS")
        cdu2.bloco_logic(203, "COMPARADOR")
        cdu2.bloco_output(302, "SINAL_CONTROLE")
        
        caso.dcdu.adicionar_controlador(cdu2)
        print("   ✅ CDU#2 criado e adicionado")
    except Exception as e:
        print(f"   ⚠️  Erro ao criar CDU#2: {e}")
    
    # Validar
    print("\n3️⃣  Validando caso com CDU...")
    avisos = caso.validar()
    if not avisos:
        print("   ✅ Caso validado com sucesso")
    else:
        for aviso in avisos:
            print(f"   ⚠️  {aviso}")
    
    # Salvar
    arquivo_saida = "caso_com_cdu_avancado.stb"
    caso.exportar(arquivo_saida)
    print(f"\n✅ Caso com CDU salvo: {arquivo_saida}")
    
    # Informações
    print(f"\n📋 Informações:")
    print(f"   Total de CDUs: {len(caso.dcdu.controladores) if hasattr(caso.dcdu, 'controladores') else 'N/A'}")

if __name__ == "__main__":
    criar_cdu_avancado()
