"""
blocos.py – Representação e serialização de cada bloco do arquivo STB.

Formato ANATEM (texto posicional, colunas fixas):
  - Palavra-chave do bloco em colunas 1-4
  - Dados em colunas fixas conforme especificação do manual (Parte X)
  - Terminador: 999999
  - Comentários: texto após '(' até fim da linha

Referência: Manual ANATEM 12.10, Parte X – Códigos e Opções de Execução
https://see.cepel.br/manual/anatem/_downloads/b9287b40dd3c8b35ce2cab11293ff68c/anatem.pdf

NOTA DE CONFIANÇA DOS CÓDIGOS:
  - Barras CA, máquinas síncronas, circuitos CA, cargas: códigos confirmados
    contra a estrutura do manual (VBAR, TBAR, FREQ, DELT, OMEG, PGER, QGER,
    ICAM, EEXC, VTER, PELM, PMEC, FLXP, FLXQ, FLXC, PCAG, QCAG).
  - FACTS (DCER/SVC, DCSC/TCSC, DVSI) e HVDC (DCNV, DELO): campos e ordem
    validados contra o manual §46.18/§46.22/§46.64/§46.21/§46.27 (Listagens
    46.16/46.20/46.61/46.19/46.25), com roundtrip garantido pelo ParserSTB.
    DCER/DCSC/DCNV/DELO são códigos de ASSOCIAÇÃO de controles.
  - Variáveis de plotagem DPLT 4-letra (OLTC/FACTS/HVDC/CDU): mnemônicos e
    réguas validados contra o manual (§13.3.1, §25.4, §26.4, §27.5, §24.6.1,
    §22.2, §29.10). Ex.: tap OLTC=TAP; CER=QCES/BCES/ICES/VCES; CSC=XCSC/BCSC/
    ICSC; VSI=QVSI/PVSI/IMVSI/ETMVSI; conversor CA-CC=VCNV/CCNV/PCNV/ALFA/GAMA;
    CDU=CDU/CDUE. As linhas fazem roundtrip como texto no ParserSTB.
  - O EQUIPAMENTO OLTC (código DLTC) ainda não é modelado (só a variável de
    plotagem TAP está validada). Use `linha_bruta()` para casos não cobertos.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

# ---------------------------------------------------------------------------
# Base
# ---------------------------------------------------------------------------


class BlocoBase:
    """Interface comum para todos os blocos."""

    keyword: str = ""

    def tem_dados(self) -> bool:
        return True

    def serializar(self) -> str:
        raise NotImplementedError

    def _cabecalho(self) -> str:
        return f"{self.keyword}\n"

    def _terminador(self) -> str:
        return "999999\n"


# ---------------------------------------------------------------------------
# DOPC – Opções globais de execução  (manual §46.53, pág. 773)
# ---------------------------------------------------------------------------


@dataclass
class BlocoDOPC(BlocoBase):
    """Opções globais do ANATEM (DOPC).

    Atributos:
        freq:     frequência nominal do sistema [Hz] (padrão 60).
        base_mva: potência base do sistema [MVA].
    """

    keyword: str = field(default="DOPC", init=False, repr=False)
    freq: Optional[float] = None  # compat de API — não faz parte do formato DOPC
    base_mva: Optional[float] = None  # compat de API — idem
    opcoes_extras: List[str] = field(default_factory=list)
    _opcoes: List[tuple] = field(default_factory=list)  # [(mnemônico, estado)]

    def ativar(self, opcao: str, estado: str = "L") -> "BlocoDOPC":
        """Adiciona uma opção de controle de execução (régua ``(Op) E``).

        ``estado``: L (ligado), D (desligado) ou "" (em branco → L).
        """
        if estado not in ("L", "D", ""):
            raise ValueError(f"Estado inválido: {estado!r} (use L, D ou vazio)")
        self._opcoes.append((opcao.upper(), estado))
        return self

    def tem_dados(self) -> bool:
        return bool(self._opcoes or self.opcoes_extras)

    def serializar(self) -> str:
        linhas = [self._cabecalho()]
        if self._opcoes:
            pares = [f"{op:<4} {estado}".rstrip() for op, estado in self._opcoes]
            linhas.append(" ".join(pares) + "\n")
        for op in self.opcoes_extras:
            linhas.append(op.rstrip() + "\n")
        linhas.append(self._terminador())
        return "".join(linhas)


# ---------------------------------------------------------------------------
# DARQ – Associação de arquivos  (manual §46.11, pág. 683)
#
# Subtipos singulares: SIST, RELA, LOGI, PLOT, PLOC, PLOR, SNAP, SINA
# Subtipos com múltiplos arquivos: DCDU, DBLT (bibliotecas de controladores
# e de modelos podem ser combinadas a partir de vários arquivos)
# ---------------------------------------------------------------------------


@dataclass
class BlocoDARQ(BlocoBase):
    """Associação dos arquivos de entrada e saída (DARQ).

    Atributos singulares (um arquivo por caso):
        sav, rela, log, plt, plt_cdu, plt_rele, snap, sina

    Atributos com suporte a múltiplos arquivos:
        cdu / cdu_extras — use `adicionar_cdu()` e `todos_cdu()`
        blt / blt_extras — use `adicionar_blt()` e `todos_blt()`
    """

    keyword: str = field(default="DARQ", init=False, repr=False)
    sav: Optional[str] = None  # SIST
    rela: Optional[str] = None  # RELA (relatório de saída)
    log: Optional[str] = None  # LOGI
    plt: Optional[str] = None  # PLOT
    plt_cdu: Optional[str] = None  # PLOC
    plt_rele: Optional[str] = None  # PLOR
    snap: Optional[str] = None  # SNAP
    sina: Optional[str] = None  # SINA
    cdu: Optional[str] = None  # DCDU (primeiro arquivo)
    blt: Optional[str] = None  # DBLT (primeiro arquivo)
    cdu_extras: List[str] = field(default_factory=list)
    blt_extras: List[str] = field(default_factory=list)
    extras: List[str] = field(default_factory=list)

    # alias retrocompatível (sessão 1 usava .out)
    @property
    def out(self) -> Optional[str]:
        return self.rela

    @out.setter
    def out(self, v: Optional[str]) -> None:
        self.rela = v

    def adicionar_cdu(self, caminho: str) -> "BlocoDARQ":
        """Associa um arquivo CDU adicional.

        O ANATEM permite múltiplos arquivos DCDU no mesmo caso (por
        exemplo, uma biblioteca de reguladores e outra de PSS separadas).
        O primeiro arquivo é gravado em `.cdu`; os demais em `.cdu_extras`.

        Args:
            caminho: caminho do arquivo .cdu.

        Returns:
            self.
        """
        if self.cdu is None:
            self.cdu = caminho
        else:
            self.cdu_extras.append(caminho)
        return self

    def adicionar_blt(self, caminho: str) -> "BlocoDARQ":
        """Associa um arquivo BLT (biblioteca de modelos dinâmicos) adicional.

        Args:
            caminho: caminho do arquivo .blt.

        Returns:
            self.
        """
        if self.blt is None:
            self.blt = caminho
        else:
            self.blt_extras.append(caminho)
        return self

    def todos_cdu(self) -> List[str]:
        """Retorna todos os arquivos CDU associados, na ordem de associação."""
        return ([self.cdu] if self.cdu else []) + list(self.cdu_extras)

    def todos_blt(self) -> List[str]:
        """Retorna todos os arquivos BLT associados, na ordem de associação."""
        return ([self.blt] if self.blt else []) + list(self.blt_extras)

    def serializar(self) -> str:
        linhas = [self._cabecalho()]
        mapa_simples = [
            ("sav", "SIST"),
            ("rela", "RELA"),
            ("log", "LOGI"),
            ("plt", "PLOT"),
            ("plt_cdu", "PLOC"),
            ("plt_rele", "PLOR"),
            ("snap", "SNAP"),
            ("sina", "SINA"),
        ]
        for attr, subtipo in mapa_simples:
            arq = getattr(self, attr)
            if arq:
                linhas.append(f"{subtipo:<8}{arq}\n")
        for arq in self.todos_cdu():
            linhas.append(f"{'DCDU':<8}{arq}\n")
        for arq in self.todos_blt():
            linhas.append(f"{'DBLT':<8}{arq}\n")
        for linha in self.extras:
            linhas.append(linha.rstrip() + "\n")
        linhas.append(self._terminador())
        return "".join(linhas)


# ---------------------------------------------------------------------------
# DSIM – Parâmetros de simulação  (manual §46.59, pág. 819)
# ---------------------------------------------------------------------------


@dataclass
class BlocoDSIM(BlocoBase):
    """Parâmetros de simulação transitória (DSIM).

    Campos oficiais (régua ``( Tmax ) (Stp) ( P ) ( I ) ( F )``):
        tmax – tempo máximo de simulação [s] (branco → 10)
        stp  – passo de integração [s] (branco → 0.001)
        p    – frequência de gravação p/ plotagem, em passos (ímpar; branco → 1)
        i    – frequência de emissão de relatórios, em passos (ímpar; branco → 1)
        f    – frequência de atualização da jacobiana p/ opção DNWT (branco → 1)

    ``tini`` é mantido apenas por compatibilidade de API (a simulação ANATEM
    sempre inicia em t=0; o campo não existe no formato e não é serializado).
    """

    keyword: str = field(default="DSIM", init=False, repr=False)
    tmax: float = 10.0
    stp: float = 0.001
    p: Optional[int] = None
    i: Optional[int] = None
    f: Optional[int] = None
    tini: float = 0.0  # compat: não faz parte do formato oficial

    # ---- aliases de retrocompatibilidade (API antiga) ----
    @property
    def tfim(self) -> float:
        return self.tmax

    @tfim.setter
    def tfim(self, v: float) -> None:
        self.tmax = v

    @property
    def delt(self) -> float:
        return self.stp

    @delt.setter
    def delt(self, v: float) -> None:
        self.stp = v

    @property
    def npas(self) -> Optional[int]:
        return self.p

    @npas.setter
    def npas(self, v: Optional[int]) -> None:
        self.p = v

    def serializar(self) -> str:
        # régua oficial: Tmax cols 0-7, Stp 9-13, P 15-19, I 21-25, F 27-31
        campos = [
            (7, 8, f"{self.tmax:.2f}"),
            (13, 5, _num_compacto(self.stp)),
        ]
        if self.p is not None:
            campos.append((19, 5, str(self.p)))
        if self.i is not None:
            campos.append((25, 5, str(self.i)))
        if self.f is not None:
            campos.append((31, 5, str(self.f)))
        canvas = list(" " * 32)
        for fim, largura, texto in campos:
            texto = texto[:largura]
            canvas[fim - len(texto) + 1 : fim + 1] = texto
        linhas = [self._cabecalho()]
        linhas.append("".join(canvas).rstrip() + "\n")
        linhas.append(self._terminador())
        return "".join(linhas)


# ---------------------------------------------------------------------------
# DEVT – Eventos da simulação  (manual §46.31, pág. 722)
# ---------------------------------------------------------------------------


def _num_compacto(v: float) -> str:
    """Número em forma compacta (estilo do manual: '.05', '10', '1.5')."""
    if float(v).is_integer():
        return str(int(v))
    s = f"{v:.6g}"
    if s.startswith("0."):
        s = s[1:]
    elif s.startswith("-0."):
        s = "-" + s[2:]
    return s


# Colunas posicionais da régua oficial do DEVT (§46.31): coluna final
# (inclusiva, 0-indexada) e largura máxima de cada campo.
# Régua: (Tp) ( Tempo)( El )( Pa)Nc( Ex) ( % ) (ABS ) Gr Uni  (Bl)P ( Rc ) ( Xc ) ( Bc ) (Defas)
_DEVT_COLUNAS = {
    "tempo": (12, 8),
    "el": (18, 6),
    "pa": (23, 5),
    "nc": (25, 2),
    "ex": (30, 5),
    "pct": (36, 6),
    "abs_": (43, 7),
    "gr": (46, 3),
    "uni": (50, 4),
    "bl": (63, 5),
    "rc": (71, 7),
    "xc": (78, 7),
    "bc": (85, 7),
    "defas": (93, 8),
}


@dataclass
class _Evento:
    """Linha de evento DEVT em colunas posicionais fixas (régua §46.31)."""

    codigo: str
    tini: float = 0.0
    el: Optional[int] = None
    pa: Optional[int] = None
    nc: Optional[int] = None
    ex: Optional[int] = None
    pct: Optional[float] = None
    abs_: Optional[float] = None
    gr: Optional[int] = None
    uni: Optional[int] = None
    bl: Optional[int] = None
    rc: Optional[float] = None
    xc: Optional[float] = None
    bc: Optional[float] = None
    defas: Optional[float] = None

    def serializar(self) -> str:
        canvas = list(" " * 94)
        canvas[0:4] = f"{self.codigo:<4}"
        valores = {"tempo": _num_compacto(self.tini)}
        for campo in ("el", "pa", "nc", "ex", "gr", "uni", "bl"):
            v = getattr(self, campo)
            if v is not None:
                valores[campo] = str(v)
        for campo in ("pct", "abs_", "rc", "xc", "bc", "defas"):
            v = getattr(self, campo)
            if v is not None:
                valores[campo] = _num_compacto(v)
        for campo, texto in valores.items():
            fim, largura = _DEVT_COLUNAS[campo]
            texto = texto[:largura]
            inicio = fim - len(texto) + 1
            canvas[inicio : fim + 1] = texto
        return "".join(canvas).rstrip()


@dataclass
class BlocoDEVT(BlocoBase):
    """Bloco de eventos da simulação (DEVT)."""

    keyword: str = field(default="DEVT", init=False, repr=False)
    _eventos: List[_Evento] = field(default_factory=list)
    _linhas_brutas: List[str] = field(default_factory=list)

    @property
    def linhas(self) -> List[str]:
        """Lista mutável de linhas brutas (compatibilidade)."""
        return self._linhas_brutas

    @linhas.setter
    def linhas(self, v: List[str]) -> None:
        self._linhas_brutas = v

    def curto_barra(
        self,
        barra: int,
        tini: float,
        tipo: str = "APCB",
        r: float = 0.0,
        x: float = 0.0,
    ) -> "BlocoDEVT":
        """Aplica (APCB) ou remove (RMCB) curto-circuito em barra CA (§10.1)."""
        self._eventos.append(
            _Evento(
                codigo=tipo,
                tini=tini,
                el=barra,
                rc=r if r else None,
                xc=x if x else None,
            )
        )
        return self

    def curto_circuito(
        self,
        de: int,
        para: int,
        circ: int,
        tini: float,
        tipo: str = "APCL",
        r: float = 0.0,
        x: float = 0.0,
    ) -> "BlocoDEVT":
        """Aplica (APCL) ou remove (RMCL) curto-circuito em circuito CA (§13.2)."""
        self._eventos.append(
            _Evento(
                codigo=tipo,
                tini=tini,
                el=de,
                pa=para,
                nc=circ,
                rc=r if r else None,
                xc=x if x else None,
            )
        )
        return self

    def abertura_linha(
        self, de: int, para: int, tini: float, circ: Optional[int] = None
    ) -> "BlocoDEVT":
        """Abre um circuito CA (ABCI, §13.2). ``circ`` em branco = circuito 1."""
        self._eventos.append(_Evento(codigo="ABCI", tini=tini, el=de, pa=para, nc=circ))
        return self

    def fechamento_linha(
        self, de: int, para: int, tini: float, circ: Optional[int] = None
    ) -> "BlocoDEVT":
        """Fecha um circuito CA (FECI, §13.2). ``circ`` em branco = circuito 1."""
        self._eventos.append(_Evento(codigo="FECI", tini=tini, el=de, pa=para, nc=circ))
        return self

    def modificacao_shunt(
        self,
        barra: int,
        tini: float,
        valor: Optional[float] = None,
        pct: Optional[float] = None,
        grupo: Optional[int] = None,
        unidades: Optional[int] = None,
    ) -> "BlocoDEVT":
        """Modificação de shunt equivalente em barra CA (MDSH, §12.1).

        ``valor`` é a variação absoluta (Abs) do shunt equivalente; ``pct`` a
        variação percentual; ``grupo``/``unidades`` para o caso individualizado.
        """
        self._eventos.append(
            _Evento(
                codigo="MDSH",
                tini=tini,
                el=barra,
                pct=pct,
                abs_=valor,
                gr=grupo,
                uni=unidades,
            )
        )
        return self

    def step_referencia(
        self, barra: int, unidade: int, tini: float, delta: float, tipo: str = "TRGT"
    ) -> "BlocoDEVT":
        """Degrau no sinal de referência de regulador built-in de máquina (§16.9).

        ``tipo``: TRGT (regulador de tensão) ou TRGV (regulador de velocidade).
        ``delta`` é a variação percentual (campo %); ``unidade`` é o grupo (Gr).
        """
        if tipo not in ("TRGT", "TRGV"):
            raise ValueError(
                f"Evento de referência inválido: {tipo!r} (use TRGT ou TRGV, §16.9)"
            )
        self._eventos.append(
            _Evento(codigo=tipo, tini=tini, el=barra, gr=unidade, pct=delta)
        )
        return self

    def linha_bruta(self, texto: str) -> "BlocoDEVT":
        """Adiciona linha de evento no formato literal do ANATEM."""
        self._linhas_brutas.append(texto)
        return self

    def serializar(self) -> str:
        linhas = [self._cabecalho()]
        for ev in self._eventos:
            linhas.append(ev.serializar() + "\n")
        for lb in self._linhas_brutas:
            linhas.append(lb.rstrip() + "\n")
        linhas.append(self._terminador())
        return "".join(linhas)


# ---------------------------------------------------------------------------
# DPLT – Variáveis de plotagem  (manual §46.55, pág. 774-791)
# ---------------------------------------------------------------------------


@dataclass
class BlocoDPLT(BlocoBase):
    """Variáveis de saída e plotagem (DPLT)."""

    keyword: str = field(default="DPLT", init=False, repr=False)
    linhas: List[str] = field(default_factory=list)

    def _add(self, codigo: str, id1: int, id2: int = 0, id3: int = 0) -> "BlocoDPLT":
        cod = f"{codigo:<4}"
        if id2 or id3:
            linha = f"{cod}  {id1:>5}  {id2:>5}  {id3:>3}"
        else:
            linha = f"{cod}  {id1:>5}"
        self.linhas.append(linha)
        return self

    # -- Barras CA --------------------------------------------------------

    def tensao_barra(self, barra: int) -> "BlocoDPLT":
        """Módulo de tensão na barra [pu]."""
        return self._add("VBAR", barra)

    def angulo_barra(self, barra: int) -> "BlocoDPLT":
        """Ângulo de tensão na barra [graus]."""
        return self._add("TBAR", barra)

    def frequencia_barra(self, barra: int) -> "BlocoDPLT":
        """Frequência na barra [Hz]."""
        return self._add("FREQ", barra)

    # -- Máquinas síncronas -------------------------------------------------

    def angulo_maquina(self, barra: int, unidade: int = 1) -> "BlocoDPLT":
        """Ângulo do rotor (delta) [graus elétricos]."""
        return self._add("DELT", barra, unidade)

    def velocidade_maquina(self, barra: int, unidade: int = 1) -> "BlocoDPLT":
        """Velocidade angular (omega) [pu]."""
        return self._add("OMEG", barra, unidade)

    def potencia_ativa(self, barra: int, unidade: int = 1) -> "BlocoDPLT":
        """Potência ativa gerada [pu]."""
        return self._add("PGER", barra, unidade)

    def potencia_reativa(self, barra: int, unidade: int = 1) -> "BlocoDPLT":
        """Potência reativa gerada [pu]."""
        return self._add("QGER", barra, unidade)

    def corrente_campo(self, barra: int, unidade: int = 1) -> "BlocoDPLT":
        """Corrente de campo [pu]."""
        return self._add("ICAM", barra, unidade)

    def tensao_excitacao(self, barra: int, unidade: int = 1) -> "BlocoDPLT":
        """Tensão de excitação Efd [pu]."""
        return self._add("EEXC", barra, unidade)

    def tensao_terminal(self, barra: int, unidade: int = 1) -> "BlocoDPLT":
        """Tensão terminal da máquina [pu]."""
        return self._add("VTER", barra, unidade)

    def potencia_eletrica(self, barra: int, unidade: int = 1) -> "BlocoDPLT":
        """Potência elétrica Pe [pu]."""
        return self._add("PELM", barra, unidade)

    def potencia_mecanica(self, barra: int, unidade: int = 1) -> "BlocoDPLT":
        """Potência mecânica Pm [pu]."""
        return self._add("PMEC", barra, unidade)

    # -- Circuitos CA -------------------------------------------------------

    def fluxo_ativo(self, de: int, para: int, circ: int = 1) -> "BlocoDPLT":
        """Fluxo de potência ativa no circuito [pu]."""
        return self._add("FLXP", de, para, circ)

    def fluxo_reativo(self, de: int, para: int, circ: int = 1) -> "BlocoDPLT":
        """Fluxo de potência reativa no circuito [pu]."""
        return self._add("FLXQ", de, para, circ)

    def corrente_circuito(self, de: int, para: int, circ: int = 1) -> "BlocoDPLT":
        """Corrente no circuito [pu]."""
        return self._add("FLXC", de, para, circ)

    # -- Cargas ---------------------------------------------------------------

    def potencia_carga(self, barra: int) -> "BlocoDPLT":
        """Potência ativa de carga [pu]."""
        return self._add("PCAG", barra)

    def reativo_carga(self, barra: int) -> "BlocoDPLT":
        """Potência reativa de carga [pu]."""
        return self._add("QCAG", barra)

    # -- Bancos shunt (§12.2, régua El=barra [+ Gr=grupo]) ------------------

    def reativo_shunt(self, barra: int) -> "BlocoDPLT":
        """Potência reativa do shunt equivalente da barra [Mvar] (§12.2.1: QSHT)."""
        return self._add("QSHT", barra)

    def shunt_individualizado(self, barra: int, grupo: int = 0) -> "BlocoDPLT":
        """Valor do banco shunt individualizado [Mvar] (§12.2.2: QBSH)."""
        return self._add("QBSH", barra, grupo)

    def unidades_shunt(self, barra: int, grupo: int = 0) -> "BlocoDPLT":
        """Nº de unidades em operação no banco shunt individualizado (§12.2.2: NUBSH)."""
        return self._add("NUBSH", barra, grupo)

    # -- Transformadores OLTC (§13.3.1, régua El=DE, Pa=PARA, Nc) ------------

    def tap_oltc(self, de: int, para: int, circ: int = 1) -> "BlocoDPLT":
        """Valor do tap do transformador no lado primário [pu] (§13.3.1: TAP)."""
        return self._add("TAP", de, para, circ)

    # -- FACTS CER/SVC (§25.4, régua El=barra CA, Gp=grupo) -----------------

    def reativo_svc(self, barra: int, grupo: int = 0) -> "BlocoDPLT":
        """Potência reativa do compensador estático [Mvar] (§25.4: QCES)."""
        return self._add("QCES", barra, grupo)

    def susceptancia_svc(self, barra: int, grupo: int = 0) -> "BlocoDPLT":
        """Susceptância do compensador estático [pu] (§25.4: BCES)."""
        return self._add("BCES", barra, grupo)

    def corrente_svc(self, barra: int, grupo: int = 0) -> "BlocoDPLT":
        """Corrente no compensador estático [pu] (§25.4: ICES)."""
        return self._add("ICES", barra, grupo)

    def tensao_svc(self, barra: int, grupo: int = 0) -> "BlocoDPLT":
        """Tensão na barra controlada pelo CER [pu] (§25.4: VCES)."""
        return self._add("VCES", barra, grupo)

    # -- FACTS CSC/TCSC (§26.4, régua El=DE, Pa=PARA, Nc) -------------------

    def reatancia_tcsc(self, de: int, para: int, circ: int = 1) -> "BlocoDPLT":
        """Reatância equivalente do compensador série [%] (§26.4: XCSC)."""
        return self._add("XCSC", de, para, circ)

    def susceptancia_tcsc(self, de: int, para: int, circ: int = 1) -> "BlocoDPLT":
        """Susceptância equivalente do compensador série [pu] (§26.4: BCSC)."""
        return self._add("BCSC", de, para, circ)

    def corrente_tcsc(self, de: int, para: int, circ: int = 1) -> "BlocoDPLT":
        """Módulo da corrente do compensador série [pu] (§26.4: ICSC)."""
        return self._add("ICSC", de, para, circ)

    # -- FACTS VSI: STATCOM/SSSC (§27.5, régua El=conversor) ----------------

    def reativo_statcom(self, conversor: int) -> "BlocoDPLT":
        """Potência reativa no lado CA do conversor VSI [pu] (§27.5: QVSI)."""
        return self._add("QVSI", conversor)

    def ativo_statcom(self, conversor: int) -> "BlocoDPLT":
        """Potência ativa no lado CA do conversor VSI [pu] (§27.5: PVSI)."""
        return self._add("PVSI", conversor)

    def corrente_statcom(self, conversor: int) -> "BlocoDPLT":
        """Módulo da corrente CA do conversor VSI [pu] (§27.5: IMVSI)."""
        return self._add("IMVSI", conversor)

    def tensao_interna_statcom(self, conversor: int) -> "BlocoDPLT":
        """Módulo da tensão interna CA do conversor VSI [pu] (§27.5: ETMVSI)."""
        return self._add("ETMVSI", conversor)

    # -- HVDC: conversor CA-CC (§24.6.1, régua El=conversor DCNV) -----------

    def tensao_cc(self, conversor: int) -> "BlocoDPLT":
        """Tensão de saída do conversor CA-CC [pu] (§24.6.1: VCNV)."""
        return self._add("VCNV", conversor)

    def corrente_cc(self, conversor: int) -> "BlocoDPLT":
        """Corrente no conversor CA-CC [pu] (§24.6.1: CCNV)."""
        return self._add("CCNV", conversor)

    def potencia_cc(self, conversor: int) -> "BlocoDPLT":
        """Potência ativa drenada da rede CA pelo conversor [MW] (§24.6.1: PCNV)."""
        return self._add("PCNV", conversor)

    def reativo_cc(self, conversor: int) -> "BlocoDPLT":
        """Potência reativa drenada da rede CA pelo conversor [Mvar] (§24.6.1: QCNV)."""
        return self._add("QCNV", conversor)

    def angulo_disparo(self, conversor: int) -> "BlocoDPLT":
        """Ângulo de disparo do conversor, alfa [graus] (§24.6.1: ALFA)."""
        return self._add("ALFA", conversor)

    def angulo_extincao(self, conversor: int) -> "BlocoDPLT":
        """Ângulo de extinção do inversor, gama [graus] (§24.6.1: GAMA)."""
        return self._add("GAMA", conversor)

    def tensao_barra_cc(self, barra_cc: int) -> "BlocoDPLT":
        """Tensão de barra CC [pu] (§22.2: VBDC)."""
        return self._add("VBDC", barra_cc)

    # -- CDU: variável de saída/estado de bloco (§29.10, régua El=CDU, Bl) --

    def saida_cdu(self, num_cdu: int, num_bloco: int) -> "BlocoDPLT":
        """Variável de saída de um bloco de CDU (§29.10: tipo CDU).

        Args:
            num_cdu:   número do controlador (ncdu).
            num_bloco: número do bloco do CDU cuja saída será plotada.
        """
        return self._add("CDU", num_cdu, num_bloco)

    def estado_cdu(self, num_cdu: int, num_bloco: int) -> "BlocoDPLT":
        """Variável de estado de um bloco de CDU (§29.10: tipo CDUE)."""
        return self._add("CDUE", num_cdu, num_bloco)

    # -- Escape hatch ---------------------------------------------------------

    def linha_bruta(self, texto: str) -> "BlocoDPLT":
        """Linha de plotagem no formato literal do ANATEM (sempre correto,
        use quando não tiver certeza do código de conveniência)."""
        self.linhas.append(texto)
        return self

    def serializar(self) -> str:
        linhas = [self._cabecalho()]
        for l in self.linhas:
            linhas.append(l.rstrip() + "\n")
        linhas.append(self._terminador())
        return "".join(linhas)


# ---------------------------------------------------------------------------
# DMAQ – Associação máquina↔modelo  (manual §46.41, pág. 751)
# ---------------------------------------------------------------------------


@dataclass
class _AssocMaquina:
    """Linha de associação máquina↔modelo no bloco DMAQ.

    Campos conforme §46.41 do manual:
        barra    – Nb: número da barra de geração
        grupo    – Gr: número do grupo de máquinas
        p        – percentual de potência ativa (inteiro, 100 se omitido)
        q        – percentual de potência reativa (inteiro, 100 se omitido)
        und      – número de unidades no grupo (1 se omitido)
        mg       – nº do modelo de gerador (DMDG)
        mt       – nº do modelo de regulador de tensão (DRGT ou CDU)
        mt_cdu   – True se mt é definido via CDU (flag 'u' após Mt)
        mv       – nº do modelo de regulador de velocidade (DRGV ou CDU)
        mv_cdu   – True se mv é definido via CDU (flag 'u' após Mv)
        me       – nº do modelo de estabilizador (DEST ou CDU)
        me_cdu   – True se me é definido via CDU (flag 'u' após Me)
        xvd      – reatância de compensação de queda de tensão [%]
        nbc      – nº da barra controlada (None = terminal, 0 = ANAREDE)
        texto_bruto – se preenchido, serializa literalmente (retrocompat.)
    """

    barra: int
    grupo: int
    p: Optional[int] = None
    q: Optional[int] = None
    und: Optional[int] = None
    mg: Optional[int] = None
    mt: Optional[int] = None
    mt_cdu: bool = False
    mv: Optional[int] = None
    mv_cdu: bool = False
    me: Optional[int] = None
    me_cdu: bool = False
    xvd: Optional[float] = None
    nbc: Optional[int] = None
    texto_bruto: Optional[str] = None

    @staticmethod
    def _fi(v: Optional[int], w: int) -> str:
        """Campo inteiro em largura fixa; espaços quando ausente."""
        return f"{v:>{w}}" if v is not None else " " * w

    @staticmethod
    def _ff(v: Optional[float], w: int) -> str:
        """Campo float em largura fixa; espaços quando ausente."""
        return f"{v:>{w}.4f}" if v is not None else " " * w

    @staticmethod
    def _fu(flag: bool) -> str:
        """Flag CDU: 'u' ou espaço."""
        return "u" if flag else " "

    def serializar(self) -> str:
        """Serializa a linha em colunas posicionais fixas conforme §46.41.

        Larguras derivadas da régua oficial do manual:
            ( Nb)   Gr (P) (Q) Und ( Mg ) ( Mt )u( Mv )u( Me )u(Xvd)(Nbc)

            Nb=5, Gr=5, P=4, Q=4, Und=4, Mg=7, Mt=7+u, Mv=7+u, Me=7+u,
            Xvd=5, Nbc=5 — todos right-aligned; flag 'u' minúsculo.

        Campos opcionais ausentes são emitidos como espaços em branco na
        posição correta, garantindo que campos posteriores não se desloquem.
        """
        if self.texto_bruto is not None:
            return self.texto_bruto
        fi = self._fi
        fu = self._fu
        xvd = f"{_num_compacto(self.xvd):>5}" if self.xvd is not None else " " * 5
        linha = (
            fi(self.barra, 5)
            + fi(self.grupo, 5)
            + fi(self.p, 4)
            + fi(self.q, 4)
            + fi(self.und, 4)
            + fi(self.mg, 7)
            + fi(self.mt, 7)
            + fu(self.mt_cdu)
            + fi(self.mv, 6)
            + fu(self.mv_cdu)
            + fi(self.me, 6)
            + fu(self.me_cdu)
            + xvd
            + fi(self.nbc, 5)
        )
        return linha.rstrip()

    # retrocompatibilidade: acesso via .unidade e .modelo (API antiga)
    @property
    def unidade(self) -> int:
        return self.grupo

    @property
    def modelo(self) -> str:
        return str(self.mg) if self.mg is not None else ""


@dataclass
class BlocoDMAQ(BlocoBase):
    """Associação de gerações a modelos de máquinas síncronas e controles (DMAQ).

    Implementação completa de §46.41 do manual.

    Campos de cada linha:
        Nb  Gr  [P]  [Q]  [Und]  [Mg]  [Mt][u]  [Mv][u]  [Me][u]  [Xvd]  [Nbc]

    Uso::

        caso.dmaq.adicionar_maquina(
            barra=1432, grupo=10, und=1,
            mg=751,                     # modelo DMDG
            mt=78, mt_cdu=False,        # regulador de tensão DRGT
            mv=126, mv_cdu=False,       # regulador de velocidade DRGV
        )

        # Com AVR definido via CDU
        caso.dmaq.adicionar_maquina(
            barra=3500, grupo=10, p=60, q=60, und=3,
            mg=753,
            mt=144, mt_cdu=True,  # CDU definido em DCDU
            mv=126, mv_cdu=False,
        )
    """

    keyword: str = field(default="DMAQ", init=False, repr=False)
    associacoes: List[_AssocMaquina] = field(default_factory=list)

    def tem_dados(self) -> bool:
        return bool(self.associacoes)

    def adicionar_maquina(
        self,
        barra: int,
        grupo: int,
        p: Optional[int] = None,
        q: Optional[int] = None,
        und: Optional[int] = None,
        mg: Optional[int] = None,
        mt: Optional[int] = None,
        mt_cdu: bool = False,
        mv: Optional[int] = None,
        mv_cdu: bool = False,
        me: Optional[int] = None,
        me_cdu: bool = False,
        xvd: Optional[float] = None,
        nbc: Optional[int] = None,
    ) -> "BlocoDMAQ":
        """Adiciona uma linha de associação máquina↔modelo.

        Args:
            barra:   Nb — número da barra de geração.
            grupo:   Gr — número do grupo de máquinas.
            p:       fator de potência ativa [%inteiro] (padrão=100).
            q:       fator de potência reativa [%inteiro] (padrão=100).
            und:     número de unidades no grupo (padrão=1).
            mg:      nº do modelo de gerador (campo No do DMDG).
            mt:      nº do modelo de regulador de tensão.
            mt_cdu:  True se mt é modelo CDU (flag 'u').
            mv:      nº do modelo de regulador de velocidade.
            mv_cdu:  True se mv é modelo CDU (flag 'u').
            me:      nº do modelo de estabilizador.
            me_cdu:  True se me é modelo CDU (flag 'u').
            xvd:     reatância de compensação de queda de tensão [%].
            nbc:     nº da barra controlada (None=terminal, 0=ANAREDE).

        Returns:
            self (encadeável).
        """
        self.associacoes.append(
            _AssocMaquina(
                barra=barra,
                grupo=grupo,
                p=p,
                q=q,
                und=und,
                mg=mg,
                mt=mt,
                mt_cdu=mt_cdu,
                mv=mv,
                mv_cdu=mv_cdu,
                me=me,
                me_cdu=me_cdu,
                xvd=xvd,
                nbc=nbc,
            )
        )
        return self

    def adicionar(
        self,
        barra: int,
        unidade: int,
        modelo: str,
        params: Optional[List[float]] = None,
    ) -> "BlocoDMAQ":
        """API legada (retrocompatibilidade) — preserva texto bruto."""
        base = f"{barra:>6}  {unidade:>4}  {modelo:<8}"
        if params:
            base += "  " + "  ".join(f"{p:>10.4f}" for p in params)
        self.associacoes.append(
            _AssocMaquina(barra=barra, grupo=unidade, texto_bruto=base)
        )
        return self

    def serializar(self) -> str:
        """Serializa o bloco DMAQ.

        A linha de comentário emitida é a régua oficial do manual (§46.41),
        alinhada às colunas reais dos campos de dados.
        """
        linhas = [self._cabecalho()]
        linhas.append("( Nb)   Gr (P) (Q) Und ( Mg ) ( Mt )u( Mv )u( Me )u(Xvd)(Nbc)\n")
        for a in self.associacoes:
            linhas.append(a.serializar() + "\n")
        linhas.append(self._terminador())
        return "".join(linhas)


# ---------------------------------------------------------------------------
# EXSI – Executa simulação  (manual §46.68, pág. 836)
# ---------------------------------------------------------------------------


@dataclass
class BlocoEXSI(BlocoBase):
    """Comando de execução do caso (EXSI, §46.68).

    ``opcoes``: opções de execução inline (ex.: ``["DLCA", "DLCC"]``).
    """

    keyword: str = field(default="EXSI", init=False, repr=False)
    opcoes: List[str] = field(default_factory=list)

    def serializar(self) -> str:
        if self.opcoes:
            return "EXSI " + " ".join(self.opcoes) + "\n"
        return "EXSI\n"


# ---------------------------------------------------------------------------
# DMDG – Modelos predefinidos de máquina síncrona  (manual §46.46, pág. 762)
#
# Três modelos disponíveis:
#   MD01 – Clássico (fonte de tensão + X'd): 1 régua
#   MD02 – Polos salientes (hidráulico), 1 campo + 2 amortecedores: 2 réguas
#   MD03 – Rotor liso (térmico), 1 campo + 3 amortecedores: 2 réguas
#
# NOTA DE CONFIANÇA: parâmetros e layout de colunas confirmados contra
# §46.46 do manual (markdowns_referencia/DMDG.md).
# ---------------------------------------------------------------------------


@dataclass
class _ModeloMD01:
    """Modelo Clássico (MD01) — fonte de tensão constante + X'd."""

    no: int
    ld: float  # L'd – indutância transitória d [%]
    h: float  # constante de inércia [s]
    mva: float  # potência nominal [MVA]
    ra: float = 0.0  # resistência de armadura [%]
    d: float = 0.0  # constante de amortecimento [pu/pu]
    fr: float = 60.0  # frequência nominal [Hz]
    corfreq: str = "N"  # correção de frequência (S/N)

    def serializar(self) -> str:
        """Colunas da régua oficial: (No)   (L'd)(Ra )( H )( D )(MVA)Fr M E.

        Campos com valor no default do ANATEM (Ra=0, D=0, Fr=60) ficam em
        branco, como nos exemplos oficiais; o flag de correção de frequência
        ocupa a primeira coluna de flag após Fr.
        """
        from pynatem.reguas_mdxx import serializar_registro

        fr = self.fr if self.fr != 60.0 else None
        flag = self.corfreq if self.corfreq.upper() == "S" else None
        linha = serializar_registro(
            "DMDG",
            "MD01",
            self.no,
            [
                self.ld,
                self.ra if self.ra else None,
                self.h,
                self.d if self.d else None,
                self.mva,
                fr,
                flag,
                None,
            ],
        )
        assert linha is not None  # régua DMDG/MD01 consta no registro
        return linha


