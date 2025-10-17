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
  - OLTC, FACTS (CER/SVC, TCSC, STATCOM) e HVDC: códigos "best-effort",
    seguindo o padrão de nomenclatura de 4 letras do ANATEM, mas SEM
    confirmação verbatim do manual (fetch de página específica não
    disponível). Confira o código exato do seu equipamento antes de uso
    em produção — use `linha_bruta()` como alternativa segura se preferir.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

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
    freq: Optional[float] = None
    base_mva: Optional[float] = None
    opcoes_extras: List[str] = field(default_factory=list)

    def tem_dados(self) -> bool:
        return bool(self.freq or self.base_mva or self.opcoes_extras)

    def serializar(self) -> str:
        linhas = [self._cabecalho()]
        if self.freq is not None:
            linhas.append(f"FREQ  {self.freq:.1f}\n")
        if self.base_mva is not None:
            linhas.append(f"BASE  {self.base_mva:.1f}\n")
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

    Atributos:
        tini  – tempo inicial [s] (padrão 0.0)
        tfim  – tempo final   [s] (padrão 10.0)
        delt  – passo de integração [s] (padrão 0.01)
        npas  – passos entre gravações de plotagem
        mxit  – máximo de iterações Newton por passo
    """

    keyword: str = field(default="DSIM", init=False, repr=False)
    tini: float = 0.0
    tfim: float = 10.0
    delt: float = 0.01
    npas: Optional[int] = None
    mxit: Optional[int] = None

    def serializar(self) -> str:
        linhas = [self._cabecalho()]
        linhas.append(f"{self.tini:10.4f}{self.tfim:10.4f}{self.delt:10.4f}\n")
        if self.npas is not None:
            linhas.append(f"NPAS  {self.npas}\n")
        if self.mxit is not None:
            linhas.append(f"MXIT  {self.mxit}\n")
        linhas.append(self._terminador())
        return "".join(linhas)


# ---------------------------------------------------------------------------
# DEVT – Eventos da simulação  (manual §46.31, pág. 722)
# ---------------------------------------------------------------------------


@dataclass
class _Evento:
    """Representa uma linha de evento DEVT."""

    codigo: str
    nb1: int
    nb2: int = 0
    nc: int = 0
    tini: float = 0.0
    p1: float = 0.0
    p2: float = 0.0

    def serializar(self) -> str:
        cod = f"{self.codigo:<4}"
        if self.nb2 or self.nc:
            return (
                f"{cod}  {self.nb1:>5}  {self.nb2:>5}  {self.nc:>3}"
                f"  {self.tini:>10.4f}  {self.p1:>10.4f}  {self.p2:>10.4f}"
            )
        else:
            return (
                f"{cod}  {self.nb1:>5}" f"  {self.tini:>10.4f}  {self.p1:>10.4f}  {self.p2:>10.4f}"
            )


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
        self, barra: int, tini: float, tipo: str = "APCB", r: float = 0.0, x: float = 0.0
    ) -> "BlocoDEVT":
        """Aplica (APCB) ou remove (RMCB) curto-circuito em barra CA."""
        self._eventos.append(_Evento(codigo=tipo, nb1=barra, tini=tini, p1=r, p2=x))
        return self

    def curto_circuito(
        self,
        de: int,
        para: int,
        circ: int,
        tini: float,
        tipo: str = "APCC",
        r: float = 0.0,
        x: float = 0.0,
    ) -> "BlocoDEVT":
        """Aplica (APCC) ou remove (RMCC) curto-circuito em circuito CA."""
        self._eventos.append(_Evento(codigo=tipo, nb1=de, nb2=para, nc=circ, tini=tini, p1=r, p2=x))
        return self

    def abertura_linha(self, de: int, para: int, tini: float, circ: int = 1) -> "BlocoDEVT":
        """Abre um circuito CA (ABLN)."""
        self._eventos.append(_Evento(codigo="ABLN", nb1=de, nb2=para, nc=circ, tini=tini))
        return self

    def fechamento_linha(self, de: int, para: int, tini: float, circ: int = 1) -> "BlocoDEVT":
        """Fecha um circuito CA (FCLN)."""
        self._eventos.append(_Evento(codigo="FCLN", nb1=de, nb2=para, nc=circ, tini=tini))
        return self

    def abertura_shunt(self, barra: int, tini: float) -> "BlocoDEVT":
        """Abre banco shunt (ABSH)."""
        self._eventos.append(_Evento(codigo="ABSH", nb1=barra, tini=tini))
        return self

    def fechamento_shunt(self, barra: int, tini: float) -> "BlocoDEVT":
        """Fecha banco shunt (FCSH)."""
        self._eventos.append(_Evento(codigo="FCSH", nb1=barra, tini=tini))
        return self

    def step_referencia(
        self, barra: int, unidade: int, tini: float, delta: float, tipo: str = "ALTG"
    ) -> "BlocoDEVT":
        """Step em sinal de referência de máquina (ALTG)."""
        self._eventos.append(_Evento(codigo=tipo, nb1=barra, nb2=unidade, tini=tini, p1=delta))
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

    # -- OLTC (best-effort, ver nota de confiança no topo do módulo) --------

    def tap_oltc(self, de: int, para: int, circ: int = 1) -> "BlocoDPLT":
        """Posição do tap de transformador OLTC.

        Código best-effort ('TAPO'); confira no manual (cap. 14) antes
        de uso em produção.
        """
        return self._add("TAPO", de, para, circ)

    # -- FACTS: CER/SVC (best-effort) ---------------------------------------

    def reativo_svc(self, num: int) -> "BlocoDPLT":
        """Potência reativa injetada pelo CER/SVC [pu ou Mvar] (best-effort)."""
        return self._add("QSVC", num)

    def tensao_svc(self, num: int) -> "BlocoDPLT":
        """Tensão controlada pelo CER/SVC [pu] (best-effort)."""
        return self._add("VSVC", num)

    def susceptancia_svc(self, num: int) -> "BlocoDPLT":
        """Susceptância equivalente do CER/SVC [pu] (best-effort)."""
        return self._add("BSVC", num)

    # -- FACTS: TCSC (best-effort) -------------------------------------------

    def reatancia_tcsc(self, de: int, para: int, circ: int = 1) -> "BlocoDPLT":
        """Reatância inserida pelo TCSC [pu] (best-effort)."""
        return self._add("XTCS", de, para, circ)

    def potencia_tcsc(self, de: int, para: int, circ: int = 1) -> "BlocoDPLT":
        """Fluxo de potência ativa através do TCSC [pu] (best-effort)."""
        return self._add("PTCS", de, para, circ)

    # -- FACTS VSI: STATCOM/SSSC/UPFC (best-effort) --------------------------

    def reativo_statcom(self, num: int) -> "BlocoDPLT":
        """Potência reativa do STATCOM [pu ou Mvar] (best-effort)."""
        return self._add("QSTA", num)

    def tensao_statcom(self, num: int) -> "BlocoDPLT":
        """Tensão controlada pelo STATCOM [pu] (best-effort)."""
        return self._add("VSTA", num)

    # -- HVDC (best-effort) ---------------------------------------------------

    def tensao_cc(self, polo: int) -> "BlocoDPLT":
        """Tensão CC do elo/polo HVDC [pu ou kV] (best-effort)."""
        return self._add("VCCD", polo)

    def corrente_cc(self, polo: int) -> "BlocoDPLT":
        """Corrente CC do elo/polo HVDC [pu ou kA] (best-effort)."""
        return self._add("ICCD", polo)

    def potencia_cc(self, polo: int) -> "BlocoDPLT":
        """Potência transmitida pelo elo/polo HVDC [pu ou MW] (best-effort)."""
        return self._add("PCCD", polo)

    def angulo_disparo(self, polo: int) -> "BlocoDPLT":
        """Ângulo de disparo do retificador, alfa [graus] (best-effort)."""
        return self._add("ALFA", polo)

    def angulo_extincao(self, polo: int) -> "BlocoDPLT":
        """Ângulo de extinção do inversor, gama [graus] (best-effort)."""
        return self._add("GAMA", polo)

    # -- CDU: saída de bloco de controlador ----------------------------------

    def saida_cdu(self, num_cdu: int, num_bloco: int) -> "BlocoDPLT":
        """Saída de um bloco específico dentro de um CDU numerado (best-effort).

        Args:
            num_cdu:   número do controlador CDU.
            num_bloco: número do bloco dentro do CDU (saída a plotar).
        """
        return self._add("SCDU", num_cdu, num_bloco)

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

        Layout (posições relativas ao início da linha de dados):
            Nb  : 6 chars  right-aligned
            Gr  : 4 chars  right-aligned
            P   : 4 chars  right-aligned  (espaços se omitido)
            Q   : 4 chars  right-aligned  (espaços se omitido)
            Und : 4 chars  right-aligned  (espaços se omitido)
            Mg  : 6 chars  right-aligned  (espaços se omitido)
            Mt  : 6 chars  right-aligned  (espaços se omitido)
            u   : 1 char   'u' se CDU, ' ' caso contrário
            Mv  : 6 chars  right-aligned  (espaços se omitido)
            u   : 1 char   'u' se CDU, ' ' caso contrário
            Me  : 6 chars  right-aligned  (espaços se omitido)
            u   : 1 char   'u' se CDU, ' ' caso contrário
            Xvd : 8 chars  float 4 casas  (espaços se omitido)
            Nbc : 6 chars  right-aligned  (espaços se omitido)

        Campos opcionais ausentes são emitidos como espaços em branco na
        posição correta, garantindo que campos posteriores não se desloquem.
        """
        if self.texto_bruto is not None:
            return self.texto_bruto
        fi = self._fi
        ff = self._ff
        fu = self._fu
        linha = (
            fi(self.barra, 6)
            + fi(self.grupo, 4)
            + fi(self.p, 4)
            + fi(self.q, 4)
            + fi(self.und, 4)
            + fi(self.mg, 6)
            + fi(self.mt, 6)
            + fu(self.mt_cdu)
            + fi(self.mv, 6)
            + fu(self.mv_cdu)
            + fi(self.me, 6)
            + fu(self.me_cdu)
            + ff(self.xvd, 8)
            + fi(self.nbc, 6)
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
        self, barra: int, unidade: int, modelo: str, params: Optional[List[float]] = None
    ) -> "BlocoDMAQ":
        """API legada (retrocompatibilidade) — preserva texto bruto."""
        base = f"{barra:>6}  {unidade:>4}  {modelo:<8}"
        if params:
            base += "  " + "  ".join(f"{p:>10.4f}" for p in params)
        self.associacoes.append(_AssocMaquina(barra=barra, grupo=unidade, texto_bruto=base))
        return self

    def serializar(self) -> str:
        """Serializa o bloco DMAQ.

        A segunda linha emitida (``( Nb)  Gr   P   Q  Und ...``) é uma **legenda
        funcional**: nomeia os campos na ordem em que são emitidos, servindo de
        referência de leitura no deck. Ela **não** é uma régua de colunas — os
        rótulos coincidem com as posições reais apenas até ``Mg`` e derivam a
        partir de ``Mt`` porque a legenda omite os três flags CDU de 1 caractere
        (após Mt/Mv/Me). As posições verdadeiras são as fatias de largura fixa
        definidas em :meth:`_AssocMaquina.serializar` e no parser posicional
        (§46.41). Ver CHANGELOG v0.11.2.
        """
        linhas = [self._cabecalho()]
        linhas.append("( Nb)  Gr   P   Q  Und    Mg      Mt        Mv        Me     Xvd    Nbc\n")
        for a in self.associacoes:
            linhas.append(a.serializar() + "\n")
        linhas.append(self._terminador())
        return "".join(linhas)


