"""
anarede.py – Interface básica com o ANAREDE (.sav) e validação cruzada.

Introduzido em v0.4.7 (etapa 0.4) — estado de partida do roadmap atual.

Implementa:
    ResultadoSAV     – dados extraídos de um arquivo .sav
    LeitorSAV        – parser básico de .sav (barras + circuitos)
    CasoAnatem.validar_contra_sav() – validação cruzada STB ↔ SAV

Formato .sav (ANAREDE):
    - Texto posicional (colunas fixas), encoding latin-1
    - Bloco DGBT: grupos de base de tensão (grupo → kV)
    - Bloco DBAR: dados de barras CA (No, Tipo, Gb, Nome, ...)
    - Bloco DLIN: dados de circuitos CA (De, Para, Nc, ...)
    - Terminador: 99999
    - Comentários: '(' ...

Confiança: Alta para os identificadores usados na validação cruzada —
DBAR (No, Nome, Tipo, grupo Gb) e DLIN (De, Para, Circuito) — via colunas
fixas do layout padrão ANAREDE, com fallback tolerante. A tensão-base (kV)
é resolvida via DGBT. O formato .sav é do ANAREDE (externo ao manual ANATEM);
a validação byte-a-byte contra uma versão específica fica pendente de amostra.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Dict, FrozenSet, List, Optional, Set, Tuple, Union

if TYPE_CHECKING:
    from .caso import CasoAnatem


# ---------------------------------------------------------------------------
# Estruturas de dados
# ---------------------------------------------------------------------------


@dataclass
class BarraSAV:
    """Dados mínimos de uma barra CA do arquivo .sav."""

    numero: int
    nome: str = ""
    tensao_base: float = 0.0  # kV (resolvida via grupo de base / DGBT)
    tipo: Optional[int] = None  # 0=PQ, 1=PV, 2=slack, 3=...
    grupo_base: Optional[str] = None  # código do grupo de base de tensão (Gb)

    def __hash__(self) -> int:
        return hash(self.numero)

    def __eq__(self, other: object) -> bool:
        return isinstance(other, BarraSAV) and self.numero == other.numero


@dataclass
class CircuitoSAV:
    """Dados mínimos de um circuito CA do arquivo .sav."""

    de: int
    para: int
    circuito: int = 1

    def chave(self) -> Tuple[int, int, int]:
        return (min(self.de, self.para), max(self.de, self.para), self.circuito)

    def __hash__(self) -> int:
        return hash(self.chave())

    def __eq__(self, other: object) -> bool:
        return isinstance(other, CircuitoSAV) and self.chave() == other.chave()


@dataclass
class ResultadoSAV:
    """Dados extraídos de um arquivo .sav do ANAREDE.

    Atributos:
        barras:    dict número → BarraSAV.
        circuitos: lista de CircuitoSAV.
        erros:     linhas que não puderam ser interpretadas.
    """

    barras: Dict[int, BarraSAV] = field(default_factory=dict)
    circuitos: List[CircuitoSAV] = field(default_factory=list)
    erros: List[str] = field(default_factory=list)

    @property
    def numeros_barras(self) -> FrozenSet[int]:
        return frozenset(self.barras.keys())

    def chaves_circuitos(self) -> Set[Tuple[int, int, int]]:
        return {c.chave() for c in self.circuitos}


# ---------------------------------------------------------------------------
# LeitorSAV
# ---------------------------------------------------------------------------


class LeitorSAV:
    """Leitor de arquivos .sav do ANAREDE.

    Extrai barras (DBAR), circuitos (DLIN) e grupos de base de tensão (DGBT)
    por parsing de **colunas fixas** — o formato dos cartões ANAREDE é
    posicional, apesar do nome "formato livre". A tensão-base (kV) de cada
    barra é resolvida a partir do seu grupo de base (campo ``Gb``) contra a
    tabela DGBT, e não lida diretamente do DBAR (onde só há a tensão em pu).

    Layout de colunas (0-based, layout padrão ANAREDE):

    ``DBAR``  ``No[0:5]  Tipo[7:8]  Gb[8:10]  Nome[10:22]``
    ``DLIN``  ``De[0:5]  Para[10:15]  Nc[15:17]``
    ``DGBT``  ``Grupo  Tensão(kV)`` (formato livre, 2 campos)

    Quando uma linha não casa com as colunas fixas (versões antigas, campos
    deslocados), há um *fallback* por split de espaços que recupera ao menos
    os identificadores. Campos não reconhecidos vão para ``resultado.erros``.
    """

    @staticmethod
    def _slice_int(linha: str, a: int, b: int) -> Optional[int]:
        tok = linha[a:b].strip() if len(linha) > a else ""
        try:
            return int(tok) if tok else None
        except ValueError:
            return None

    @staticmethod
    def _slice_str(linha: str, a: int, b: int) -> str:
        return linha[a:b].strip() if len(linha) > a else ""

    # Blocos ANAREDE reconhecidos como cabeçalho (encerram o modo anterior)
    _BLOCOS_CONHECIDOS = frozenset(
        {
            "DBAR",
            "DLIN",
            "DGBT",
            "DGLT",
            "DCTE",
            "DOPC",
            "TITU",
            "DGER",
            "DCAR",
            "DSHL",
            "DBSH",
            "DPMU",
            "DCSC",
            "DARE",
            "DTPF",
            "DANC",
        }
    )

    @classmethod
    def ler(cls, caminho: Union[str, Path]) -> ResultadoSAV:
        """Lê um arquivo .sav e retorna um ResultadoSAV.

        Args:
            caminho: caminho do arquivo .sav.

        Returns:
            ResultadoSAV com barras e circuitos identificados.
        """
        caminho = Path(caminho)
        texto = caminho.read_text(encoding="latin-1", errors="replace")
        linhas = texto.splitlines()
        return cls._parsear(linhas)

    @classmethod
    def ler_texto(cls, texto: str) -> ResultadoSAV:
        """Variante para parsing de string (útil em testes)."""
        return cls._parsear(texto.splitlines())

    @classmethod
    def _parsear(cls, linhas: List[str]) -> ResultadoSAV:
        resultado = ResultadoSAV()
        modo = None  # "DBAR" | "DLIN" | "DGBT" | None
        grupos_base: Dict[str, float] = {}

        for linha in linhas:
            stripped = linha.strip()

            # Comentário / linha vazia
            if not stripped or stripped.startswith("("):
                continue

            # Terminador de bloco (99999 ou 99999999)
            if stripped.startswith("99999"):
                modo = None
                continue

            kw = stripped.upper().split()[0]

            # Cabeçalho de bloco: troca de modo
            if kw in cls._BLOCOS_CONHECIDOS:
                modo = kw if kw in ("DBAR", "DLIN", "DGBT") else None
                continue

            if modo == "DGBT":
                cls._parsear_grupo_base(linha, grupos_base)

            elif modo == "DBAR":
                barra = cls._parsear_barra(linha)
                if barra is not None:
                    resultado.barras[barra.numero] = barra
                else:
                    resultado.erros.append(f"DBAR não interpretada: {stripped[:60]}")

            elif modo == "DLIN":
                circ = cls._parsear_circuito(linha)
                if circ is not None:
                    resultado.circuitos.append(circ)
                else:
                    resultado.erros.append(f"DLIN não interpretada: {stripped[:60]}")

        # Resolve a tensão-base de cada barra a partir do seu grupo (DGBT)
        if grupos_base:
            for barra in resultado.barras.values():
                if barra.grupo_base and barra.tensao_base == 0.0:
                    barra.tensao_base = grupos_base.get(barra.grupo_base, 0.0)

        return resultado

    @classmethod
    def _parsear_grupo_base(cls, linha: str, grupos: Dict[str, float]) -> None:
        """Extrai (grupo, tensão-base kV) de uma linha DGBT.

        Formato: ``Gb  ( tensão )`` — código do grupo + tensão-base em kV.
        """
        partes = linha.split()
        if len(partes) >= 2:
            try:
                grupos[partes[0].strip()] = float(partes[1])
            except ValueError:
                pass

    @classmethod
    def _parsear_barra(cls, linha: str) -> Optional[BarraSAV]:
        """Extrai número, tipo, grupo de base e nome de uma linha DBAR.

        Usa colunas fixas do layout ANAREDE; recorre a split de espaços se
        o número da barra não estiver na coluna esperada.
        """
        numero = cls._slice_int(linha, 0, 5)
        if numero is None:
            # Fallback: primeiro token inteiro
            partes = linha.split()
            if not partes:
                return None
            try:
                numero = int(partes[0])
            except ValueError:
                return None
            nome = partes[1] if len(partes) > 1 else ""
            return BarraSAV(numero=numero, nome=nome)

        tipo = cls._slice_int(linha, 7, 8)
        grupo = cls._slice_str(linha, 8, 10) or None
        nome = cls._slice_str(linha, 10, 22)
        return BarraSAV(numero=numero, nome=nome, tipo=tipo, grupo_base=grupo)

    @classmethod
    def _parsear_circuito(cls, linha: str) -> Optional[CircuitoSAV]:
        """Extrai De, Para, Circuito de uma linha DLIN (colunas fixas).

        Recorre a split de espaços se as colunas fixas não produzirem
        inteiros válidos para De/Para.
        """
        de = cls._slice_int(linha, 0, 5)
        para = cls._slice_int(linha, 10, 15)
        nc = cls._slice_int(linha, 15, 17)
        if de is not None and para is not None:
            return CircuitoSAV(de=de, para=para, circuito=nc if nc is not None else 1)

        # Fallback: três primeiros inteiros
        partes = linha.split()
        if len(partes) < 2:
            return None
        try:
            de = int(partes[0])
            para = int(partes[1])
            circ = int(partes[2]) if len(partes) > 2 else 1
            return CircuitoSAV(de=de, para=para, circuito=circ)
        except ValueError:
            return None


# ---------------------------------------------------------------------------
# Validação cruzada STB ↔ SAV
# ---------------------------------------------------------------------------


def validar_contra_sav(caso: "CasoAnatem", path_sav: Union[str, Path]) -> List[str]:
    """Cruza barras/circuitos referenciados no STB com os presentes no SAV.

    Args:
        caso:     CasoAnatem a validar.
        path_sav: caminho do arquivo .sav do ANAREDE.

    Returns:
        Lista de avisos/erros de inconsistência. Vazia = tudo OK.
    """
    sav = LeitorSAV.ler(path_sav)
    erros: List[str] = []

    barras_sav = sav.numeros_barras
    circuitos_sav = sav.chaves_circuitos()

    # Barras referenciadas em eventos
    for ev in caso.devt._eventos:
        if ev.el and ev.el not in barras_sav:
            erros.append(
                f"DEVT: barra {ev.el} (evento {ev.codigo}) não existe no SAV."
            )
        if ev.pa and ev.pa not in barras_sav:
            erros.append(
                f"DEVT: barra {ev.pa} (evento {ev.codigo}) não existe no SAV."
            )
        if ev.pa and (ev.nc or 1):
            chave = (min(ev.el, ev.pa), max(ev.el, ev.pa), ev.nc or 1)
            if chave not in circuitos_sav:
                erros.append(
                    f"DEVT: circuito {ev.el}-{ev.pa} nc={ev.nc or 1} "
                    f"(evento {ev.codigo}) não existe no SAV."
                )

    # Barras referenciadas em DPLT
    for linha in caso.dplt.linhas:
        partes = linha.split()
        if len(partes) >= 2:
            try:
                nb = int(partes[1])
                if nb and nb not in barras_sav:
                    erros.append(
                        f"DPLT: barra {nb} (var {partes[0]}) não existe no SAV."
                    )
            except ValueError:
                pass

    # Barras em DMAQ
    for assoc in caso.dmaq.associacoes:
        if assoc.barra and assoc.barra not in barras_sav:
            erros.append(f"DMAQ: barra {assoc.barra} não existe no SAV.")

    return erros
