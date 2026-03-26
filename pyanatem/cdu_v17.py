"""
cdu_v17.py – Definições e Inicializações de CDU (v1.7).

v1.7.1: DEFVAL, DEFVDF, DEFPLT — Inicialização de Modelos CDU
  • DEFVAL: Valores iniciais de variáveis
  • DEFVDF: Valores default para INPUT (equipamento ausente)
  • DEFPLT: Declaração de variáveis para plotagem automática
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional

@dataclass
class DefiniçãoValor:
    """DEFVAL — Valor inicial de variável CDU."""
    nome_variavel: str
    valor: float

    def serializar(self) -> str:
        return f"DEFVAL {self.nome_variavel:<15} {self.valor:>15.10f}\n"

@dataclass
class DefiniçãoValorDefault:
    """DEFVDF — Valor default para saída de INPUT (equipamento ausente)."""
    nome_saida: str  # saída do bloco INPUT
    valor: float  # valor numérico ou referência a #PARAM

    def serializar(self) -> str:
        return f"DEFVDF {self.nome_saida:<15} {self.valor:>15.10f}\n"

@dataclass
class DefiniçãoPlotagem:
    """DEFPLT — Variável CDU a ser plotada automaticamente."""
    nome_variavel: str
    descricao: str = ""

    def serializar(self) -> str:
        return f"DEFPLT {self.nome_variavel:<15} {self.descricao}\n"

@dataclass
class BlocoDefiniçõesCDU:
    """Agregador de definições DEFVAL/DEFVDF/DEFPLT para um CDU."""
    
    valores_iniciais: List[DefiniçãoValor] = field(default_factory=list)
    valores_default: List[DefiniçãoValorDefault] = field(default_factory=list)
    plotagem: List[DefiniçãoPlotagem] = field(default_factory=list)

    def adicionar_valor_inicial(self, nome: str, valor: float) -> "BlocoDefiniçõesCDU":
        """Adiciona valor inicial de variável."""
        self.valores_iniciais.append(DefiniçãoValor(nome, valor))
        return self

    def adicionar_valor_default(self, nome_saida: str, valor: float) -> "BlocoDefiniçõesCDU":
        """Adiciona valor default para INPUT."""
        self.valores_default.append(DefiniçãoValorDefault(nome_saida, valor))
        return self

    def adicionar_plotagem(self, nome: str, descricao: str = "") -> "BlocoDefiniçõesCDU":
        """Adiciona variável para plotagem automática."""
        self.plotagem.append(DefiniçãoPlotagem(nome, descricao))
        return self

    def serializar(self) -> str:
        """Serializa todas as definições na ordem correta."""
        linhas = []
        
        # DEFVAL
        for defval in self.valores_iniciais:
            linhas.append(defval.serializar())
        
        # DEFVDF
        for defvdf in self.valores_default:
            linhas.append(defvdf.serializar())
        
        # DEFPLT
        for defplt in self.plotagem:
            linhas.append(defplt.serializar())
        
        return "".join(linhas)

# Exemplo de uso em DCDU
if __name__ == "__main__":
    # Exemplo: Regulador de Tensão com CDU
    defs = BlocoDefiniçõesCDU()
    
    # Valores iniciais
    defs.adicionar_valor_inicial("X1", 0.0)
    defs.adicionar_valor_inicial("X2", 1.0)
    
    # Valores default (se não conseguir ler da rede)
    defs.adicionar_valor_default("VBARRA", 1.0)  # tensão padrão
    defs.adicionar_valor_default("PBARRA", 0.5)  # potência padrão
    
    # Variáveis a plotar
    defs.adicionar_plotagem("X1", "Estado integrador")
    defs.adicionar_plotagem("VSAIDA", "Sinal de saída")
    
    print(defs.serializar())