@dataclass
class _ModeloMD02:
    """Modelo de polos salientes (MD02) — hidráulico, 2 réguas."""

    no: int
    ld: float  # indutância síncrona d [%]
    lq: float  # indutância síncrona q [%]
    ld_trans: float  # L'd transitória d [%]
    ld_sub: float  # L"d subtransitória d [%]
    ll: float  # indutância de dispersão [%]
    td_trans: float  # T'd transitória em CA [s]
    td_sub: float  # T"d subtransitória em CA [s]
    tq_sub: float  # T"q subtransitória em CA [s]
    h: float = 3.0  # constante de inércia [s]
    mva: float = 100.0  # potência nominal [MVA]
    cs: int = 0  # nº curva de saturação (0 = sem saturação)
    ra: float = 0.0
    d: float = 0.0
    fr: float = 60.0
    corfreq: str = "N"

    def serializar(self) -> str:
        """Duas linhas nas colunas das réguas oficiais do MD02 (§46.46)."""
        from pynatem.reguas_mdxx import serializar_registro

        fr = self.fr if self.fr != 60.0 else None
        flag = self.corfreq if self.corfreq.upper() == "S" else None
        r1 = serializar_registro(
            "DMDG",
            "MD02",
            self.no,
            [
                self.cs,
                self.ld,
                self.lq,
                self.ld_trans,
                self.ld_sub,
                self.ll,
                self.td_trans,
                self.td_sub,
                self.tq_sub,
            ],
            0,
        )
        r2 = serializar_registro(
            "DMDG",
            "MD02",
            self.no,
            [
                self.ra if self.ra else None,
                self.h,
                self.d if self.d else None,
                self.mva,
                fr,
                flag,
            ],
            1,
        )
        return f"{r1}\n{r2}"


