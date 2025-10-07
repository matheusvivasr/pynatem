"""
pyanatem/cdu/__init__.py – DSL de Controladores Definidos pelo Usuário (CDU/DCDU).

Cobre todas as etapas 4.4 e 4.5:
  - BlocoCDU: linha genérica de bloco CDU (tipos aritméticos, dinâmicos, lógicos,
    interface, seletores, limitadores, curvas inversas, terminadores)
  - ParametroCDU (DEFPAR)
  - ValorInicialCDU (DEFVAL)
  - ValorDefaultCDU (DEFVDF)
  - ControladorCDU: container de um controlador (ncdu + nome + blocos)
  - BlocoDCDU: bloco completo (múltiplos controladores + 999999)

Referência: Manual ANATEM 12.10, Cap. 29 (blocos_CDU_completo.md)

CONFIANÇA:
  Tipos aritméticos e dinâmicos: Alta (confirmados no manual).
  Tipos lógicos, interface, seletores, limitadores: Alta (confirmados no manual).
  Curvas de tempo inverso (RELINV): best-effort.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional, Union


# ---------------------------------------------------------------------------
# Constantes – todos os tipos de blocos conhecidos
# ---------------------------------------------------------------------------

# Tipos aritméticos
TIPOS_ARITMETICOS = frozenset({
    "SOMA", "MULTPL", "DIVSAO", "GANHO", "FRACAO",
})

# Tipos dinâmicos e limitadores dinâmicos
TIPOS_DINAMICOS = frozenset({
    "ORD1", "LEDLAG", "WSHOUT", "PROINT", "LAGNL",
    "INTRES", "LDLAG2", "PROIN2", "WSHOU2",
    "POLS", "DERIVA", "LIMITA", "RATELM",
    # aliases/variantes mencionados no manual
    "PROIT2", "INTGR", "DERIV",
})

# Lógicos e comparadores
TIPOS_LOGICOS = frozenset({
    "LOGIC", "COMPAR", "MONEST",
    "DISMIN", "DISMAX", "DLAYON", "DLAYOF",
})

# Seletores
TIPOS_SELETORES = frozenset({
    "MAXSEL", "MINSEL", "SWITCH",
})

# Atraso e não-lineares
TIPOS_NAO_LINEARES = frozenset({
    "ATRASO", "NLIMR", "NLIMP", "BORDAI", "LOOKUP",
})

# Curvas de tempo inverso
TIPOS_RELINV = frozenset({
    "RELINV",
})

# Interface com a rede
TIPOS_INTERFACE = frozenset({
    "IMPORT", "EXPORT", "INPUT", "OUTPUT", "SERIET",
})

# Terminadores e constantes
TIPOS_TERMINADORES = frozenset({
    "CONST", "PASO", "SAIDA",
})

TODOS_TIPOS = (
    TIPOS_ARITMETICOS | TIPOS_DINAMICOS | TIPOS_LOGICOS |
    TIPOS_SELETORES | TIPOS_NAO_LINEARES | TIPOS_RELINV |
    TIPOS_INTERFACE | TIPOS_TERMINADORES
)


# ---------------------------------------------------------------------------
# BlocoCDU – linha (ou grupo de linhas) de bloco
# ---------------------------------------------------------------------------

@dataclass
class BlocoCDU:
    """Representa um bloco dentro de um CDU.

    Um bloco corresponde a uma ou mais linhas do arquivo .cdu. O campo
    ``linhas_extras`` armazena linhas adicionais (e.g. entradas extras do
    SOMA/MULTPL, segunda régua do POLS, entradas do INTRES).

    Atributos:
        nb:          número de identificação do bloco.
        tipo:        tipo do bloco (SOMA, LEDLAG, IMPORT, etc.).
        vent:        nome da variável de entrada.
        vsai:        nome da variável de saída.
        init_flag:   True → campo ``i`` = '*' (bloco de inicialização apenas).
        silent_flag: True → campo ``o`` = '*' (sem mensagens no relatório).
        stip:        subtipo do bloco (quando aplicável).
        polaridade:  '-' para polaridade invertida (blocos que admitem).
        p1..p4:      parâmetros numéricos ou nomes de parâmetros (#xxx).
        vmin:        nome da variável de limite inferior.
        vmax:        nome da variável de limite superior.
        linhas_extras: linhas adicionais literais (entradas extras, segunda régua).
    """

    nb: int
    tipo: str
    vent: str = ""
    vsai: str = ""
    init_flag: bool = False
    silent_flag: bool = False
    stip: str = ""
    polaridade: str = ""
    p1: Union[str, float, None] = None
    p2: Union[str, float, None] = None
    p3: Union[str, float, None] = None
    p4: Union[str, float, None] = None
    vmin: str = ""
    vmax: str = ""
    linhas_extras: List[str] = field(default_factory=list)

    def _fmt_param(self, v: Union[str, float, None]) -> str:
        if v is None:
            return ""
        if isinstance(v, float):
            return f"{v:g}"
        return str(v)

    def serializar(self) -> str:
        """Serializa o bloco no formato CDU."""
        i_flag = "*" if self.init_flag else ""
        o_flag = "*" if self.silent_flag else ""
        s_flag = self.polaridade if self.polaridade else ""

        partes = [
            f"{self.nb:>4}",
            f"{i_flag:<1}",
            f"{self.tipo:<6}",
            f"{o_flag:<1}",
            f"{self.stip:<6}" if self.stip else " " * 6,
            f"{s_flag:<1}",
            f"{self.vent:<8}" if self.vent else " " * 8,
            f"{self.vsai:<8}" if self.vsai else " " * 8,
        ]
        params = [
            self._fmt_param(self.p1),
            self._fmt_param(self.p2),
            self._fmt_param(self.p3),
            self._fmt_param(self.p4),
        ]
        params_str = " ".join(f"{p:>8}" for p in params if p != "")
        if params_str:
            partes.append(params_str)
        limites = []
        if self.vmin:
            limites.append(f"{self.vmin:<8}")
        if self.vmax:
            limites.append(f"{self.vmax:<8}")
        if limites:
            partes.append(" ".join(limites))

        linha1 = " ".join(partes).rstrip()
        linhas = [linha1]
        for extra in self.linhas_extras:
            linhas.append(extra.rstrip())
        return "\n".join(linhas)

    def adicionar_entrada(self, vent: str, polaridade: str = "") -> "BlocoCDU":
        """Adiciona linha de entrada extra (SOMA, MULTPL, DIVSAO, INTRES)."""
        s = "-" if polaridade == "-" else ""
        self.linhas_extras.append(f"     {s}{vent:<8}{self.vsai}")
        return self


# ---------------------------------------------------------------------------
# ParametroCDU – DEFPAR
# ---------------------------------------------------------------------------

@dataclass
class ParametroCDU:
    """Define um parâmetro CDU via DEFPAR.

    Args:
        nome:       nome do parâmetro (deve começar por '#').
        valor:      valor numérico ou string do parâmetro.
        comentario: descrição opcional (aparece na linha seguinte).
    """
    nome: str
    valor: Union[float, str]
    comentario: str = ""

    def serializar(self) -> str:
        val = f"{self.valor:g}" if isinstance(self.valor, float) else str(self.valor)
        linha = f"DEFPAR {self.nome} {val}"
        if self.comentario:
            linha += f"\n{self.comentario}"
        return linha


# ---------------------------------------------------------------------------
# ValorInicialCDU – DEFVAL
# ---------------------------------------------------------------------------

@dataclass
class ValorInicialCDU:
    """Define valor inicial de uma variável via DEFVAL.

    Args:
        vdef:      nome da variável a receber o valor inicial.
        d1:        valor numérico, nome de parâmetro ou nome de variável.
        stip:      subtipo (em branco, VAR, CDU, VOLT, etc.).
        silent:    True → campo 'o' preenchido (excluir do P2D2 NULL).
        d2:        valor default quando a localização remota não existe.
    """
    vdef: str
    d1: Union[float, str]
    stip: str = ""
    silent: bool = False
    d2: Optional[Union[float, str]] = None

    def serializar(self) -> str:
        o_flag = "o" if self.silent else ""
        d1_str = f"{self.d1:g}" if isinstance(self.d1, float) else str(self.d1)
        partes = ["DEFVAL"]
        if self.stip:
            partes.append(f"{self.stip:<6}")
        partes.append(f"{self.vdef:<8}")
        partes.append(d1_str)
        if o_flag:
            partes.append(o_flag)
        if self.d2 is not None:
            d2_str = f"{self.d2:g}" if isinstance(self.d2, float) else str(self.d2)
            partes.append(d2_str)
        return " ".join(partes)


# ---------------------------------------------------------------------------
# ValorDefaultCDU – DEFVDF
# ---------------------------------------------------------------------------

@dataclass
class ValorDefaultCDU:
    """Define valor default de uma variável via DEFVDF."""
    vdef: str
    valor: Union[float, str]

    def serializar(self) -> str:
        val = f"{self.valor:g}" if isinstance(self.valor, float) else str(self.valor)
        return f"DEFVDF {self.vdef:<8} {val}"


# ---------------------------------------------------------------------------
# ControladorCDU – um controlador completo (ncdu + nome + conteúdo)
# ---------------------------------------------------------------------------

@dataclass
class ControladorCDU:
    """Container de um controlador CDU.

    Corresponde a uma declaração DCDU ... FIMCDU.

    Args:
        ncdu: número de identificação do CDU.
        nome: nome alfanumérico (ex: 'AVR_USINA_01').
    """
    ncdu: int
    nome: str = ""
    _parametros: List[ParametroCDU] = field(default_factory=list)
    _blocos: List[BlocoCDU] = field(default_factory=list)
    _defvals: List[ValorInicialCDU] = field(default_factory=list)
    _defvdfs: List[ValorDefaultCDU] = field(default_factory=list)

    # ------------------------------------------------------------------
    # API fluente
    # ------------------------------------------------------------------

    def defpar(self, nome: str, valor: Union[float, str],
               comentario: str = "") -> "ControladorCDU":
        """Adiciona parâmetro DEFPAR."""
        self._parametros.append(ParametroCDU(nome=nome, valor=valor, comentario=comentario))
        return self

    def bloco(self, nb: int, tipo: str, vent: str = "", vsai: str = "",
              p1=None, p2=None, p3=None, p4=None,
              vmin: str = "", vmax: str = "",
              stip: str = "", init_flag: bool = False,
              silent_flag: bool = False,
              polaridade: str = "") -> BlocoCDU:
        """Adiciona e retorna um BlocoCDU (permite encadeamento de entradas extras)."""
        b = BlocoCDU(
            nb=nb, tipo=tipo.upper(), vent=vent, vsai=vsai,
            p1=p1, p2=p2, p3=p3, p4=p4,
            vmin=vmin, vmax=vmax,
            stip=stip, init_flag=init_flag,
            silent_flag=silent_flag, polaridade=polaridade,
        )
        self._blocos.append(b)
        return b

    def defval(self, vdef: str, d1: Union[float, str],
               stip: str = "", silent: bool = False,
               d2: Optional[Union[float, str]] = None) -> "ControladorCDU":
        """Adiciona DEFVAL."""
        self._defvals.append(ValorInicialCDU(vdef=vdef, d1=d1, stip=stip,
                                              silent=silent, d2=d2))
        return self

    def defvdf(self, vdef: str, valor: Union[float, str]) -> "ControladorCDU":
        """Adiciona DEFVDF."""
        self._defvdfs.append(ValorDefaultCDU(vdef=vdef, valor=valor))
        return self

    def serializar(self) -> str:
        linhas: List[str] = []
        # identificação
        linhas.append(f"{self.ncdu} {self.nome}".strip())
        linhas.append("(nb)i(tipo)o(stip)s(vent)    (vsai)   ( p1 )( p2 )( p3 )( p4 ) (vmin) (vmax)")
        for p in self._parametros:
            linhas.append(p.serializar())
        for b in self._blocos:
            linhas.append(b.serializar())
        for dv in self._defvdfs:
            linhas.append(dv.serializar())
        for dv in self._defvals:
            linhas.append(dv.serializar())
        linhas.append("FIMCDU")
        return "\n".join(linhas)

    def __repr__(self) -> str:
        return (f"ControladorCDU(ncdu={self.ncdu}, nome={self.nome!r}, "
                f"blocos={len(self._blocos)}, defvals={len(self._defvals)})")


# ---------------------------------------------------------------------------
# BlocoDCDU – bloco DCDU completo (múltiplos controladores)
# ---------------------------------------------------------------------------

@dataclass
class BlocoDCDU:
    """Bloco DCDU completo (código de execução do ANATEM).

    Contém múltiplos ControladorCDU, serializa com DCDU ... 999999.

    Uso::

        dcdu = BlocoDCDU()

        avr = dcdu.novo_controlador(ncdu=100, nome="AVR_G1")
        avr.defpar("#Vref", 1.0, "Tensão de referência [pu]")
        avr.bloco(10, "IMPORT", stip="VOLT", vsai="Vt")
        avr.bloco(20, "SOMA",   vent="Vref", vsai="Erro")
        avr.bloco(20, "SOMA",   vent="Vt",   vsai="Erro", polaridade="-")
        avr.bloco(30, "LEDLAG", vent="Erro", vsai="Efd",
                  p1=200.0, p2=0.0, p3=1.0, p4=0.05,
                  vmin="Emin", vmax="Emax")
        avr.bloco(40, "EXPORT", stip="EFD",  vent="Efd")
        avr.defval("Vref",  1.0)
        avr.defval("Emin", -5.0)
        avr.defval("Emax",  5.0)

    """

    keyword: str = field(default="DCDU", init=False, repr=False)
    _controladores: List[ControladorCDU] = field(default_factory=list)

    def tem_dados(self) -> bool:
        return bool(self._controladores)

    def novo_controlador(self, ncdu: int, nome: str = "") -> ControladorCDU:
        """Cria e registra um novo ControladorCDU."""
        ctrl = ControladorCDU(ncdu=ncdu, nome=nome)
        self._controladores.append(ctrl)
        return ctrl

    def adicionar(self, ctrl: ControladorCDU) -> "BlocoDCDU":
        """Adiciona um ControladorCDU já construído."""
        self._controladores.append(ctrl)
        return self

    def serializar(self) -> str:
        if not self._controladores:
            return ""
        linhas: List[str] = ["DCDU"]
        linhas.append("(ncdu) ( nome cdu )")
        for ctrl in self._controladores:
            linhas.append(ctrl.serializar())
            linhas.append("(")
        linhas.append("999999")
        return "\n".join(linhas)

    def __repr__(self) -> str:
        return f"BlocoDCDU(controladores={len(self._controladores)})"


# ---------------------------------------------------------------------------
# Parser básico de blocos CDU (leitura de DCDU ... 999999)
# ---------------------------------------------------------------------------

def _safe_float_cdu(s: str) -> float:
    try:
        return float(s)
    except (ValueError, TypeError):
        return 0.0


def _parse_param(s: str) -> Union[str, float]:
    """Tenta converter para float; se não conseguir, retorna string."""
    try:
        return float(s)
    except (ValueError, TypeError):
        return s


def parsear_dcdu(linhas: List[str], inicio: int) -> tuple:
    """Lê um bloco DCDU a partir da linha ``inicio`` (linha 'DCDU').

    Returns:
        (BlocoDCDU, proximo_indice)
    """
    dcdu = BlocoDCDU()
    i = inicio + 1  # pula 'DCDU'

    while i < len(linhas):
        linha = linhas[i].rstrip()
        stripped = linha.strip()

        # Fim do bloco DCDU
        if stripped.startswith("999999"):
            return dcdu, i + 1

        # Comentário
        if stripped.startswith("(") or not stripped:
            i += 1
            continue

        # Início de novo controlador: linha com ncdu + nome
        # Formato: "<ncdu> <nome>" onde ncdu é inteiro
        partes = stripped.split(None, 1)
        try:
            ncdu = int(partes[0])
        except (ValueError, IndexError):
            i += 1
            continue

        nome = partes[1].strip() if len(partes) > 1 else ""
        ctrl = ControladorCDU(ncdu=ncdu, nome=nome)
        i += 1

        # Lê o conteúdo do controlador até FIMCDU
        i = _parsear_controlador(linhas, i, ctrl)
        dcdu._controladores.append(ctrl)

    return dcdu, i


def _parsear_controlador(linhas: List[str], inicio: int,
                          ctrl: ControladorCDU) -> int:
    i = inicio
    while i < len(linhas):
        linha = linhas[i].rstrip()
        stripped = linha.strip()

        if stripped.upper() == "FIMCDU":
            return i + 1

        if stripped.startswith("999999"):
            return i  # deixa o pai consumir

        if stripped.startswith("(") or not stripped:
            i += 1
            continue

        partes = stripped.split()
        kw = partes[0].upper()

        if kw == "DEFPAR":
            nome = partes[1] if len(partes) > 1 else ""
            val_str = partes[2] if len(partes) > 2 else "0"
            ctrl._parametros.append(ParametroCDU(nome=nome, valor=_parse_param(val_str)))
            i += 1
            continue

        if kw == "DEFVAL":
            # DEFVAL [stip] vdef d1 [o] [d2]
            # stip pode ser omitido (começa por letra, não por '#' nem '-')
            # vdef começa por letra
            idx = 1
            stip = ""
            if idx < len(partes):
                candidate = partes[idx].upper()
                # se não é vdef (vdef segue, é nome de variável)
                # heurística: stip vai de VAR, CDU, VOLT, etc.
                if candidate in ("VAR", "CDU", "VOLT", "STGER", "STBAR", "EFD",
                                  "VTR", "WMAQ", "PMEC", "PGER"):
                    stip = partes[idx]
                    idx += 1
            vdef = partes[idx] if idx < len(partes) else ""
            idx += 1
            d1_str = partes[idx] if idx < len(partes) else "0"
            d1 = _parse_param(d1_str)
            ctrl._defvals.append(ValorInicialCDU(vdef=vdef, d1=d1, stip=stip))
            i += 1
            continue

        if kw == "DEFVDF":
            vdef = partes[1] if len(partes) > 1 else ""
            val_str = partes[2] if len(partes) > 2 else "0"
            ctrl._defvdfs.append(ValorDefaultCDU(vdef=vdef, valor=_parse_param(val_str)))
            i += 1
            continue

        # Linha de bloco: começa com número (nb)
        try:
            nb = int(partes[0])
        except ValueError:
            # Linha extra de bloco anterior (entradas SOMA, etc.)
            if ctrl._blocos:
                ctrl._blocos[-1].linhas_extras.append(linha)
            i += 1
            continue

        # Parse da linha de bloco
        # Formato posicional:
        # nb [i] tipo [o] [stip] [s] vent vsai [p1 p2 p3 p4] [vmin vmax]
        idx = 1
        init_flag = False
        if idx < len(partes) and partes[idx] == "*":
            init_flag = True
            idx += 1

        tipo = partes[idx].upper() if idx < len(partes) else ""
        idx += 1

        silent_flag = False
        if idx < len(partes) and partes[idx] == "*":
            silent_flag = True
            idx += 1

        stip = ""
        polaridade = ""

        # stip: campo alfanumérico que não é variável (não começa por letra pura)
        # Heurística simples: se o próximo token está nos conjuntos de stip conhecidos
        if idx < len(partes):
            candidate = partes[idx].upper()
            if candidate in ("VOLT", "VTR", "EFD", "WMAQ", "PMEC", "PGER",
                              ".AND.", ".OR.", ".NOT.", ".XOR.", "IEC", "IEEE"):
                stip = partes[idx]
                idx += 1

        # polaridade
        if idx < len(partes) and partes[idx] == "-":
            polaridade = "-"
            idx += 1

        vent = partes[idx] if idx < len(partes) else ""
        idx += 1
        vsai = partes[idx] if idx < len(partes) else ""
        idx += 1

        p1 = _parse_param(partes[idx]) if idx < len(partes) else None
        idx += 1
        p2 = _parse_param(partes[idx]) if idx < len(partes) else None
        idx += 1
        p3 = _parse_param(partes[idx]) if idx < len(partes) else None
        idx += 1
        p4 = _parse_param(partes[idx]) if idx < len(partes) else None
        idx += 1
        vmin = partes[idx] if idx < len(partes) else ""
        idx += 1
        vmax = partes[idx] if idx < len(partes) else ""

        b = BlocoCDU(
            nb=nb, tipo=tipo, vent=vent, vsai=vsai,
            p1=p1, p2=p2, p3=p3, p4=p4,
            vmin=vmin, vmax=vmax,
            stip=stip, init_flag=init_flag,
            silent_flag=silent_flag, polaridade=polaridade,
        )
        ctrl._blocos.append(b)
        i += 1

    return i
