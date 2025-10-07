"""
Exemplo 01: Criar um caso básico do zero

Este exemplo mostra como criar um caso ANATEM completo do zero,
incluindo simulação, eventos e variáveis de saída.
"""

from pyanatem import CasoAnatem

def criar_caso_basico():
    # Criar caso vazio
    caso = CasoAnatem()
    
    # Configurar simulação
    caso.dsim.tfim = 30.0       # Tempo final: 30s
    caso.dsim.delt = 0.01       # Passo: 10ms
    caso.dsim.dtout = 0.1       # Saída a cada 100ms
    caso.dsim.tini = 0.0        # Tempo inicial: 0s
    
    # Associar arquivos
    caso.darq.arq_sav = "sistema.sav"
    caso.darq.arq_plt = "saidas.plt"
    caso.darq.arq_rela = "relatorio.rela"
    
    # Adicionar evento: curto-circuito em barra
    caso.curto_barra(
        barra=1001,
        tempo_inicio=1.0,
        tempo_fim=1.1  # 100ms de duração
    )
    
    # Adicionar variáveis de saída
    caso.dplt.tensao_barra(barra=1001)
    caso.dplt.tensao_barra(barra=1002)
    caso.dplt.potencia_circuito(de=1001, para=1002, circuito=1)
    
    # Validar
    avisos = caso.validar()
    if avisos:
        print("⚠️ Avisos de validação:")
        for aviso in avisos:
            print(f"  - {aviso}")
    
    # Salvar
    caso.exportar("exemplo_basico.stb")
    print("✅ Caso criado: exemplo_basico.stb")

if __name__ == "__main__":
    criar_caso_basico()