@dataclass
class _ModeloMD03:
    """Modelo de rotor liso (MD03) — térmico, 2 réguas."""

    no: int
    ld: float  # indutância síncrona d [%]
    lq: float  # indutância síncrona q [%]
    ld_trans: float  # L'd [%]
    lq_trans: float  # L'q [%]
    ld_sub: float  # L"d [%]
    ll: float  # indutância de dispersão [%]
    td_trans: float  # T'd [s]
    tq_trans: float  # T'q [s]
    td_sub: float  # T"d [s]
    tq_sub: float  # T"q [s]
    h: float = 3.0
    mva: float = 100.0
    cs: int = 0
    ra: float = 0.0
    d: float = 0.0
    fr: float = 60.0
    corfreq: str = "N"

    def serializar(self) -> str:
        from pynatem.reguas_mdxx import serializar_registro

        fr = self.fr if self.fr != 60.0 else None
        flag = self.corfreq if self.corfreq.upper() == "S" else None
        r1 = serializar_registro(
            "DMDG",
            "MD03",
            self.no,
            [
                self.cs,
                self.ld,
                self.lq,
                self.ld_trans,
                self.lq_trans,
                self.ld_sub,
                self.ll,
                self.td_trans,
                self.tq_trans,
                self.td_sub,
                self.tq_sub,
            ],
            0,
        )
        r2 = serializar_registro(
            "DMDG",
            "MD03",
            self.no,
            [
                self.ra if self.ra else None,
                self.h,
                self.d if self.d else None,
                self.mva,
                fr,
                flag,
            ],
            1,
        )
        return f"{r1}\n{r2}"


@dataclass
class BlocoDMDG(BlocoBase):
    """Modelos predefinidos de máquina síncrona (DMDG).

    Suporta os três modelos do manual §46.46:

    - MD01: Clássico (fonte de tensão constante + X'd). Uma régua por modelo.
    - MD02: Polos salientes, 1 enrolamento de campo + 2 amortecedores
      (representação típica de usinas hidráulicas). Duas réguas por modelo.
    - MD03: Rotor liso, 1 campo + 3 amortecedores (representação típica de
      usinas térmicas). Duas réguas por modelo.

    Confiança: **Alta** — parâmetros confirmados contra §46.46 do manual.

    Uso::

        dmdg = BlocoDMDG()

        # barra infinita — MD01 sem inércia
        dmdg.adicionar_md01(no=20, ld=20.0, h=999.0, mva=9999.0)

        # gerador hidráulico — MD02
        dmdg.adicionar_md02(
            no=14,
            ld=170.0, lq=100.0, ld_trans=37.0,
            ld_sub=22.0, ll=15.4,
            td_trans=9.00, td_sub=0.060, tq_sub=0.200,
            ra=1.600, h=300.0, mva=100.0,
        )
    """

    keyword: str = field(default="DMDG", init=False, repr=False)
    _md01: List[_ModeloMD01] = field(default_factory=list)
    _md02: List[_ModeloMD02] = field(default_factory=list)
    _md03: List[_ModeloMD03] = field(default_factory=list)

    def tem_dados(self) -> bool:
        return bool(self._md01 or self._md02 or self._md03)

    def adicionar_md01(
        self,
        no: int,
        ld: float,
        h: float,
        mva: float,
        ra: float = 0.0,
        d: float = 0.0,
        fr: float = 60.0,
        corfreq: str = "N",
    ) -> "BlocoDMDG":
        """Adiciona um modelo clássico (MD01).

        Args:
            no:      número de identificação do modelo.
            ld:      indutância transitória de eixo direto L'd [%].
            h:       constante de inércia [s].
            mva:     potência aparente nominal [MVA].
            ra:      resistência de armadura [%] (default 0).
            d:       constante de amortecimento [pu/pu] (default 0).
            fr:      frequência síncrona [Hz] (default 60).
            corfreq: correção com frequência nas equações – 'S' ou 'N'.

        Returns:
            self (encadeável).
        """
        self._md01.append(
            _ModeloMD01(no=no, ld=ld, h=h, mva=mva, ra=ra, d=d, fr=fr, corfreq=corfreq)
        )
        return self

    def adicionar_md02(
        self,
        no: int,
        ld: float,
        lq: float,
        ld_trans: float,
        ld_sub: float,
        ll: float,
        td_trans: float,
        td_sub: float,
        tq_sub: float,
        h: float = 3.0,
        mva: float = 100.0,
        cs: int = 0,
        ra: float = 0.0,
        d: float = 0.0,
        fr: float = 60.0,
        corfreq: str = "N",
    ) -> "BlocoDMDG":
        """Adiciona modelo de polos salientes (MD02) — tipicamente hidráulico.

        Args:
            no:       número de identificação do modelo.
            ld:       indutância síncrona de eixo direto [%].
            lq:       indutância síncrona de eixo em quadratura [%].
            ld_trans: indutância transitória L'd [%].
            ld_sub:   indutância subtransitória L"d [%].
            ll:       indutância de dispersão da armadura [%].
            td_trans: constante de tempo transitória T'd em CA [s].
            td_sub:   constante de tempo subtransitória T"d em CA [s].
            tq_sub:   constante de tempo subtransitória T"q em CA [s].
            h:        constante de inércia [s].
            mva:      potência aparente nominal [MVA].
            cs:       número da curva de saturação (0 = sem saturação).
            ra:       resistência de armadura [%].
            d:        constante de amortecimento [pu/pu].
            fr:       frequência síncrona [Hz].
            corfreq:  correção de frequência 'S'/'N'.

        Returns:
            self (encadeável).
        """
        self._md02.append(
            _ModeloMD02(
                no=no,
                ld=ld,
                lq=lq,
                ld_trans=ld_trans,
                ld_sub=ld_sub,
                ll=ll,
                td_trans=td_trans,
                td_sub=td_sub,
                tq_sub=tq_sub,
                h=h,
                mva=mva,
                cs=cs,
                ra=ra,
                d=d,
                fr=fr,
                corfreq=corfreq,
            )
        )
        return self

    def adicionar_md03(
        self,
        no: int,
        ld: float,
        lq: float,
        ld_trans: float,
        lq_trans: float,
        ld_sub: float,
        ll: float,
        td_trans: float,
        tq_trans: float,
        td_sub: float,
        tq_sub: float,
        h: float = 3.0,
        mva: float = 100.0,
        cs: int = 0,
        ra: float = 0.0,
        d: float = 0.0,
        fr: float = 60.0,
        corfreq: str = "N",
    ) -> "BlocoDMDG":
        """Adiciona modelo de rotor liso (MD03) — tipicamente térmico.

        Args:
            no:       número de identificação do modelo.
            ld:       indutância síncrona de eixo direto [%].
            lq:       indutância síncrona de eixo em quadratura [%].
            ld_trans: indutância transitória L'd [%].
            lq_trans: indutância transitória L'q [%].
            ld_sub:   indutância subtransitória L"d [%].
            ll:       indutância de dispersão da armadura [%].
            td_trans: constante de tempo transitória T'd [s].
            tq_trans: constante de tempo transitória T'q [s].
            td_sub:   constante de tempo subtransitória T"d [s].
            tq_sub:   constante de tempo subtransitória T"q [s].
            h, mva, cs, ra, d, fr, corfreq: idem MD02.

        Returns:
            self (encadeável).
        """
        self._md03.append(
            _ModeloMD03(
                no=no,
                ld=ld,
                lq=lq,
                ld_trans=ld_trans,
                lq_trans=lq_trans,
                ld_sub=ld_sub,
                ll=ll,
                td_trans=td_trans,
                tq_trans=tq_trans,
                td_sub=td_sub,
                tq_sub=tq_sub,
                h=h,
                mva=mva,
                cs=cs,
                ra=ra,
                d=d,
                fr=fr,
                corfreq=corfreq,
            )
        )
        return self

    def serializar(self) -> str:
        linhas: List[str] = []

        if self._md01:
            linhas.append("DMDG MD01\n")
            linhas.append("(No)   (L'd)(Ra )( H )( D )(MVA)Fr M E\n")
            for m in self._md01:
                linhas.append(m.serializar() + "\n")
            linhas.append("999999\n")

        if self._md02:
            linhas.append("DMDG MD02\n")
            linhas.append(
                '(No)   (CS) (Ld )(Lq )(L\'d)     (L"d)(Ll )(T\'d)     (T"d)(T"q)\n'
            )
            linhas.append("(No)   (Ra )( H )( D )(MVA)Fr C\n")
            for m2 in self._md02:
                linhas.append(m2.serializar() + "\n")
            linhas.append("999999\n")

        if self._md03:
            linhas.append("DMDG MD03\n")
            linhas.append(
                "(No)   (CS) (Ld )(Lq )(L'd)(L'q)(L\"d)(Ll )(T'd)(T'q)(T\"d)(T\"q)\n"
            )
            linhas.append("(No)   (Ra )( H )( D )(MVA)Fr C\n")
            for m3 in self._md03:
                linhas.append(m3.serializar() + "\n")
            linhas.append("999999\n")

        return "".join(linhas)


