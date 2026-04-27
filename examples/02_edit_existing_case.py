"""
Exemplo 02: Editar um caso existente

Demonstra como carregar um arquivo .stb, modificar seus parâmetros
e salvar com um novo nome.
"""

from pynatem import CasoAnatem

def editar_caso_existente(arquivo_entrada, arquivo_saida):
    # Carregar caso existente
    caso = CasoAnatem.ler(arquivo_entrada)

    print(f"📖 Caso carregado: {arquivo_entrada}")
    print(f"   Tempo final original: {caso.dsim.tfim}s")

    # Modificar parâmetros
    caso.dsim.tfim = 45.0  # Aumentar tempo final para 45s
    caso.dsim.delt = 0.005  # Reduzir passo para 5ms

    # Adicionar novo evento
    caso.curto_barra(
        barra=2001,
        tempo_inicio=5.0,
        tempo_fim=5.15
    )

    # Adicionar novas variáveis de saída
    caso.dplt.velocidade_maquina(maquina=1001)
    caso.dplt.frequencia_barra(barra=1001)

    # Validar mudanças
    avisos = caso.validar()
    if not avisos:
        print("✅ Caso validado com sucesso")

    # Salvar com novo nome
    caso.exportar(arquivo_saida)
    print(f"💾 Caso salvo: {arquivo_saida}")
    print(f"   Tempo final novo: {caso.dsim.tfim}s")

if __name__ == "__main__":
    # Usar seus próprios arquivos
    editar_caso_existente("base.stb", "base_modificada.stb")