# ---------------------------------------------------------------------------
# EXSI – Executa simulação  (manual §46.68, pág. 836)
# ---------------------------------------------------------------------------


class BlocoEXSI(BlocoBase):
    """Comando de execução do caso (EXSI)."""

    keyword = "EXSI"

    def serializar(self) -> str:
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
        fr_str = f"{self.fr:.1f}" if self.fr != 60.0 else ""
        c_str = self.corfreq if self.corfreq.upper() == "S" else ""
        linha = (
            f"{self.no:>4}  {self.ld:>6.3f}{self.ra:>6.3f}"
            f"{self.h:>7.3f}{self.d:>6.3f}{self.mva:>8.1f}"
        )
        if fr_str:
            linha += f"  {fr_str}"
        if c_str:
            linha += f"  {c_str}"
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
        cs_str = f"{self.cs:>4}"  # sempre emite (0 inclusive) — evita deslocamento de colunas
        # régua 1
        r1 = (
            f"{self.no:>4}  {cs_str}"
            f"  {self.ld:>7.3f} {self.lq:>7.3f} {self.ld_trans:>7.3f}"
            f" {self.ld_sub:>7.3f} {self.ll:>7.3f}"
            f"  {self.td_trans:>7.4f}  {self.td_sub:>7.4f} {self.tq_sub:>7.4f}"
        )
        # régua 2
        fr_str = f"  {self.fr:.1f}" if self.fr != 60.0 else ""
        c_str = f"  {self.corfreq}" if self.corfreq.upper() == "S" else ""
        r2 = (
            f"{self.no:>4}  {self.ra:>6.3f}"
            f"  {self.h:>7.3f}{self.d:>6.3f}{self.mva:>8.1f}"
            f"{fr_str}{c_str}"
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
        cs_str = f"{self.cs:>4}"  # sempre emite (0 inclusive)
        r1 = (
            f"{self.no:>4}  {cs_str}"
            f"  {self.ld:>7.3f} {self.lq:>7.3f}"
            f" {self.ld_trans:>7.3f} {self.lq_trans:>7.3f}"
            f" {self.ld_sub:>7.3f} {self.ll:>7.3f}"
            f"  {self.td_trans:>7.4f} {self.tq_trans:>7.4f}"
            f"  {self.td_sub:>7.4f} {self.tq_sub:>7.4f}"
        )
        fr_str = f"  {self.fr:.1f}" if self.fr != 60.0 else ""
        c_str = f"  {self.corfreq}" if self.corfreq.upper() == "S" else ""
        r2 = (
            f"{self.no:>4}  {self.ra:>6.3f}"
            f"  {self.h:>7.3f}{self.d:>6.3f}{self.mva:>8.1f}"
            f"{fr_str}{c_str}"
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
            linhas.append("(No) (L'd)(Ra )( H )( D )(MVA)Fr C\n")
            for m in self._md01:
                linhas.append(m.serializar() + "\n")
            linhas.append("999999\n")

        if self._md02:
            linhas.append("DMDG MD02\n")
            linhas.append('(No) (CS) (Ld )(Lq )(L\'d)(L"d)(Ll )(T\'d) (T"d)(T"q)\n')
            linhas.append("(No) (Ra )( H )( D )(MVA)Fr C\n")
            for m in self._md02:
                linhas.append(m.serializar() + "\n")
            linhas.append("999999\n")

        if self._md03:
            linhas.append("DMDG MD03\n")
            linhas.append("(No) (CS) (Ld )(Lq )(L'd)(L'q)(L\"d)(Ll )(T'd)(T'q)(T\"d)(T\"q)\n")
            linhas.append("(No) (Ra )( H )( D )(MVA)Fr C\n")
            for m in self._md03:
                linhas.append(m.serializar() + "\n")
            linhas.append("999999\n")

        return "".join(linhas)


# ---------------------------------------------------------------------------
# FACTS / HVDC – blocos de dados (introduzidos em v0.4.3, etapa 0.4)
# ---------------------------------------------------------------------------


@dataclass
class _CER:
    """Dados de um Compensador Estático de Reativos (CER/SVC) – best-effort."""

    no: int
    nb: int  # barra de conexão
    bmin: float = 0.0  # susceptância mínima [pu]
    bmax: float = 0.0  # susceptância máxima [pu]
    vref: float = 1.0  # tensão de referência [pu]
    modelo: int = 1  # número do modelo de controle (DMCS)
    extras: str = ""  # campos adicionais em formato bruto

    def serializar(self) -> str:
        return (
            f"{self.no:>4}  {self.nb:>6}  {self.bmin:>8.4f}  {self.bmax:>8.4f}"
            f"  {self.vref:>8.4f}  {self.modelo:>4}"
        )


@dataclass
class BlocoSVC(BlocoBase):
    """Dados de Compensadores Estáticos de Reativos (DCER/SVC).

    Confiança: best-effort — campos confirmados contra descrição geral do
    manual (cap. 25), mas layout de colunas não verificado verbatim.
    Use `linha_bruta()` se precisar de precisão de colunas.
    """

    keyword: str = field(default="DCER", init=False, repr=False)
    _equipamentos: list = field(default_factory=list)

    def tem_dados(self) -> bool:
        return bool(self._equipamentos)

    def adicionar(
        self,
        no: int,
        nb: int,
        bmin: float = 0.0,
        bmax: float = 0.0,
        vref: float = 1.0,
        modelo: int = 1,
    ) -> "BlocoSVC":
        self._equipamentos.append(
            _CER(no=no, nb=nb, bmin=bmin, bmax=bmax, vref=vref, modelo=modelo)
        )
        return self

    def serializar(self) -> str:
        linhas = [self._cabecalho()]
        for eq in self._equipamentos:
            linhas.append(eq.serializar() + "\n")
        linhas.append(self._terminador())
        return "".join(linhas)


@dataclass
class _TCSC:
    """Dados de Compensador Série Controlado (TCSC) – best-effort."""

    no: int
    de: int
    para: int
    circ: int = 1
    xcmin: float = 0.0
    xcmax: float = 0.0
    modelo: int = 1

    def serializar(self) -> str:
        return (
            f"{self.no:>4}  {self.de:>6}  {self.para:>6}  {self.circ:>2}"
            f"  {self.xcmin:>8.4f}  {self.xcmax:>8.4f}  {self.modelo:>4}"
        )


@dataclass
class BlocoTCSC(BlocoBase):
    """Dados de Compensadores Série Controláveis (DCSC) – best-effort."""

    keyword: str = field(default="DCSC", init=False, repr=False)
    _equipamentos: list = field(default_factory=list)

    def tem_dados(self) -> bool:
        return bool(self._equipamentos)

    def adicionar(
        self,
        no: int,
        de: int,
        para: int,
        circ: int = 1,
        xcmin: float = 0.0,
        xcmax: float = 0.0,
        modelo: int = 1,
    ) -> "BlocoTCSC":
        self._equipamentos.append(
            _TCSC(no=no, de=de, para=para, circ=circ, xcmin=xcmin, xcmax=xcmax, modelo=modelo)
        )
        return self

    def serializar(self) -> str:
        linhas = [self._cabecalho()]
        for eq in self._equipamentos:
            linhas.append(eq.serializar() + "\n")
        linhas.append(self._terminador())
        return "".join(linhas)


@dataclass
class _STATCOM:
    """Dados de equipamento FACTS VSI (STATCOM/SSSC/UPFC) – best-effort."""

    no: int
    nb: int
    tipo_vsi: str = "STATCOM"  # STATCOM, SSSC, UPFC
    qmin: float = 0.0
    qmax: float = 0.0
    vref: float = 1.0
    modelo: int = 1

    def serializar(self) -> str:
        return (
            f"{self.no:>4}  {self.nb:>6}  {self.tipo_vsi:<8}"
            f"  {self.qmin:>8.4f}  {self.qmax:>8.4f}  {self.vref:>8.4f}"
            f"  {self.modelo:>4}"
        )


@dataclass
class BlocoSTATCOM(BlocoBase):
    """Dados de equipamentos FACTS VSI (DVSI) – best-effort."""

    keyword: str = field(default="DVSI", init=False, repr=False)
    _equipamentos: list = field(default_factory=list)

    def tem_dados(self) -> bool:
        return bool(self._equipamentos)

    def adicionar(
        self,
        no: int,
        nb: int,
        tipo_vsi: str = "STATCOM",
        qmin: float = 0.0,
        qmax: float = 0.0,
        vref: float = 1.0,
        modelo: int = 1,
    ) -> "BlocoSTATCOM":
        self._equipamentos.append(
            _STATCOM(
                no=no, nb=nb, tipo_vsi=tipo_vsi, qmin=qmin, qmax=qmax, vref=vref, modelo=modelo
            )
        )
        return self

    def serializar(self) -> str:
        linhas = [self._cabecalho()]
        for eq in self._equipamentos:
            linhas.append(eq.serializar() + "\n")
        linhas.append(self._terminador())
        return "".join(linhas)


@dataclass
class _HVDC:
    """Dados básicos de um conversor de elo HVDC LCC – best-effort."""

    no: int
    nb_ret: int  # barra do retificador
    nb_inv: int  # barra do inversor
    pcc: float = 0.0  # potência nominal [MW]
    vcc: float = 0.0  # tensão nominal CC [kV]
    icc: float = 0.0  # corrente nominal CC [kA]
    alfa_min: float = 5.0  # ângulo mínimo de disparo [graus]
    alfa_max: float = 90.0  # ângulo máximo [graus]
    gama_min: float = 15.0  # ângulo mínimo de extinção [graus]

    def serializar(self) -> str:
        return (
            f"{self.no:>4}  {self.nb_ret:>6}  {self.nb_inv:>6}"
            f"  {self.pcc:>10.2f}  {self.vcc:>10.2f}  {self.icc:>8.4f}"
            f"  {self.alfa_min:>6.1f}  {self.alfa_max:>6.1f}  {self.gama_min:>6.1f}"
        )


@dataclass
class BlocoHVDC(BlocoBase):
    """Dados de conversores HVDC LCC (DCNV) – best-effort.

    Confiança: best-effort — layout de campos confirma estrutura geral do
    manual (cap. 24), mas colunas exatas não verificadas verbatim.
    """

    keyword: str = field(default="DCNV", init=False, repr=False)
    _conversores: list = field(default_factory=list)

    def tem_dados(self) -> bool:
        return bool(self._conversores)

    def adicionar(
        self,
        no: int,
        nb_ret: int,
        nb_inv: int,
        pcc: float = 0.0,
        vcc: float = 0.0,
        icc: float = 0.0,
        alfa_min: float = 5.0,
        alfa_max: float = 90.0,
        gama_min: float = 15.0,
    ) -> "BlocoHVDC":
        self._conversores.append(
            _HVDC(
                no=no,
                nb_ret=nb_ret,
                nb_inv=nb_inv,
                pcc=pcc,
                vcc=vcc,
                icc=icc,
                alfa_min=alfa_min,
                alfa_max=alfa_max,
                gama_min=gama_min,
            )
        )
        return self

    def serializar(self) -> str:
        linhas = [self._cabecalho()]
        for c in self._conversores:
            linhas.append(c.serializar() + "\n")
        linhas.append(self._terminador())
        return "".join(linhas)