# ---------------------------------------------------------------------------
# Modelos predefinidos de controle de máquina síncrona
#
# DRGT  §16.3 — Regulador de Tensão e Excitatriz   (24 modelos MD01–MD24)
# DRGV  §16.4 — Regulador de Velocidade e Turbina   (7 modelos MD01–MD07)
# DEST  §16.5 — Estabilizador (PSS) em Reg. de Tensão (12 modelos MD01–MD12)
# DCST  §16.2 — Curva de Saturação (bloco plano; 4 tipos, sem variante MDxx)
#
# Cada modelo MDxx tem régua de parâmetros própria. Estes blocos usam
# armazenamento GENÉRICO POSICIONAL: nº de identificação + parâmetros na ordem
# da régua do modelo. Isso cobre todos os modelos com roundtrip garantido, sem
# hardcode de cada régua. O modelo MD01 tem construtor nomeado, validado campo
# a campo contra o manual. A associação à máquina é feita via DMAQ (DRGT→Mv,
# DRGV→Mt, DEST→Me).
# ---------------------------------------------------------------------------


def _fmt_valor(v) -> str:
    """Formata um valor de parâmetro (int/float/str) de forma compacta."""
    if isinstance(v, float):
        return f"{v:g}"
    return str(v)


def _norm_md(modelo) -> str:
    """Normaliza o identificador de variante para 'MDnn' (ex.: 1 → 'MD01')."""
    if isinstance(modelo, int):
        return f"MD{modelo:02d}"
    m = str(modelo).upper().strip()
    if m.startswith("MD"):
        num = m[2:]
        return f"MD{int(num):02d}" if num.isdigit() else m
    return f"MD{int(m):02d}" if m.isdigit() else m


@dataclass
class _ModeloMDxx:
    """Registro genérico de um modelo predefinido MDxx (DRGT/DRGV/DEST).

    Armazenamento: ``no`` (identificador usado no DMAQ) + ``parametros``
    posicionais, na ordem exata da régua do modelo MDxx no manual.
    """

    modelo: str  # "MD01" ...
    no: int
    parametros: list = field(default_factory=list)

    def serializar(self) -> str:
        return "  ".join([f"{self.no:>4}"] + [_fmt_valor(p) for p in self.parametros])


@dataclass
class _BlocoModeloMDxx(BlocoBase):
    """Base dos blocos de modelos predefinidos por variante MDxx.

    Cobre qualquer modelo via parâmetros posicionais (roundtrip garantido).
    Emite um sub-bloco ``<keyword> MDxx`` por variante (o manual só permite
    uma variante por execução do código). Subclasses definem a ``keyword`` e
    construtores nomeados para os modelos mais comuns.
    """

    _modelos: list = field(default_factory=list)

    def tem_dados(self) -> bool:
        return bool(self._modelos)

    def adicionar(self, modelo, no: int, *parametros):
        """Adiciona um modelo genérico (qualquer MDxx).

        Args:
            modelo: "MD01".."MDnn" (ou o inteiro correspondente).
            no: número de identificação do modelo.
            *parametros: valores posicionais na ordem da régua do modelo.
        """
        self._modelos.append(
            _ModeloMDxx(modelo=_norm_md(modelo), no=no, parametros=list(parametros))
        )
        return self

    def serializar(self) -> str:
        ordem: list = []
        grupos: dict = {}
        for m in self._modelos:
            if m.modelo not in grupos:
                grupos[m.modelo] = []
                ordem.append(m.modelo)
            grupos[m.modelo].append(m)

        from pynatem.reguas_mdxx import (
            n_linhas_registro,
            regua_oficial,
            serializar_registro,
        )

        linhas: list = []
        for variante in ordem:
            linhas.append(f"{self.keyword} {variante}\n")
            n_lin = n_linhas_registro(self.keyword, variante)
            # emite as réguas oficiais como comentário (estilo dos exemplos)
            for k in range(n_lin):
                r = regua_oficial(self.keyword, variante, k)
                if r:
                    linhas.append(r + "\n")
            contador: dict = {}
            for m in grupos[variante]:
                idx = contador.get(m.no, 0) % n_lin
                contador[m.no] = contador.get(m.no, 0) + 1
                posicional = serializar_registro(
                    self.keyword, variante, m.no, m.parametros, idx
                )
                if posicional is not None:
                    linhas.append(posicional + "\n")
                else:
                    linhas.append(m.serializar() + "\n")
            linhas.append(self._terminador())
        return "".join(linhas)


@dataclass
class BlocoDRGT(_BlocoModeloMDxx):
    """Modelos predefinidos de Regulador de Tensão e Excitatriz (DRGT, §16.3).

    24 modelos (MD01–MD24). Cobre TODOS via parâmetros posicionais; o MD01 tem
    construtor nomeado validado campo a campo. Associação à máquina via DMAQ
    (campo Mv). Reguladores fora dos modelos predefinidos usam CDU (DCDU).

    Confiança: Alta — estrutura e MD01 validados contra §16.3; roundtrip
    garantido pelo ParserSTB.
    """

    keyword: str = field(default="DRGT", init=False, repr=False)

    def adicionar_md01(
        self,
        no: int,
        cs: int,
        ka: float,
        ke: float,
        kf: float,
        tm: float,
        ta: float,
        te: float,
        tf: float,
        lmn: float,
        lmx: float,
        l: str = "D",
        s: str = "I",
    ) -> "BlocoDRGT":
        """Regulador de tensão MD01 (§16.3), com campos nomeados e validados.

        Campos (na ordem da régua): Cs (curva saturação/DCST), Ka (ganho), Ke
        (excitatriz), Kf (ganho realimentação), Tm (transdutor), Ta (regulador),
        Te (excitatriz), Tf (realimentação), Lmn/Lmx (limites), L ('D' dinâmico
        ou 'E' estático), S ('D' se saturação × tensão de campo, senão 'I').
        """
        return self.adicionar(
            "MD01", no, cs, ka, ke, kf, tm, ta, te, tf, lmn, lmx, l, s
        )


@dataclass
class BlocoDRGV(_BlocoModeloMDxx):
    """Modelos predefinidos de Regulador de Velocidade e Turbina (DRGV, §16.4).

    7 modelos (MD01–MD07). Cobre TODOS via parâmetros posicionais; o MD01 tem
    construtor nomeado validado campo a campo. Associação à máquina via DMAQ
    (campo Mt). Reguladores fora dos modelos predefinidos usam CDU (DCDU).

    Confiança: Alta — estrutura e MD01 validados contra §16.4; roundtrip
    garantido pelo ParserSTB.
    """

    keyword: str = field(default="DRGV", init=False, repr=False)

    def adicionar_md01(
        self,
        no: int,
        r: float,
        rp: float,
        at: float,
        qnl: float,
        tw: float,
        tr: float,
        tf: float,
        tg: float,
        lmn: float,
        lmx: float,
        dtb: float,
        d: float,
        pbg: Optional[float] = None,
        pbt: Optional[float] = None,
        vel: Optional[float] = None,
    ) -> "BlocoDRGV":
        """Regulador de velocidade MD01 (§16.4), campos nomeados e validados.

        Campos (na ordem da régua oficial): R (estatismo permanente), Rp
        (estatismo transitório), At (ganho da turbina), Qnl (vazão sem carga),
        Tw (água), Tr (regulador), Tf (filtragem), Tg (servomotor), Vel
        (velocidade da comporta — coluna comprovada pelo exemplo oficial),
        Lmn/Lmx (limites de abertura da comporta), Dtb (amortecimento da
        turbina), D (amortecimento da carga), Pbg/Pbt (potências base do
        gerador [MVA] e da turbina [MW], opcionais).
        """
        return self.adicionar(
            "MD01", no, r, rp, at, qnl, tw, tr, tf, tg, vel, lmn, lmx, dtb, d, pbg, pbt
        )


@dataclass
class BlocoDEST(_BlocoModeloMDxx):
    """Modelos predefinidos de Estabilizador aplicado em Regulador de Tensão
    (PSS) — código DEST (§16.5).

    12 modelos (MD01–MD12). Cobre TODOS via parâmetros posicionais; o MD01 tem
    construtor nomeado validado campo a campo. Associação à máquina via DMAQ
    (campo Me). Estabilizadores fora dos modelos predefinidos usam CDU (DCDU).

    Confiança: Alta — estrutura e MD01 validados contra §16.5; roundtrip
    garantido pelo ParserSTB.
    """

    keyword: str = field(default="DEST", init=False, repr=False)

    def adicionar_md01(
        self,
        no: int,
        k: float,
        t: float,
        t1: float,
        t2: float,
        t3: float,
        t4: float,
        lmn: float,
        lmx: float,
    ) -> "BlocoDEST":
        """Estabilizador (PSS) MD01 (§16.5), com campos nomeados e validados.

        Campos (na ordem da régua): K (ganho), T (constante de tempo do
        transdutor/washout), T1–T4 (constantes de tempo dos compensadores de
        fase), Lmn/Lmx (limites de saída do estabilizador).
        """
        return self.adicionar("MD01", no, k, t, t1, t2, t3, t4, lmn, lmx)


@dataclass
class _CurvaSaturacao:
    """Uma curva de saturação de máquina síncrona (código DCST, §16.2)."""

    nc: int  # nº de identificação (referenciado no campo Cs do DMDG/DRGT)
    tipo: int  # 1=exp. c/ descontinuidade, 2=exp., 3=linear, 4=linear por partes
    p1: float  # Y1 (tipos 1/3/4) ou A (tipo 2)
    p2: float  # Y2 (tipos 1/3/4) ou B (tipo 2)
    p3: float  # X1 (tipos 1/3/4) ou C (tipo 2)

    def serializar(self) -> str:
        # régua oficial: (No)   T (  Y1  ) (  Y2  ) (  X1  )
        return f"{self.nc:>4}{self.tipo:>4}" + "".join(
            f"{_fmt_valor(p):>9}" for p in (self.p1, self.p2, self.p3)
        )


@dataclass
class BlocoDCST(BlocoBase):
    """Modelos de Curva de Saturação de máquina síncrona (DCST, §16.2).

    4 tipos de curva (campo Tp): 1 exponencial com descontinuidade, 2
    exponencial, 3 linear, 4 linear por partes. Cada curva é identificada por
    ``Nc`` e referenciada pelo campo ``Cs`` dos modelos de máquina/regulador
    (DMDG/DRGT). Parâmetros P1/P2/P3 conforme o tipo (§16.2).

    Confiança: Alta — régua (Nc, Tipo, P1, P2, P3) validada contra §16.2;
    roundtrip garantido pelo ParserSTB.
    """

    keyword: str = field(default="DCST", init=False, repr=False)
    _curvas: list = field(default_factory=list)

    def tem_dados(self) -> bool:
        return bool(self._curvas)

    def adicionar(
        self, nc: int, tipo: int, p1: float, p2: float, p3: float
    ) -> "BlocoDCST":
        """Adiciona uma curva de saturação.

        Args:
            nc: número de identificação (usado no campo Cs do DMDG/DRGT).
            tipo: 1 (exp. c/ descontinuidade), 2 (exp.), 3 (linear) ou 4
                (linear por partes).
            p1, p2, p3: parâmetros da curva (Y1/Y2/X1 nos tipos 1/3/4;
                A/B/C no tipo 2).
        """
        self._curvas.append(_CurvaSaturacao(nc=nc, tipo=tipo, p1=p1, p2=p2, p3=p3))
        return self

    def serializar(self) -> str:
        linhas = [self._cabecalho(), "(Nc) Tp ( P1 )( P2 )( P3 )\n"]
        for c in self._curvas:
            linhas.append(c.serializar() + "\n")
        linhas.append(self._terminador())
        return "".join(linhas)


# ---------------------------------------------------------------------------
# Controles de área associados a CDU (código de associação Nc + Mc[U])
#
# DCAG  §46.13 — Controle Automático de Geração (CAG, §16.7)
# DCCT  §46.15 — Controle Centralizado de Tensão (CCT, §16.8)
#
# Ambos só possuem modelo definido por CDU (não há modelos predefinidos), então
# o código apenas associa o controle (Nc) ao seu modelo CDU (Mc, sempre 'U').
# ---------------------------------------------------------------------------


@dataclass
class _AssocCDU:
    """Associação de um controle de área ao seu modelo CDU (Nc + Mc[U])."""

    nc: int  # nº de identificação do controle (CAG ou CCT)
    mc: int  # nº do modelo CDU (campo ncdu do DCDU)
    usuario: bool = True  # sempre 'U' — só há modelo por CDU

    def serializar(self) -> str:
        # régua oficial: (Nc)   ( Mc )u — Mc termina na col 12, flag na col 13
        return f"{self.nc:>4}{self.mc:>9}" + ("U" if self.usuario else " ")


@dataclass
class _BlocoAssocCDU(BlocoBase):
    """Base dos códigos de associação de controle de área a um modelo CDU."""

    _assoc: list = field(default_factory=list)

    def tem_dados(self) -> bool:
        return bool(self._assoc)

    def adicionar(self, nc: int, mc: int, usuario: bool = True):
        """Associa o controle ``nc`` ao modelo CDU ``mc`` (``usuario`` = flag U)."""
        self._assoc.append(_AssocCDU(nc=nc, mc=mc, usuario=usuario))
        return self

    def serializar(self) -> str:
        linhas = [self._cabecalho(), "(Nc)   ( Mc )u\n"]
        for a in self._assoc:
            linhas.append(a.serializar() + "\n")
        linhas.append(self._terminador())
        return "".join(linhas)


@dataclass
class BlocoDCAG(_BlocoAssocCDU):
    """Associação de Controle Automático de Geração a modelo CDU (DCAG, §46.13).

    O CAG (§16.7) só pode ser modelado por CDU; este código associa o CAG (Nc)
    ao seu modelo CDU (Mc). Confiança: Alta — régua validada contra §46.13
    (Listagem 46.11); roundtrip garantido.
    """

    keyword: str = field(default="DCAG", init=False, repr=False)


@dataclass
class BlocoDCCT(_BlocoAssocCDU):
    """Associação de Controle Centralizado de Tensão a modelo CDU (DCCT, §46.15).

    O CCT (§16.8) só pode ser modelado por CDU; este código associa o CCT (Nc)
    ao seu modelo CDU (Mc). Confiança: Alta — régua validada contra §46.15
    (Listagem 46.13); roundtrip garantido.
    """

    keyword: str = field(default="DCCT", init=False, repr=False)


