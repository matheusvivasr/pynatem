"""
cdu_v17.py – Definições e Inicializações de CDU (v1.7).

v1.7.1: DEFVAL, DEFVDF, DEFPLT — Inicialização de Modelos CDU
  Especificação §29.4–29.7 do Manual ANATEM 12.10

DEFVAL (§29.4):
  Declaração de variável e valor inicial de CDU.
  Campos: DEFVAL (stip) (vdef) (d1) (o) (d2)
    stip: subtipo (em branco, VAR, CDU, VOLT, FREQ, ANGL, FLXA, TAP, etc)
    vdef: identificação alfanumérica da variável
    d1: valor/nome/ID conforme stip (em branco→valor numérico ou #PARAM)
    o: exclusão em relatório P2D2 NULL (opcional)
    d2: valor default se localização remota ausente

DEFVDF (§29.5):
  Definição de valor default para saída de bloco INPUT.
  Campos: DEFVDF (nome) (valor)
    nome: identificação alfanumérica do sinal de saída INPUT
    valor: numérico ou #PARAM (used when equipment absent)

DEFPLT (§29.6):
  Declaração de variável para plotagem automática.
  Campos: DEFPLT (var)
    var: identificação alfanumérica da variável a plotar

Inicialização (§29.7):
  Algoritmo em 12 passos para inicializar CDU no início da simulação.
  Passo 1: Tentar inicializar a partir de DEFVAL.
"""

from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class DEFVAL:
    """Declaração de Valor Inicial de Variável CDU (§29.4)."""

    vdef: str  # identificação alfanumérica da variável
    d1: str = ""  # valor/nome/ID conforme stip
    stip: str = ""  # subtipo (vazio=numérico, VAR, CDU, VOLT, FREQ, etc)
    o: bool = False  # exclusão P2D2 NULL
    d2: float = 0.0  # valor default se localização ausente

    def serializar(self) -> str:
        """Serializa em formato ANATEM §29.4."""
        linha = f"DEFVAL"
        if self.stip:
            linha += f" {self.stip:<6}"
        else:
            linha += f" {'':<6}"
        linha += f" {self.vdef:<15}"
        linha += f" {self.d1:<20}"
        if self.o:
            linha += f" O"
        if self.d2 != 0.0:
            linha += f" {self.d2:>15.10f}"
        return linha + "\n"


@dataclass
class DEFVDF:
    """Declaração de Valor Default para INPUT (§29.5)."""

    nome: str  # identificação da saída de bloco INPUT
    valor: float  # valor default (numérico ou #PARAM)

    def serializar(self) -> str:
        """Serializa em formato ANATEM §29.5."""
        return f"DEFVDF {self.nome:<15} {self.valor:>15.10f}\n"


@dataclass
class DEFPLT:
    """Declaração de Variável para Plotagem (§29.6)."""

    var: str  # identificação alfanumérica da variável

    def serializar(self) -> str:
        """Serializa em formato ANATEM §29.6."""
        return f"DEFPLT {self.var:<15}\n"


@dataclass
class InicializacaoCDU:
    """Agregador de definições DEFVAL/DEFVDF/DEFPLT para inicialização CDU (§29.7)."""

    defval_list: List[DEFVAL] = field(default_factory=list)
    defvdf_list: List[DEFVDF] = field(default_factory=list)
    defplt_list: List[DEFPLT] = field(default_factory=list)

    def adicionar_defval(self, vdef: str, d1: str = "", stip: str = "",
                        o: bool = False, d2: float = 0.0) -> "InicializacaoCDU":
        """Adiciona DEFVAL (§29.4)."""
        self.defval_list.append(DEFVAL(vdef=vdef, d1=d1, stip=stip, o=o, d2=d2))
        return self

    def adicionar_defvdf(self, nome: str, valor: float) -> "InicializacaoCDU":
        """Adiciona DEFVDF (§29.5)."""
        self.defvdf_list.append(DEFVDF(nome=nome, valor=valor))
        return self

    def adicionar_defplt(self, var: str) -> "InicializacaoCDU":
        """Adiciona DEFPLT (§29.6)."""
        self.defplt_list.append(DEFPLT(var=var))
        return self

    def serializar(self) -> str:
        """Serializa na ordem correta (DEFVAL → DEFVDF → DEFPLT)."""
        linhas = []
        for defval in self.defval_list:
            linhas.append(defval.serializar())
        for defvdf in self.defvdf_list:
            linhas.append(defvdf.serializar())
        for defplt in self.defplt_list:
            linhas.append(defplt.serializar())
        return "".join(linhas)


if __name__ == "__main__":
    # Exemplo: AVR (Regulador de Tensão) com inicialização
    init = InicializacaoCDU()

    # DEFVAL: valores iniciais de variáveis de estado
    # Tipo 1: valor numérico direto
    init.adicionar_defval("X1", d1="0.0", stip="")  # X1 = 0.0
    init.adicionar_defval("X2", d1="1.0", stip="")  # X2 = 1.0

    # Tipo 2: importar tensão da barra terminal (d1 vazio = barra do equipamento)
    init.adicionar_defval("VTERMO", d1="", stip="VOLT", d2=1.0)  # default 1.0 pu

    # DEFVDF: valores default para INPUT (quando equipamento ausente)
    init.adicionar_defvdf("QINPi", 0.0)  # Reativo default = 0
    init.adicionar_defvdf("STINPi", 1.0)  # Status default = 1

    # DEFPLT: variáveis para plotagem automática
    init.adicionar_defplt("X1")  # Plotar estado X1
    init.adicionar_defplt("VSAIDA")  # Plotar saída

    print(init.serializar())