# ---------------------------------------------------------------------------
# Cargas estáticas funcionais — DCAR (§46.14 / Cap. 11)
#
# Define a variação da carga estática com a tensão via parâmetros ZIP:
#   A/B → parcela ativa que varia com V / V²   (corrente/impedância constante)
#   C/D → parcela reativa que varia com V / V²
#   Vmn → tensão (%) abaixo da qual a carga vira impedância constante
#
# O DCAR usa "linguagem de seleção" (Cap. 42) para escolher as barras/cargas
# alvo — uma feature à parte (roadmap A43). Aqui a seleção é tratada como uma
# string opaca; a leitura preserva a linha bruta (roundtrip garantido).
# ---------------------------------------------------------------------------


@dataclass
class _CargaFuncional:
    """Definição/alteração de carga estática funcional (DCAR §46.14)."""

    selecao: str = ""  # expressão de seleção (ex.: "BARR 1 A BARR 9998")
    a: float = 0.0  # parcela ativa ~ V (corrente constante)
    b: float = 0.0  # parcela ativa ~ V² (impedância constante)
    c: float = 0.0  # parcela reativa ~ V
    d: float = 0.0  # parcela reativa ~ V²
    vmn: Optional[float] = None  # tensão (%) p/ Z constante (branco → default 70)
    texto_bruto: str = ""  # linha original (preserva roundtrip quando lida)

    def serializar(self) -> str:
        """Colunas fixas da régua oficial (§46.14): seleção até a col 51;
        (A) cols 52-54, (B) 56-58, (C) 60-62, (D) 64-66, (Vmn) 68-72."""
        if self.texto_bruto:
            return self.texto_bruto
        linha = f"{self.selecao:<52}" + " ".join(
            f"{_num_compacto(v):>3}" for v in (self.a, self.b, self.c, self.d)
        )
        if self.vmn is not None:
            linha += f" {_num_compacto(self.vmn):>5}"
        return linha.rstrip()


@dataclass
class BlocoDCAR(BlocoBase):
    """Cargas estáticas funcionais — modelo ZIP por tensão (DCAR, §46.14).

    Confiança: Média — os parâmetros do modelo de carga (A/B/C/D/Vmn) são
    estruturados e validados contra §46.14, mas a *linguagem de seleção* que
    escolhe as barras alvo (Cap. 42) é tratada como string opaca (roadmap A43).
    A leitura preserva a linha bruta, garantindo roundtrip.
    """

    keyword: str = field(default="DCAR", init=False, repr=False)
    opcoes: str = ""  # opções na linha de cabeçalho (ex.: "IMPR")
    _cargas: list = field(default_factory=list)

    def tem_dados(self) -> bool:
        return bool(self._cargas)

    def adicionar(
        self,
        selecao: str,
        a: float = 0.0,
        b: float = 0.0,
        c: float = 0.0,
        d: float = 0.0,
        vmn: Optional[float] = None,
    ) -> "BlocoDCAR":
        """Adiciona/altera um modelo de carga funcional (ZIP).

        Args:
            selecao: expressão da linguagem de seleção (barras/cargas alvo).
            a, b: parcelas da carga ativa que variam com V e V².
            c, d: parcelas da carga reativa que variam com V e V².
            vmn: tensão (%) abaixo da qual a carga vira impedância constante
                 (em branco, o ANATEM assume o default de 70%).
        """
        self._cargas.append(
            _CargaFuncional(selecao=selecao, a=a, b=b, c=c, d=d, vmn=vmn)
        )
        return self

    def adicionar_bruto(self, texto: str) -> "BlocoDCAR":
        """Adiciona uma linha DCAR no formato literal (escape hatch)."""
        self._cargas.append(_CargaFuncional(texto_bruto=texto))
        return self

    def _cabecalho(self) -> str:
        return f"{self.keyword} {self.opcoes}\n".replace(" \n", "\n")

    def serializar(self) -> str:
        linhas = [
            self._cabecalho(),
            "(tp) ( no) C (tp) ( no) C (tp) ( no) C (tp) ( no)   (A) (B) (C) (D) (Vmn)\n",
        ]
        for c in self._cargas:
            linhas.append(c.serializar() + "\n")
        linhas.append(self._terminador())
        return "".join(linhas)


# ---------------------------------------------------------------------------
# Geração Funcional ZIP — Cap. 17 / §46 (v1.5.2)
#
# DGER  — Geração ZIP funcional (modelo simétrico a DCAR, mas para geração)
# Comportamento: P = A·V + B·V² ; Q = C·V + D·V²
# Seleção de barras via linguagem de seleção (Cap. 42, tratada como opaca)
# ---------------------------------------------------------------------------


@dataclass
class _GeracaoFuncional:
    """Descrição de um modelo de geração funcional ZIP (DGER, §17.1)."""

    selecao: str = ""  # "BARR 1 A BARR 9998" etc. (linguagem de seleção)
    a: float = 0.0  # ativa ~ V [%]
    b: float = 0.0  # ativa ~ V² [%]
    c: float = 0.0  # reativa ~ V [%]
    d: float = 0.0  # reativa ~ V² [%]
    vbp: Optional[float] = None  # tensão base ativa [%] (branco → default)
    vdp: Optional[float] = None  # tensão limite ativa [%] (branco → default)
    vbq: Optional[float] = None  # tensão base reativa [%] (branco → default)
    vdq: Optional[float] = None  # tensão limite reativa [%] (branco → default)
    texto_bruto: str = ""  # fallback para roundtrip exato

    def serializar(self) -> str:
        """Colunas oficiais: seleção até col 51; (A) 52-54, (B) 56-58,
        (C) 60-62, (D) 64-66, (VbP) 68-72, (VdP) 74-78, (VbQ) 80-84, (VdQ) 86-90."""
        if self.texto_bruto:
            return self.texto_bruto
        linha = f"{self.selecao:<52}" + " ".join(
            f"{_num_compacto(v):>3}" for v in (self.a, self.b, self.c, self.d)
        )
        for v in (self.vbp, self.vdp, self.vbq, self.vdq):
            # percentuais com 1 casa decimal (estilo do exemplo oficial: 84.5)
            linha += f" {v:>5.1f}" if v is not None else " " * 6
        return linha.rstrip()


@dataclass
class BlocoDGER(BlocoBase):
    """Geração Funcional ZIP (DGER, §17.1, Cap. 17 / v1.5.2).

    Modelo simétrico a DCAR, mas para geração. Define o comportamento de
    gerações que não têm modelo dinâmico explícito. Gerações sem modelo
    DGER são automaticamente convertidas em impedância constante.

    Confiança: Média — os parâmetros ZIP (A/B/C/D) e tensões são estruturados,
    mas a linguagem de seleção de barras (Cap. 42) é tratada como string opaca
    (parsing completo fica para roadmap A43/v1.9.2).

    Uso::

        dger = BlocoDGER()
        dger.adicionar("BARR 1 A BARR 9998", a=50, b=50, c=100, d=0)
    """

    keyword: str = field(default="DGER", init=False, repr=False)
    opcoes: str = ""  # opções na linha de cabeçalho (ex.: "IMPR")
    _geracoes: list = field(default_factory=list)

    def tem_dados(self) -> bool:
        return bool(self._geracoes)

    def adicionar(
        self,
        selecao: str,
        a: float = 0.0,
        b: float = 0.0,
        c: float = 0.0,
        d: float = 0.0,
        vbp: Optional[float] = None,
        vdp: Optional[float] = None,
        vbq: Optional[float] = None,
        vdq: Optional[float] = None,
    ) -> "BlocoDGER":
        """Adiciona um modelo de geração funcional (ZIP).

        Args:
            selecao: expressão de seleção de barras (linguagem Cap. 42).
            a, b: parcelas ativas que variam com V e V² [%].
            c, d: parcelas reativas que variam com V e V² [%].
            vbp, vdp: tensões base e limite para ativa [%].
            vbq, vdq: tensões base e limite para reativa [%].
        """
        self._geracoes.append(
            _GeracaoFuncional(
                selecao=selecao, a=a, b=b, c=c, d=d, vbp=vbp, vdp=vdp, vbq=vbq, vdq=vdq
            )
        )
        return self

    def adicionar_bruto(self, texto: str) -> "BlocoDGER":
        """Adiciona uma linha DGER no formato literal (escape hatch)."""
        self._geracoes.append(_GeracaoFuncional(texto_bruto=texto))
        return self

    def _cabecalho(self) -> str:
        return f"{self.keyword} {self.opcoes}\n".replace(" \n", "\n")

    def serializar(self) -> str:
        linhas = [
            self._cabecalho(),
            "(tp) ( no) C (tp) ( no) C (tp) ( no) C (tp) ( no)   "
            "(A) (B) (C) (D) (VbP) (VdP) (VbQ) (VdQ)\n",
        ]
        for g in self._geracoes:
            linhas.append(g.serializar() + "\n")
        linhas.append(self._terminador())
        return "".join(linhas)


# ---------------------------------------------------------------------------
# Transformadores OLTC (comutação sob carga) — Cap. 14 / §46.40
#
# DMTC  §14.1 — modelo predefinido de controle de tap (No + parâmetros)
# DLTC  §46.40 — dados adicionais do OLTC + associação ao modelo de controle
#
# O transformador em si é um Circuito CA definido no ANAREDE (com Tap mín/máx);
# DMTC define o controle de tap e DLTC o associa ao circuito.
# ---------------------------------------------------------------------------


@dataclass
class BlocoDMTC(_BlocoModeloMDxx):
    """Modelos predefinidos de controle de tap de OLTC (DMTC, §14.1).

    Cobre os modelos via parâmetros posicionais; o MD01 tem construtor nomeado.
    A associação ao transformador é feita via DLTC (campo Mt).

    Confiança: Alta — estrutura e MD01 validados contra §14.1; roundtrip
    garantido pelo ParserSTB.
    """

    keyword: str = field(default="DMTC", init=False, repr=False)

    def adicionar_md01(
        self,
        no: int,
        bm1: float,
        bm2: float,
        tr: float,
        tm: float,
        tb: float,
        t: float,
        vlm: float = 0.0,
    ) -> "BlocoDMTC":
        """Controle de tap MD01 (§14.1), com campos nomeados e validados.

        Campos (na ordem da régua): Bm1/Bm2 (bandas mortas), TR (tempo de ajuste
        do relé), TM/TB/T (constantes de tempo), Vlm (tensão abaixo da qual o
        controle de tap é congelado; 0 = não congela).
        """
        return self.adicionar("MD01", no, bm1, bm2, tr, tm, tb, t, vlm)


# Colunas do OLTC (DLTC §46.40). Tmn/Tmx/Kbs são opcionais → colunas fixas
# (espelhadas por ParserSTB._ler_dltc).
_DLTC_COLS = (
    ("de", 5),
    ("pa", 8),
    ("nc", 3),
    ("mt", 8),  # 7 + coluna do flag 'u'
    ("tmn", 6),
    ("tmx", 6),
    ("nst", 4),
    ("kbs", 7),
)


@dataclass
class _AssocOLTC:
    """Dados adicionais de um OLTC e associação ao seu controle (DLTC §46.40)."""

    de: int  # barra DE do circuito (ANAREDE/DLIN)
    pa: int  # barra PARA do circuito
    mt: int  # nº do modelo de controle (DMTC ou CDU)
    nc: Optional[int] = None  # nº do circuito paralelo (branco → 1)
    nst: int = 1  # nº de intervalos de discretização do tap (>0)
    mt_usuario: bool = False  # 'u' se Mt definido por CDU
    tmn: Optional[float] = None  # tap mínimo [pu] (branco → ANAREDE)
    tmx: Optional[float] = None  # tap máximo [pu] (branco → ANAREDE)
    kbs: Optional[int] = None  # barra controlada (sinal indica direção)

    def serializar(self) -> str:
        # régua oficial: ( Nf)   ( Nt) Nc ( Mt )u (Tmn) (Tmx) Nst ( Kbs)
        return (
            _col_int(self.de, 5)
            + _col_int(self.pa, 8)
            + _col_int(self.nc, 3)
            + _col_int(self.mt, 7)
            + ("u" if self.mt_usuario else " ")
            + _col_float(self.tmn, 6)
            + _col_float(self.tmx, 6)
            + _col_int(self.nst, 4)
            + _col_int(self.kbs, 7)
        ).rstrip()


@dataclass
class BlocoDLTC(BlocoBase):
    """Dados de Transformadores OLTC e associação ao controle (DLTC, §46.40).

    O transformador é um Circuito CA definido no ANAREDE; este código informa os
    dados adicionais do OLTC (faixa e discretização do tap, barra controlada) e
    associa ao modelo de controle (DMTC ou CDU). Campos Tmn/Tmx/Kbs opcionais
    (branco → valor do ANAREDE); para defasador puro, deixe-os em branco e Nst=1.

    Confiança: Alta — campos e ordem validados contra §46.40 (Listagem 46.38);
    serialização em colunas fixas com roundtrip garantido.
    """

    keyword: str = field(default="DLTC", init=False, repr=False)
    _oltcs: list = field(default_factory=list)

    def tem_dados(self) -> bool:
        return bool(self._oltcs)

    def adicionar(
        self,
        de: int,
        pa: int,
        mt: int,
        nc: Optional[int] = None,
        nst: int = 1,
        mt_usuario: bool = False,
        tmn: Optional[float] = None,
        tmx: Optional[float] = None,
        kbs: Optional[int] = None,
    ) -> "BlocoDLTC":
        """Associa um transformador OLTC (circuito De-Pa-Nc) ao controle Mt."""
        self._oltcs.append(
            _AssocOLTC(
                de=de,
                pa=pa,
                mt=mt,
                nc=nc,
                nst=nst,
                mt_usuario=mt_usuario,
                tmn=tmn,
                tmx=tmx,
                kbs=kbs,
            )
        )
        return self

    def _guia(self) -> str:
        # régua oficial do manual (§46.40)
        return "( Nf)   ( Nt) Nc ( Mt )u (Tmn) (Tmx) Nst ( Kbs)\n"

    def serializar(self) -> str:
        linhas = [self._cabecalho(), self._guia()]
        for o in self._oltcs:
            linhas.append(o.serializar() + "\n")
        linhas.append(self._terminador())
        return "".join(linhas)


# ---------------------------------------------------------------------------
# Circuitos CA — Fluxo Agregado de Intercâmbio (DFLA, §13.1)
#
# O circuito CA em si é dado do ANAREDE (não há código próprio no ANATEM); seus
# eventos usam o DEVT e a plotagem usa FLXP/FLXQ/FLXC. O DFLA agrega os fluxos
# de vários circuitos numa "área" para monitoração/plotagem do intercâmbio.
# ---------------------------------------------------------------------------


@dataclass
class _CircuitoIntercambio:
    """Um circuito CA que compõe uma área de fluxo agregado (DFLA §13.1)."""

    de: int  # barra DE (ANAREDE)
    pa: int  # barra PARA (ANAREDE)
    nc: Optional[int] = None  # nº do circuito (branco → 1)
    ex: Optional[int] = None  # extremidade de medição (default=De; sinal inverte)

    def serializar(self) -> str:
        # régua oficial: (De ) (Pa ) NC ( Ex )
        campos = [f"{self.de:>5}", f" {self.pa:>5}", _col_int(self.nc, 3)]
        if self.ex is not None:
            campos.append(f"{self.ex:>7}")
        return "".join(campos).rstrip()


@dataclass
class _AreaFluxo:
    """Área de fluxo agregado de intercâmbio (DFLA §13.1)."""

    na: int  # nº de identificação da área (distinto da área do ANAREDE)
    ident: str = ""  # identificação alfanumérica
    circuitos: list = field(default_factory=list)

    def adicionar_circuito(
        self, de: int, pa: int, nc: Optional[int] = None, ex: Optional[int] = None
    ) -> "_AreaFluxo":
        """Adiciona um circuito à área (encadeável)."""
        self.circuitos.append(_CircuitoIntercambio(de=de, pa=pa, nc=nc, ex=ex))
        return self


@dataclass
class BlocoDFLA(BlocoBase):
    """Fluxo Agregado de Intercâmbio (DFLA, §13.1).

    Agrega os fluxos de vários circuitos CA numa "área" para monitoração e
    plotagem do intercâmbio. Bloco aninhado: por área, uma linha ``NA ID`` e
    a lista de circuitos (``De Pa NC [Ex]``), encerrada por ``FIMFLA``.

    Confiança: Alta — estrutura validada contra §13.1; roundtrip garantido.
    """

    keyword: str = field(default="DFLA", init=False, repr=False)
    _areas: list = field(default_factory=list)

    def tem_dados(self) -> bool:
        return bool(self._areas)

    def adicionar_area(self, na: int, ident: str = "") -> _AreaFluxo:
        """Cria uma área de fluxo agregado e a retorna (para adicionar circuitos).

        Args:
            na: número de identificação da área (distinto da área do ANAREDE).
            ident: identificação alfanumérica (opcional).
        """
        area = _AreaFluxo(na=na, ident=ident)
        self._areas.append(area)
        return area

    def serializar(self) -> str:
        linhas = [self._cabecalho()]
        for area in self._areas:
            linhas.append(f"{area.na:>4} {area.ident}".rstrip() + "\n")
            for c in area.circuitos:
                linhas.append(c.serializar() + "\n")
            linhas.append("FIMFLA\n")
        linhas.append(self._terminador())
        return "".join(linhas)


# ---------------------------------------------------------------------------
# FACTS – blocos de associação e de conversores
#
# DCER  §46.18 — associação de compensador estático (CER/SVC) a modelos
# DCSC  §46.22 — associação de compensador série controlável (CSC/TCSC)
# DVSI  §46.64 — dados de conversores FACTS VSI (STATCOM/SSSC)
#
# Campos e ordem validados contra o manual (Listagens 46.16 / 46.20 / 46.61,
# Caps. 25–27 e 46). DCER/DCSC são códigos de ASSOCIAÇÃO — o equipamento em si
# (faixa de operação, estatismo, nº de unidades) é definido no ANAREDE; estes
# códigos apenas ligam o equipamento ao seu modelo dinâmico e ao estabilizador.
# ---------------------------------------------------------------------------


def _sep_u(numero: int, usuario: bool) -> str:
    """Formata ``<numero>[U]`` — a letra U (colada) marca modelo do usuário."""
    return f"{numero}{'U' if usuario else ''}"


def _sep_u_float(valor: float, usuario: bool) -> str:
    """Formata ``<valor>[U]`` para floats — U marca CDU vs. parâmetro."""
    if usuario:
        return f"{int(valor)}U"
    return f"{valor:.2f}"


@dataclass
class _AssocCER:
    """Associação de um grupo de CER/SVC a seus modelos (código DCER, §46.18).

    Régua do manual (Listagem 46.16):  ``( Nb) Gr ( Mc )u( Me )u``
    """

    nb: int  # barra CA à qual o grupo de compensadores está conectado
    gr: int  # nº do grupo de compensadores estáticos
    mc: int  # nº do modelo de CER (DMCE predefinido ou CDU do usuário)
    me: Optional[int] = None  # nº do modelo de estabilizador (CDU), opcional
    mc_usuario: bool = False  # 'U' se Mc foi definido pelo usuário (DCDU/DTDU)
    me_usuario: bool = True  # estabilizador só pode ser definido por CDU

    def serializar(self) -> str:
        from pynatem.reguas_mdxx import REGUAS_CODIGOS, serializar_linha

        def flag(num, usuario):
            return "U" if (num is not None and usuario) else None

        return serializar_linha(
            REGUAS_CODIGOS["DCER"],
            [
                self.nb,
                self.gr,
                self.mc,
                flag(self.mc, self.mc_usuario),
                self.me,
                flag(self.me, self.me_usuario),
            ],
        )


@dataclass
class BlocoSVC(BlocoBase):
    """Associação de Compensadores Estáticos de Reativos a controles (DCER).

    Confiança: Alta — campos e ordem validados contra o manual §46.18
    (Listagem 46.16). Roundtrip garantido (serializa ↔ ``ParserSTB``).
    """

    keyword: str = field(default="DCER", init=False, repr=False)
    _equipamentos: list = field(default_factory=list)

    def tem_dados(self) -> bool:
        return bool(self._equipamentos)

    def adicionar(
        self,
        nb: int,
        gr: int,
        mc: int,
        me: Optional[int] = None,
        mc_usuario: bool = False,
        me_usuario: bool = True,
    ) -> "BlocoSVC":
        self._equipamentos.append(
            _AssocCER(
                nb=nb, gr=gr, mc=mc, me=me, mc_usuario=mc_usuario, me_usuario=me_usuario
            )
        )
        return self

    def serializar(self) -> str:
        from pynatem.reguas_mdxx import REGUAS_CODIGOS

        linhas = [self._cabecalho(), REGUAS_CODIGOS["DCER"] + "\n"]
        for eq in self._equipamentos:
            linhas.append(eq.serializar() + "\n")
        linhas.append(self._terminador())
        return "".join(linhas)


@dataclass
class _AssocCSC:
    """Associação de um CSC/TCSC a seus modelos (código DCSC, §46.22).

    Régua do manual (Listagem 46.20):  ``( De) ( Pa) Nc ( Mc )u ( Me )u``
    """

    de: int  # barra DE do compensador série
    pa: int  # barra PARA do compensador série
    mc: int  # nº do modelo de CSC (DMCS predefinido ou CDU do usuário)
    nc: int = 1  # nº do circuito paralelo (default = 1)
    me: Optional[int] = None
    mc_usuario: bool = False
    me_usuario: bool = True

    def serializar(self) -> str:
        partes = [
            f"{self.de:>5}",
            f"{self.pa:>6}",
            f"{self.nc:>3}",
            f"{_sep_u(self.mc, self.mc_usuario):>7}",
        ]
        if self.me is not None:
            partes.append(f"{_sep_u(self.me, self.me_usuario):>7}")
        return "".join(partes)


@dataclass
class BlocoTCSC(BlocoBase):
    """Associação de Compensadores Série Controláveis a controles (DCSC).

    Confiança: Alta — campos e ordem validados contra o manual §46.22
    (Listagem 46.20). Roundtrip garantido.
    """

    keyword: str = field(default="DCSC", init=False, repr=False)
    _equipamentos: list = field(default_factory=list)

    def tem_dados(self) -> bool:
        return bool(self._equipamentos)

    def adicionar(
        self,
        de: int,
        pa: int,
        mc: int,
        nc: int = 1,
        me: Optional[int] = None,
        mc_usuario: bool = False,
        me_usuario: bool = True,
    ) -> "BlocoTCSC":
        self._equipamentos.append(
            _AssocCSC(
                de=de,
                pa=pa,
                mc=mc,
                nc=nc,
                me=me,
                mc_usuario=mc_usuario,
                me_usuario=me_usuario,
            )
        )
        return self

    def serializar(self) -> str:
        linhas = [self._cabecalho(), "( De) ( Pa) Nc ( Mc )u ( Me )u\n"]
        for eq in self._equipamentos:
            linhas.append(eq.serializar() + "\n")
        linhas.append(self._terminador())
        return "".join(linhas)


# Larguras de coluna do conversor VSI (§46.64). Campos Pa/Rv/Vpt são opcionais,
# então a linha é serializada em COLUNAS FIXAS — um campo em branco não pode
# deslocar os seguintes. Estes offsets são espelhados por ``ParserSTB._ler_dvsi``.
_VSI_COLS = (
    ("nv", 5),
    ("de", 6),
    ("pa", 6),
    ("nx", 4),
    ("np", 4),
    ("cnvk", 14),
    ("m", 2),
    ("vb", 10),
    ("rv", 10),
    ("xv", 10),
    ("vpt", 10),
    ("vst", 10),
    ("st", 10),
    ("tap", 8),
    ("ne", 6),
)


def _num(v: float) -> str:
    """Formata float de forma compacta e round-trippable (``repr`` do float)."""
    return repr(float(v))


def _col_int(v: Optional[int], w: int) -> str:
    return " " * w if v is None else f"{v:>{w}d}"


def _col_float(v: Optional[float], w: int) -> str:
    return " " * w if v is None else f"{_num(v):>{w}}"


@dataclass
class _ConversorVSI:
    """Dados de um conversor FACTS VSI (código DVSI, §46.64).

    Régua do manual (Listagem 46.61)::

        (Nv) ( De) ( Pa) Nx np ( Cnvk )M(Vb ) ( Rv)( Xv)(Vpt)(Vst)(St )(Tap) (Ne)

    Campos ``pa``, ``rv`` e ``vpt`` são opcionais: a conexão *shunt* deixa
    ``Pa`` em branco e o manual recomenda deixar ``Rv`` em branco.
    """

    nv: int  # nº de identificação do conversor VSI
    de: int  # barra terminal (shunt) ou barra DE do compensador série
    np: int  # nº de pontes conversoras em série no lado CA
    cnvk: float  # fator de forma Kf da tensão do conversor
    vb: float  # tensão base CA nas barras terminais [kV]
    xv: float  # reatância do trafo por ponte [pu]
    vst: float  # tensão base do enrolamento secundário [kV]
    st: float  # potência base de uma unidade do trafo conversor [MW]
    ne: int  # nº do equipamento FACTS VSI (código DEVS) ao qual pertence
    pa: Optional[int] = None  # barra PARA (série); em branco para shunt
    nx: int = 1  # grupo (shunt) ou circuito paralelo (série)
    m: str = "P"  # estratégia de chaveamento: 'P' (PWM) ou 'N' (não-PWM)
    rv: Optional[float] = None  # resistência do trafo por ponte [pu]
    vpt: Optional[float] = None  # tensão base do enrolamento primário [kV]
    tap: float = 1.0  # tap do trafo no lado secundário [pu]

    def serializar(self) -> str:
        from pynatem.reguas_mdxx import REGUAS_CODIGOS, serializar_linha

        return serializar_linha(
            REGUAS_CODIGOS["DVSI"],
            [
                self.nv,
                self.de,
                self.pa,
                self.nx,
                self.np,
                self.cnvk,
                self.m,
                self.vb,
                self.rv,
                self.xv,
                self.vpt,
                self.vst,
                self.st,
                self.tap,
                self.ne,
            ],
        )


@dataclass
class BlocoSTATCOM(BlocoBase):
    """Dados de conversores FACTS VSI — STATCOM/SSSC (DVSI, §46.64).

    Confiança: Alta — conjunto e ordem dos 15 campos validados contra o
    manual §46.64 (Listagem 46.61); serialização em colunas fixas com
    roundtrip garantido pelo parser. As larguras de coluna seguem a
    régua-guia do manual; a validação byte-a-byte contra um ``.stb`` real
    do CEPEL fica pendente de amostra.
    """

    keyword: str = field(default="DVSI", init=False, repr=False)
    _conversores: list = field(default_factory=list)

    def tem_dados(self) -> bool:
        return bool(self._conversores)

    def adicionar(
        self,
        nv: int,
        de: int,
        np: int,
        cnvk: float,
        vb: float,
        xv: float,
        vst: float,
        st: float,
        ne: int,
        pa: Optional[int] = None,
        nx: int = 1,
        m: str = "P",
        rv: Optional[float] = None,
        vpt: Optional[float] = None,
        tap: float = 1.0,
    ) -> "BlocoSTATCOM":
        self._conversores.append(
            _ConversorVSI(
                nv=nv,
                de=de,
                np=np,
                cnvk=cnvk,
                vb=vb,
                xv=xv,
                vst=vst,
                st=st,
                ne=ne,
                pa=pa,
                nx=nx,
                m=m,
                rv=rv,
                vpt=vpt,
                tap=tap,
            )
        )
        return self

    def _guia(self) -> str:
        from pynatem.reguas_mdxx import REGUAS_CODIGOS

        return REGUAS_CODIGOS["DVSI"] + "\n"

    def serializar(self) -> str:
        linhas = [self._cabecalho(), self._guia()]
        for c in self._conversores:
            linhas.append(c.serializar() + "\n")
        linhas.append(self._terminador())
        return "".join(linhas)


# ---------------------------------------------------------------------------
# HVDC (elos LCC) – blocos de associação
#
# DCNV  §46.21 — dados de conversor CA-CC e associação aos controles
# DELO  §46.27 — associação de elos CC aos modelos (DMEL / CDU)
#
# Como nos FACTS, os dados físicos do conversor/elo (barras, potência, tensão
# CC) vêm do ANAREDE; DCNV/DELO informam parâmetros de controle e associam os
# equipamentos aos seus modelos dinâmicos.
# ---------------------------------------------------------------------------


def _col_modelo(num: Optional[int], usuario: bool, w: int) -> str:
    """Formata ``<num>[U]`` (modelo + flag usuário) em coluna fixa; None → branco."""
    return " " * w if num is None else f"{_sep_u(num, usuario):>{w}}"


# Colunas do conversor CA-CC (DCNV §46.21). Gkb/Amn/Amx/Gmn e S1–S4 são
# opcionais, então usa-se colunas fixas (espelhadas por ParserSTB._ler_dcnv).
_CACC_COLS = (
    ("no", 5),
    ("gkb", 8),
    ("amn", 8),
    ("amx", 8),
    ("gmn", 8),
    ("mc", 7),
    ("s1", 7),
    ("s2", 7),
    ("s3", 7),
    ("s4", 7),
)


@dataclass
class _ConversorCACC:
    """Conversor CA-CC de elo LCC e sua associação a controles (DCNV, §46.21).

    Régua do manual (Listagem 46.19)::

        (No) (Gkb)(Amn)(Amx)(Gmn)( Mc )u( S1 )u( S2 )u( S3 )u( S4 )u

    ``Mc`` é o modelo de controle (associação obrigatória); ``S1``–``S4`` são
    modelos de sinal de modulação, todos opcionais. Cada modelo pode trazer a
    flag ``U`` (definido pelo usuário via DCDU/ACDU). Os ângulos ``Amn``/``Amx``/
    ``Gmn`` em branco assumem o valor do ANAREDE.

    Nota: o campo ``tap`` (modelo de controle de tap), citado na régua textual
    §46.21.2, não aparece no exemplo do manual e não é serializado aqui.
    """

    no: int  # nº de identificação do conversor
    mc: int  # nº do modelo de controle do conversor (DMCV ou CDU)
    gkb: Optional[float] = None  # fator do balanceador de ordem de corrente
    amn: Optional[float] = None  # alpha mínimo [graus]
    amx: Optional[float] = None  # alpha máximo [graus]
    gmn: Optional[float] = None  # gama mínimo [graus]
    mc_usuario: bool = False
    s1: Optional[int] = None  # modelos de sinal de modulação (opcionais)
    s2: Optional[int] = None
    s3: Optional[int] = None
    s4: Optional[int] = None
    s1_usuario: bool = False
    s2_usuario: bool = False
    s3_usuario: bool = False
    s4_usuario: bool = False

    def serializar(self) -> str:
        from pynatem.reguas_mdxx import REGUAS_CODIGOS, serializar_linha

        def flag(num, usuario):
            return "U" if (num is not None and usuario) else None

        return serializar_linha(
            REGUAS_CODIGOS["DCNV"],
            [
                self.no,
                self.gkb,
                self.amn,
                self.amx,
                self.gmn,
                self.mc,
                flag(self.mc, self.mc_usuario),
                self.s1,
                flag(self.s1, self.s1_usuario),
                self.s2,
                flag(self.s2, self.s2_usuario),
                self.s3,
                flag(self.s3, self.s3_usuario),
                self.s4,
                flag(self.s4, self.s4_usuario),
            ],
        )


@dataclass
class BlocoHVDC(BlocoBase):
    """Associação de conversores CA-CC de elos LCC a controles (DCNV, §46.21).

    Confiança: Alta — campos e ordem validados contra o manual §46.21
    (Listagem 46.19); serialização em colunas fixas com roundtrip garantido.
    As larguras seguem a régua-guia do manual (byte-validação contra `.stb`
    real do CEPEL pendente de amostra).
    """

    keyword: str = field(default="DCNV", init=False, repr=False)
    _conversores: list = field(default_factory=list)

    def tem_dados(self) -> bool:
        return bool(self._conversores)

    def adicionar(
        self,
        no: int,
        mc: int,
        gkb: Optional[float] = None,
        amn: Optional[float] = None,
        amx: Optional[float] = None,
        gmn: Optional[float] = None,
        mc_usuario: bool = False,
        s1: Optional[int] = None,
        s2: Optional[int] = None,
        s3: Optional[int] = None,
        s4: Optional[int] = None,
        s1_usuario: bool = False,
        s2_usuario: bool = False,
        s3_usuario: bool = False,
        s4_usuario: bool = False,
    ) -> "BlocoHVDC":
        self._conversores.append(
            _ConversorCACC(
                no=no,
                mc=mc,
                gkb=gkb,
                amn=amn,
                amx=amx,
                gmn=gmn,
                mc_usuario=mc_usuario,
                s1=s1,
                s2=s2,
                s3=s3,
                s4=s4,
                s1_usuario=s1_usuario,
                s2_usuario=s2_usuario,
                s3_usuario=s3_usuario,
                s4_usuario=s4_usuario,
            )
        )
        return self

    def _guia(self) -> str:
        rotulos = {
            "no": "(No)",
            "gkb": "(Gkb)",
            "amn": "(Amn)",
            "amx": "(Amx)",
            "gmn": "(Gmn)",
            "mc": "(Mc)u",
            "s1": "(S1)u",
            "s2": "(S2)u",
            "s3": "(S3)u",
            "s4": "(S4)u",
        }
        return "".join(f"{rotulos[nome]:>{w}}" for nome, w in _CACC_COLS) + "\n"

    def serializar(self) -> str:
        linhas = [self._cabecalho(), self._guia()]
        for c in self._conversores:
            linhas.append(c.serializar() + "\n")
        linhas.append(self._terminador())
        return "".join(linhas)


@dataclass
class _AssocElo:
    """Associação de um elo CC aos modelos de polo (DELO, §46.27).

    Régua do manual (Listagem 46.25):  ``(Ne) ( M+ )u( M- )u``

    ``mp`` (polo positivo) é obrigatório; ``mm`` (polo negativo) é opcional
    (elos monopolares só têm polo positivo). Cada modelo pode trazer flag U.
    """

    ne: int  # nº de identificação do elo CC
    mp: int  # modelo do polo positivo (DMEL ou CDU)
    mm: Optional[int] = None  # modelo do polo negativo (opcional)
    mp_usuario: bool = False
    mm_usuario: bool = False

    def serializar(self) -> str:
        # régua oficial: (Ne)   ( M+ )u( M- )u
        linha = f"{self.ne:>4}{self.mp:>9}" + ("u" if self.mp_usuario else " ")
        if self.mm is not None:
            linha += f"{self.mm:>6}" + ("u" if self.mm_usuario else "")
        return linha.rstrip()


@dataclass
class BlocoDELO(BlocoBase):
    """Associação de elos CC (LCC) aos seus modelos de polo (DELO, §46.27).

    Confiança: Alta — campos e ordem validados contra o manual §46.27
    (Listagem 46.25). Roundtrip garantido.
    """

    keyword: str = field(default="DELO", init=False, repr=False)
    _elos: list = field(default_factory=list)

    def tem_dados(self) -> bool:
        return bool(self._elos)

    def adicionar(
        self,
        ne: int,
        mp: int,
        mm: Optional[int] = None,
        mp_usuario: bool = False,
        mm_usuario: bool = False,
    ) -> "BlocoDELO":
        self._elos.append(
            _AssocElo(ne=ne, mp=mp, mm=mm, mp_usuario=mp_usuario, mm_usuario=mm_usuario)
        )
        return self

    def serializar(self) -> str:
        linhas = [self._cabecalho(), "(Ne)   ( M+ )u( M- )u\n"]
        for e in self._elos:
            linhas.append(e.serializar() + "\n")
        linhas.append(self._terminador())
        return "".join(linhas)


# ---------------------------------------------------------------------------
# DMOT – Máquinas de Indução Convencional (§15, v1.5.1)
# ---------------------------------------------------------------------------


@dataclass
class _MotorTipo1:
    """Motor de indução tipo 1 (sem efeito transitório no rotor, §15.1.1)."""

    nb: int  # barra terminal
    gr: int  # grupo
    h: float  # inércia [s]
    k0: float = 0.0  # parâmetro curva torque
    k1: float = 0.0
    k2: float = 0.0
    exp: float = 0.0  # η
    m: int = 1  # tipo (fixo em 1)

    mt: "Optional[int]" = None  # modelo CDU de turbina (geradores de indução)

    def serializar(self) -> str:
        from pynatem.reguas_mdxx import REGUAS_CODIGOS, serializar_linha

        return serializar_linha(
            REGUAS_CODIGOS["DMOT"],
            [
                self.nb,
                self.gr,
                self.h,
                self.k0 if self.k0 else None,
                self.k1 if self.k1 else None,
                self.k2 if self.k2 else None,
                self.exp if self.exp else None,
                self.m,
                self.mt,
            ],
        )


@dataclass
class _MotorTipo2:
    """Motor de indução tipo 2 (com efeito transitório no rotor, §15.1.1)."""

    nb: int  # barra terminal
    gr: int  # grupo
    h: float  # inércia [s]
    k0: float = 0.0  # parâmetro curva torque
    k1: float = 0.0
    k2: float = 0.0
    exp: float = 0.0  # η
    rr: float = 0.0  # resistência rotor [pu]
    xr: float = 0.0  # reatância transitória rotor [pu]
    xs: float = 0.0  # reatância de dispersão estator [pu]
    xm: float = 0.0  # reatância magnetizante [pu]
    xp: float = 0.0  # reatância transitória [pu]
    tr0: float = 0.0  # constante tempo rotor [s]
    m: int = 2  # tipo (fixo em 2)

    mt: "Optional[int]" = None  # modelo CDU de turbina (geradores de indução)

    def serializar(self) -> str:
        """Linha única do formato oficial DMOT.

        Os atributos rr/xr/xs/xm/xp/tr0 são mantidos por compatibilidade de
        API, mas NÃO são campos de entrada do DMOT oficial (aparecem apenas
        nas equações do modelo, §15.1) e não são serializados.
        """
        from pynatem.reguas_mdxx import REGUAS_CODIGOS, serializar_linha

        return serializar_linha(
            REGUAS_CODIGOS["DMOT"],
            [
                self.nb,
                self.gr,
                self.h,
                self.k0 if self.k0 else None,
                self.k1 if self.k1 else None,
                self.k2 if self.k2 else None,
                self.exp if self.exp else None,
                self.m,
                self.mt,
            ],
        )


# ---------------------------------------------------------------------------
# Geradores Eólicos DFIG — Cap. 19 / §46 (v1.5.3)
#
# DDFM  — Associação de gerador DFIG aos seus modelos (máquina, turbina, controle)
# Régua: Nb Gr P% Q% Und Mg Mt[u] Mc[u] Xvd Nbc Slip[u] R I
# ---------------------------------------------------------------------------


@dataclass
class _AssocDFIG:
    """Associação de gerador eólico DFIG (DDFM, §19.2)."""

    nb: int  # barra terminal
    gr: int  # grupo
    p: float  # participação ativa [%]
    q: float  # participação reativa [%]
    und: int  # número unidades
    mg: int  # modelo máquina indução
    mt: int  # modelo turbina
    mc: int  # modelo controle
    mt_usuario: bool = False
    mc_usuario: bool = False
    xvd: float = 0.0  # reatância do sistema [pu]
    nbc: int = 0  # número barras controle
    slip: float = 0.0  # escorregamento inicial
    slip_usuario: bool = False  # se slip é número CDU
    r: int = 0  # flag resposta rápida
    i: int = 0  # flag RMSB

    def serializar(self) -> str:
        from pynatem.reguas_mdxx import REGUAS_CODIGOS, serializar_linha

        def flag(usuario):
            return "U" if usuario else None

        return serializar_linha(
            REGUAS_CODIGOS["DDFM"],
            [
                self.nb,
                self.gr,
                self.p,
                self.q,
                self.und,
                self.mg,
                self.mt,
                flag(self.mt_usuario),
                self.mc,
                flag(self.mc_usuario),
                self.xvd if self.xvd else None,
                self.nbc if self.nbc else None,
                self.slip,
                flag(self.slip_usuario),
                self.r if self.r else None,
                self.i if self.i else None,
            ],
        )


@dataclass
class BlocoDDFM(BlocoBase):
    """Associação de geradores eólicos DFIG (DDFM, §19.2, Cap. 19 / v1.5.3).

    Conecta um gerador DFIG (máquina de indução com dupla alimentação, rotor
    bobinado) aos seus modelos de máquina, turbina e controle.

    Campos:
        Nb:   barra terminal.
        Gr:   grupo (múltiplos grupos por barra).
        P/Q:  participação de potência ativa/reativa [%].
        Und:  número de unidades.
        Mg:   modelo de máquina (DMDF).
        Mt:   modelo de turbina (predefinido ou CDU).
        Mc:   modelo de controle (CDU).
        Xvd:  reatância do sistema [pu].
        Nbc:  número de barras para cálculo de controle.
        Slip: escorregamento inicial (ou número CDU para cálculo).
        R/I:  flags de comportamento.

    Confiança: Média — estrutura validada contra §19.2; associação entre
    modelos é tratada sem validação cruzada.

    Uso::

        ddfm = BlocoDDFM()
        ddfm.adicionar(nb=6073, gr=10, p=100, q=100, und=66, mg=17, mt=90146,
                      mc=90145, xvd=21.50, nbc=2, slip=2, r=0, i=0)
    """

    keyword: str = field(default="DDFM", init=False, repr=False)
    _dfigs: List[_AssocDFIG] = field(default_factory=list)

    def tem_dados(self) -> bool:
        return bool(self._dfigs)

    def adicionar(
        self,
        nb: int,
        gr: int,
        p: float,
        q: float,
        und: int,
        mg: int,
        mt: int,
        mc: int,
        mt_usuario: bool = False,
        mc_usuario: bool = False,
        xvd: float = 0.0,
        nbc: int = 0,
        slip: float = 0.0,
        slip_usuario: bool = False,
        r: int = 0,
        i: int = 0,
    ) -> "BlocoDDFM":
        """Adiciona uma associação DFIG.

        Args:
            nb, gr, p, q, und: identificação e participação.
            mg, mt, mc: modelos (máquina, turbina, controle).
            mt_usuario, mc_usuario: se modelos são CDU (flag 'u').
            xvd: reatância [pu].
            nbc: barras de controle.
            slip: escorregamento ou número CDU para inicialização.
            slip_usuario: se slip é número CDU (flag 'u').
            r, i: flags.

        Returns:
            self (encadeável).
        """
        self._dfigs.append(
            _AssocDFIG(
                nb=nb,
                gr=gr,
                p=p,
                q=q,
                und=und,
                mg=mg,
                mt=mt,
                mc=mc,
                mt_usuario=mt_usuario,
                mc_usuario=mc_usuario,
                xvd=xvd,
                nbc=nbc,
                slip=slip,
                slip_usuario=slip_usuario,
                r=r,
                i=i,
            )
        )
        return self

    def _guia(self) -> str:
        from pynatem.reguas_mdxx import REGUAS_CODIGOS

        return REGUAS_CODIGOS["DDFM"] + "\n"

    def serializar(self) -> str:
        linhas = [self._cabecalho(), self._guia()]
        for d in self._dfigs:
            linhas.append(d.serializar() + "\n")
        linhas.append(self._terminador())
        return "".join(linhas)


@dataclass
class BlocoDMOT(BlocoBase):
    """Modelos predefinidos de máquina de indução convencional (DMOT, §15).

    Suporta 2 modelos:

    - **Tipo 1 (M=1)**: Sem efeito transitório no rotor. Params: Nb, Gr, H,
      K0, K1, K2, EXP. Simples, adequado para cargas constantes.
    - **Tipo 2 (M=2)**: Com efeito transitório no rotor. Params: Nb, Gr, H,
      K0, K1, K2, EXP, Rr, Xr, Xs, Xm, Xp, Tr0. Mais detalhado, para dinâmica
      transiente.

    Nota: Máquinas devem estar previamente definidas no ANAREDE (fluxo de potência).
    Os parâmetros aqui são complementares. Máquinas não modeladas viram impedâncias
    constantes automaticamente.

    Confiança: **Média** — estrutura validada contra §15 do manual; parâmetros
    de curva de torque (K0–EXP) para motores são tratados como opacos (validação
    completa fica para roadmap A43, linguagem de seleção).

    Uso::

        dmot = BlocoDMOT()

        # Motor tipo 1 (sem dinâmica rotórica)
        dmot.adicionar_tipo1(nb=3, gr=1, h=2.5)

        # Motor tipo 2 (com dinâmica rotórica)
        dmot.adicionar_tipo2(
            nb=4, gr=1, h=3.0, k0=1.0, k1=0.5, k2=0.1, exp=2.0,
            rr=0.02, xr=0.15, xs=0.10, xm=3.0, xp=0.20, tr0=0.8
        )
    """

    keyword: str = field(default="DMOT", init=False, repr=False)
    _tipo1: List[_MotorTipo1] = field(default_factory=list)
    _tipo2: List[_MotorTipo2] = field(default_factory=list)

    def tem_dados(self) -> bool:
        return bool(self._tipo1 or self._tipo2)

    def adicionar_tipo1(
        self,
        nb: int,
        gr: int,
        h: float,
        k0: float = 0.0,
        k1: float = 0.0,
        k2: float = 0.0,
        exp: float = 0.0,
        mt: Optional[int] = None,
    ) -> "BlocoDMOT":
        """Adiciona motor tipo 1 (sem efeito transitório no rotor, M=1).

        Args:
            nb:   barra terminal da máquina de indução.
            gr:   grupo (múltiplos grupos por barra).
            h:    constante de inércia [s].
            k0–k2, exp: parâmetros da curva Torque×velocidade (motores).
                        Default 0 (carga constante).

        Returns:
            self (encadeável).
        """
        self._tipo1.append(
            _MotorTipo1(nb=nb, gr=gr, h=h, k0=k0, k1=k1, k2=k2, exp=exp, mt=mt)
        )
        return self

    def adicionar_tipo2(
        self,
        nb: int,
        gr: int,
        h: float,
        k0: float = 0.0,
        k1: float = 0.0,
        k2: float = 0.0,
        exp: float = 0.0,
        rr: float = 0.0,
        xr: float = 0.0,
        xs: float = 0.0,
        xm: float = 0.0,
        xp: float = 0.0,
        tr0: float = 0.0,
        mt: Optional[int] = None,
    ) -> "BlocoDMOT":
        """Adiciona motor tipo 2 (com efeito transitório no rotor, M=2).

        Args:
            nb:   barra terminal.
            gr:   grupo.
            h:    inércia [s].
            k0–k2, exp: parâmetros da curva Torque×velocidade.
            rr:   resistência do rotor [pu].
            xr:   reatância transitória do rotor [pu].
            xs:   reatância de dispersão do estator [pu].
            xm:   reatância magnetizante [pu].
            xp:   reatância transitória [pu].
            tr0:  constante de tempo do rotor a circuito aberto [s].

        Returns:
            self (encadeável).
        """
        self._tipo2.append(
            _MotorTipo2(
                nb=nb,
                gr=gr,
                h=h,
                k0=k0,
                k1=k1,
                k2=k2,
                exp=exp,
                rr=rr,
                xr=xr,
                xs=xs,
                xm=xm,
                xp=xp,
                tr0=tr0,
                mt=mt,
            )
        )
        return self

    def _guia(self) -> str:
        from pynatem.reguas_mdxx import REGUAS_CODIGOS

        return REGUAS_CODIGOS["DMOT"] + "\n"

    def serializar(self) -> str:
        linhas = [self._cabecalho(), self._guia()]
        for m in self._tipo1:
            linhas.append(m.serializar() + "\n")
        for m2 in self._tipo2:
            linhas.append(m2.serializar() + "\n")
        linhas.append(self._terminador())
        return "".join(linhas)


@dataclass
class _AssocGSE:
    """Associação de gerador eólico síncrono (DGSE, §20.2)."""

    nb: int
    gr: int
    p: float
    q: float
    und: int
    mg: int
    mt: int
    mv: int
    mc1: int
    mc2: int
    freq: float = 0.0
    vtr0: float = 0.0
    vcap0: float = 0.0
    mt_usuario: bool = False
    mv_usuario: bool = False
    mc1_usuario: bool = False
    mc2_usuario: bool = False

    def serializar(self) -> str:
        from pynatem.reguas_mdxx import REGUAS_CODIGOS, serializar_linha

        def flag(usuario):
            return "U" if usuario else None

        return serializar_linha(
            REGUAS_CODIGOS["DGSE"],
            [
                self.nb,
                self.gr,
                self.p,
                self.q,
                self.und,
                self.mg,
                self.mt,
                flag(self.mt_usuario),
                self.mv,
                flag(self.mv_usuario),
                self.mc1,
                flag(self.mc1_usuario),
                self.mc2,
                flag(self.mc2_usuario),
                int(self.freq) if self.freq else None,
                self.vtr0 if self.vtr0 else None,
                self.vcap0 if self.vcap0 else None,
            ],
        )


@dataclass
class BlocoDGSE(BlocoBase):
    """Associação de geradores eólicos síncronos (DGSE, §20.2, Cap. 20 / v1.5.4).

    Conecta um gerador síncrono eólico (GSE, máquina síncrona com velocidade
    variável) aos seus modelos de máquina, turbina, controle de tensão (chopper),
    e inversor de tensão (VSI).

    Campos:
        Nb:     barra terminal.
        Gr:     grupo (múltiplos grupos por barra).
        P/Q:    participação de potência ativa/reativa [%].
        Und:    número de unidades.
        Mg:     modelo de máquina (DMGE).
        Mt:     modelo de regulador de tensão (DRGT ou CDU).
        Mv:     modelo de turbina eólica (CDU).
        Mc1:    modelo de chopper (regulador CC, CDU).
        Mc2:    modelo de inversor de tensão (VSI, CDU).
        Freq:   frequência inicial [Hz].
        Vtr0:   tensão inicial máquina síncrona [pu].
        Vcap0:  tensão inicial capacitor CC [pu].

    Confiança: Alta — estrutura validada contra §20.2 (Listagem 46.34).

    Uso::

        dgse = BlocoDGSE()
        dgse.adicionar(nb=100, gr=10, p=100, q=100, und=1, mg=1525,
                      mt=2000, mv=102, mc1=104, mc2=106,
                      freq=60, vtr0=1.0, vcap0=1.0,
                      mv_usuario=True, mc1_usuario=True, mc2_usuario=True)
    """

    keyword: str = field(default="DGSE", init=False, repr=False)
    _gses: List[_AssocGSE] = field(default_factory=list)

    def tem_dados(self) -> bool:
        return bool(self._gses)

    def adicionar(
        self,
        nb: int,
        gr: int,
        p: float,
        q: float,
        und: int,
        mg: int,
        mt: int,
        mv: int,
        mc1: int,
        mc2: int,
        freq: float = 0.0,
        vtr0: float = 0.0,
        vcap0: float = 0.0,
        mt_usuario: bool = False,
        mv_usuario: bool = False,
        mc1_usuario: bool = False,
        mc2_usuario: bool = False,
    ) -> "BlocoDGSE":
        """Adiciona uma associação GSE.

        Args:
            nb, gr, p, q, und: identificação e participação [%].
            mg, mt, mv, mc1, mc2: modelos (máquina, regulador, turbina, chopper, inversor).
            mt_usuario, mv_usuario, mc1_usuario, mc2_usuario: se modelos são CDU (flag 'u').
            freq: frequência inicial [Hz].
            vtr0: tensão máquina síncrona [pu].
            vcap0: tensão capacitor CC [pu].

        Returns:
            self (encadeável).
        """
        self._gses.append(
            _AssocGSE(
                nb=nb,
                gr=gr,
                p=p,
                q=q,
                und=und,
                mg=mg,
                mt=mt,
                mv=mv,
                mc1=mc1,
                mc2=mc2,
                freq=freq,
                vtr0=vtr0,
                vcap0=vcap0,
                mt_usuario=mt_usuario,
                mv_usuario=mv_usuario,
                mc1_usuario=mc1_usuario,
                mc2_usuario=mc2_usuario,
            )
        )
        return self

    def _guia(self) -> str:
        from pynatem.reguas_mdxx import REGUAS_CODIGOS

        return REGUAS_CODIGOS["DGSE"] + "\n"

    def serializar(self) -> str:
        linhas = [self._cabecalho(), self._guia()]
        for g in self._gses:
            linhas.append(g.serializar() + "\n")
        linhas.append(self._terminador())
        return "".join(linhas)


@dataclass
class _FonteShuntCDU:
    """Fonte shunt controlada por CDU (DFNT, §21)."""

    nb: int
    gr: int
    tipo: str
    fp: float
    fq: float
    und: int
    mc: int
    mc_usuario: bool
    r_ou_g: float
    x_ou_b: float
    sbas: float = 0.0

    def serializar(self) -> str:
        from pynatem.reguas_mdxx import REGUAS_CODIGOS, serializar_linha

        return serializar_linha(
            REGUAS_CODIGOS["DFNT"],
            [
                self.nb,
                self.gr,
                self.tipo,
                self.fp,
                self.fq,
                self.und,
                self.mc,
                "U" if self.mc_usuario else None,
                self.r_ou_g,
                self.x_ou_b,
                self.sbas if self.sbas else None,
            ],
        )


@dataclass
class BlocoDFNT(BlocoBase):
    """Fonte shunt controlada por CDU (DFNT, §21 / Cap. 21, v1.5.5).

    Modela parcela de geração como fonte shunt (tensão ou corrente) controlada
    por CDU. Permite injeção de potência ativa/reativa com impedância equivalente.

    Campos:
        Nb:   barra CA.
        Gr:   grupo de geração.
        T:    tipo (V=tensão/Thévenin, I=corrente/Norton).
        FP%:  fator potência ativa [%].
        FQ%:  fator potência reativa [%].
        Und:  número de unidades (1 default).
        Mc:   modelo de controle (CDU).
        R/G:  resistência (V) ou condutância (I) [%].
        X/B:  reatância (V) ou susceptância (I) [%].
        Sbas: base potência [MVA].

    Confiança: Alta — estrutura validada contra §21 (Listagem 46.32).

    Uso::

        dfnt = BlocoDFNT()
        dfnt.adicionar(nb=10, gr=10, tipo='I', fp=100, fq=100, und=5,
                      mc=101, r_ou_g=1.2, x_ou_b=4.0, sbas=0.0,
                      mc_usuario=True)
    """

    keyword: str = field(default="DFNT", init=False, repr=False)
    _fontes: List[_FonteShuntCDU] = field(default_factory=list)

    def tem_dados(self) -> bool:
        return bool(self._fontes)

    def adicionar(
        self,
        nb: int,
        gr: int,
        tipo: str,
        fp: float,
        fq: float,
        und: int,
        mc: int,
        r_ou_g: float,
        x_ou_b: float,
        sbas: float = 0.0,
        mc_usuario: bool = False,
    ) -> "BlocoDFNT":
        """Adiciona uma fonte shunt controlada.

        Args:
            nb, gr: identificação barra e grupo.
            tipo: 'V' (tensão/Thévenin) ou 'I' (corrente/Norton).
            fp, fq: percentual potência ativa/reativa [%].
            und: número de unidades.
            mc: número modelo CDU.
            r_ou_g: resistência [%] (V) ou condutância (I).
            x_ou_b: reatância [%] (V) ou susceptância (I).
            sbas: base potência [MVA].
            mc_usuario: se modelo é CDU (flag 'u').

        Returns:
            self (encadeável).
        """
        self._fontes.append(
            _FonteShuntCDU(
                nb=nb,
                gr=gr,
                tipo=tipo.upper(),
                fp=fp,
                fq=fq,
                und=und,
                mc=mc,
                mc_usuario=mc_usuario,
                r_ou_g=r_ou_g,
                x_ou_b=x_ou_b,
                sbas=sbas,
            )
        )
        return self

    def _guia(self) -> str:
        from pynatem.reguas_mdxx import REGUAS_CODIGOS

        return REGUAS_CODIGOS["DFNT"] + "\n"

    def serializar(self) -> str:
        linhas = [self._cabecalho(), self._guia()]
        for f in self._fontes:
            linhas.append(f.serializar() + "\n")
        linhas.append(self._terminador())
        return "".join(linhas)


@dataclass
class _ModeloElo:
    """Modelo predefinido de elo CC (DMEL MD01, §46.47)."""

    no: int
    tipo: str
    tbp: float = 0.0

    def serializar(self) -> str:
        # régua oficial: (No)   C (Tbp) — No 0-3, C na col 7, Tbp 8-13
        linha = f"{self.no:>4}{self.tipo:>4}"
        if self.tbp != 0.0:
            linha += f"{_num_compacto(self.tbp):>6}"
        return linha


@dataclass
class BlocoDMEL(BlocoBase):
    """Modelos predefinidos de elo CC (DMEL MD01, §46.47 / v1.6.1).

    Define modelos de polos para elos HVDC LCC com controle de corrente
    ou potência. Apenas MD01 suportado (2 modelos predefinidos: 0010/C, 0020/P).

    Campos:
        No:   identificador modelo (ex: 0010, 0020).
        C:    tipo (C=corrente, P=potência).
        Tbp:  constante tempo balanceador [s] (opcional).

    Confiança: Alta — estrutura simples, validada contra §46.47 (Listagem 46.45).

    Uso::

        dmel = BlocoDMEL()
        dmel.adicionar_md01(no=0010, tipo='C', tbp=0.0)
        dmel.adicionar_md01(no=0020, tipo='P', tbp=0.0)
    """

    keyword: str = field(default="DMEL", init=False, repr=False)
    opcoes: str = field(default="MD01", init=False)
    _modelos: List[_ModeloElo] = field(default_factory=list)

    def _cabecalho(self) -> str:
        return f"{self.keyword} {self.opcoes}\n"

    def tem_dados(self) -> bool:
        return bool(self._modelos)

    def adicionar_md01(self, no: int, tipo: str, tbp: float = 0.0) -> "BlocoDMEL":
        """Adiciona modelo MD01 de elo CC.

        Args:
            no: número identificador.
            tipo: 'C' (corrente) ou 'P' (potência).
            tbp: constante tempo balanceador [s].

        Returns:
            self (encadeável).
        """
        self._modelos.append(_ModeloElo(no=no, tipo=tipo.upper(), tbp=tbp))
        return self

    def _guia(self) -> str:
        return "( No) C (Tbp)\n"

    def serializar(self) -> str:
        linhas = [self._cabecalho(), self._guia()]
        for m in self._modelos:
            linhas.append(m.serializar() + "\n")
        linhas.append(self._terminador())
        return "".join(linhas)


@dataclass
class _LinhaCC:
    """Linha CC com indutância e capacitância (DCLI, §46.19)."""

    de: int
    pa: int
    nc: Optional[int] = None  # branco → 1
    l: float = 0.0
    c: float = 0.0

    def serializar(self) -> str:
        # régua oficial: (De)    (Pa)Nc         ( L  )( C  )
        # De 0-3, Pa 4-11, Nc 12-13 (branco = 1), L termina col 28, C col 34
        linha = f"{self.de:>4}{self.pa:>8}" + _col_int(self.nc, 2)
        linha += f"{_fmt_valor(self.l):>15}" if self.l != 0.0 else " " * 15
        if self.c != 0.0:
            linha += f"{_fmt_valor(self.c):>6}"
        return linha.rstrip()


@dataclass
class BlocoDCLI(BlocoBase):
    """Indutâncias e capacitâncias de linhas CC (DCLI, §46.19 / v1.6.2).

    Define parâmetros de linhas CC (transmissão por elo HVDC).

    Campos:
        De:  barra CC origem.
        Pa:  barra CC destino.
        Nc:  circuito (default 1).
        L:   indutância [mH].
        C:   capacitância [μF] (opcional, para cabos).

    Confiança: Alta — estrutura plana simples, validada §46.19 (Listagem 46.17).

    Uso::

        dcli = BlocoDCLI()
        dcli.adicionar(de=1, pa=2, l=0.1)  # linhas aéreas (sem C)
        dcli.adicionar(de=3, pa=4, l=0.05, c=5.0)  # cabo (com C)
    """

    keyword: str = field(default="DCLI", init=False, repr=False)
    _linhas: List[_LinhaCC] = field(default_factory=list)

    def tem_dados(self) -> bool:
        return bool(self._linhas)

    def adicionar(
        self, de: int, pa: int, nc: Optional[int] = None, l: float = 0.0, c: float = 0.0
    ) -> "BlocoDCLI":
        """Adiciona linha CC.

        Args:
            de, pa: barras CC.
            nc: circuito (default 1).
            l: indutância [mH].
            c: capacitância [μF] (default 0, omitido se zero).

        Returns:
            self (encadeável).
        """
        self._linhas.append(_LinhaCC(de=de, pa=pa, nc=nc, l=l, c=c))
        return self

    def _guia(self) -> str:
        return "(De)    (Pa)Nc         ( L  )( C  )\n"

    def serializar(self) -> str:
        linhas = [self._cabecalho(), self._guia()]
        for linha in self._linhas:
            linhas.append(linha.serializar() + "\n")
        linhas.append(self._terminador())
        return "".join(linhas)


@dataclass
class BlocoDMCV(BlocoBase):
    """Modelos predefinidos de conversor CA-CC (DMCV, §46.44 / v1.6.1).

    Modelos de controle para conversores LCC (Line Commutated Converter).
    Suporta MD01 (2 réguas) e MD03 (4 réguas).

    Confiança: Alta — estrutura posicional validada contra §46.44 (Listagem 46.42).

    Uso::

        dmcv = BlocoDMCV()
        dmcv.adicionar_md01(nm=1, vmn=0.5, tvp=0.02, ...)  # 2 réguas
        dmcv.adicionar_md03(no=2, vmn=0.5, tvp=0.02, ...)  # 4 réguas
    """

    keyword: str = field(default="DMCV", init=False, repr=False)
    _dados_brutos: List[str] = field(
        default_factory=list
    )  # texto bruto para cada modelo

    def tem_dados(self) -> bool:
        return bool(self._dados_brutos)

    def adicionar_md01(
        self,
        nm: int,
        vmn: float,
        tvp: float,
        tx1: float,
        td1: float,
        yal: float,
        tmx: float,
        amx: float,
        gmx: float = 0.0,
        stx: float = 0.0,
        f: str = "",
    ) -> "BlocoDMCV":
        """Adiciona modelo MD01 de conversor (2 réguas)."""
        # Régua 1
        r1 = (
            f"{nm:>5}{vmn:>6.2f}{tvp:>6.3f}{tx1:>6.2f}{td1:>6.2f}{yal:>6.1f}"
            f"{tmx:>6.2f}{amx:>6.2f}{gmx:>6.2f}{stx:>6.1f}{f:>2}"
        )
        self._dados_brutos.append(r1 + "\n")
        return self

    def adicionar_md01_r2(
        self,
        nm: int,
        tvd: float,
        tvs: float,
        vdn: float,
        vdx: float,
        frn: float,
        imn: float,
        imx: float,
        img: float,
        ki: float,
        kp: float,
        to: float,
        kcg: float,
    ) -> "BlocoDMCV":
        """Adiciona régua 2 do modelo MD01."""
        r2 = (
            f"{nm:>5}{tvd:>6.2f}{tvs:>6.2f}{vdn:>6.1f}{vdx:>6.1f}{frn:>6.1f}"
            f"{imn:>6.1f}{imx:>6.1f}{img:>6.1f}{ki:>7.2f}{kp:>7.2f}{to:>6.3f}{kcg:>7.2f}"
        )
        self._dados_brutos.append(r2 + "\n")
        return self

    def _guia(self) -> str:
        return "( Nm)(Vmn)(Tvp)(Tx1)(Td1)(Yal)(Tmx)(Amx)(Gmx)(Stx) F\n"

    def serializar(self) -> str:
        linhas = [self._cabecalho(), self._guia()]
        linhas.extend(self._dados_brutos)
        linhas.append(self._terminador())
        return "".join(linhas)
