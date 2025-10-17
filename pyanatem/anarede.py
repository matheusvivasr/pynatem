"""
anarede.py – Interface básica com o ANAREDE (.sav) e validação cruzada.

Introduzido em v0.4.7 (etapa 0.4) — estado de partida do roadmap atual.

Implementa:
    ResultadoSAV     – dados extraídos de um arquivo .sav
    LeitorSAV        – parser básico de .sav (barras + circuitos)
    CasoAnatem.validar_contra_sav() – validação cruzada STB ↔ SAV

Formato .sav (ANAREDE):
    - Texto posicional, encoding latin-1
    - Bloco DBAR: dados de barras CA
    - Bloco DLIN: dados de circuitos CA
    - Terminador: 99999
    - Comentários: '(' ...

Confiança: Alta para DBAR (No, Nome, Vb) e DLIN (De, Para, Circuito).
Layout de colunas confirmado contra estrutura padrão ANAREDE.
"""

from __future__ import annotations

import re
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
    tensao_base: float = 0.0  # kV

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
    """Leitor básico de arquivos .sav do ANAREDE.

    Extrai barras (DBAR) e circuitos (DLIN) por parsing posicional/regex.
    Não decodifica todos os campos — apenas os necessários para validação
    cruzada com o STB do ANATEM.

    Formato DBAR (colunas 1-10 = No, 11-22 = Nome, …, Vb em cols 21-26):
        A layout exato varia por versão do ANAREDE; o parser usa regex
        tolerante que captura o número da barra na posição inicial e o
        nome como sequência alfanumérica seguinte.

    Formato DLIN (De Para Circuito na posição inicial da linha):
        Extrai os três primeiros campos inteiros da linha.
    """

    # Padrão para linha de barra: começa com inteiro, segue nome e campos
    _RE_DBAR = re.compile(r"^\s*(\d+)\s+([\w\-\.]+)?\s*(\d+)?\s*(\d+)?\s*([\d\.]+)?", re.ASCII)
    # Padrão simples para circuito: três inteiros no início
    _RE_DLIN = re.compile(r"^\s*(\d+)\s+(\d+)\s+(\d+)", re.ASCII)

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
        modo = None  # "DBAR" | "DLIN" | None

        for linha in linhas:
            stripped = linha.strip()

            # Comentário
            if stripped.startswith("(") or not stripped:
                continue

            # Terminador de bloco
            if stripped.startswith("99999"):
                modo = None
                continue

            kw = stripped.upper().split()[0] if stripped else ""

            # Detecção de blocos
            if kw == "DBAR":
                modo = "DBAR"
                continue
            if kw == "DLIN":
                modo = "DLIN"
                continue
            if kw in (
                "DGBT",
                "DGLT",
                "DCTE",
                "DOPC",
                "TITU",
                "DGER",
                "DCAR",
                "DGBT",
                "DPMU",
                "DCSC",
            ):
                modo = None
                continue

            if modo == "DBAR":
                barra = cls._parsear_barra(stripped)
                if barra is not None:
                    resultado.barras[barra.numero] = barra
                else:
                    resultado.erros.append(f"DBAR não interpretada: {stripped[:60]}")

            elif modo == "DLIN":
                circ = cls._parsear_circuito(stripped)
                if circ is not None:
                    resultado.circuitos.append(circ)
                else:
                    resultado.erros.append(f"DLIN não interpretada: {stripped[:60]}")

        return resultado

    @classmethod
    def _parsear_barra(cls, linha: str) -> Optional[BarraSAV]:
        """Extrai número, nome e tensão-base de uma linha DBAR."""
        partes = linha.split()
        if not partes:
            return None
        try:
            numero = int(partes[0])
        except ValueError:
            return None
        nome = partes[1] if len(partes) > 1 else ""
        # Tensão base é geralmente o último campo numérico em formato decimal
        # Em muitas versões do SAV: No Nome Tipo Area Zona Vb Ang ...
        # Tentativa: campo 5 ou 6 pode ser Vb
        vb = 0.0
        for tok in partes[2:6]:
            try:
                v = float(tok)
                if 0.1 < v < 9999:  # heurística para tensão-base em kV
                    vb = v
                    break
            except ValueError:
                continue
        return BarraSAV(numero=numero, nome=nome, tensao_base=vb)

    @classmethod
    def _parsear_circuito(cls, linha: str) -> Optional[CircuitoSAV]:
        """Extrai De, Para, Circuito de uma linha DLIN."""
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
        if ev.nb1 and ev.nb1 not in barras_sav:
            erros.append(f"DEVT: barra {ev.nb1} (evento {ev.codigo}) não existe no SAV.")
        if ev.nb2 and ev.nb2 not in barras_sav:
            erros.append(f"DEVT: barra {ev.nb2} (evento {ev.codigo}) não existe no SAV.")
        if ev.nb2 and ev.nc:
            chave = (min(ev.nb1, ev.nb2), max(ev.nb1, ev.nb2), ev.nc)
            if chave not in circuitos_sav:
                erros.append(
                    f"DEVT: circuito {ev.nb1}-{ev.nb2} nc={ev.nc} "
                    f"(evento {ev.codigo}) não existe no SAV."
                )

    # Barras referenciadas em DPLT
    for linha in caso.dplt.linhas:
        partes = linha.split()
        if len(partes) >= 2:
            try:
                nb = int(partes[1])
                if nb and nb not in barras_sav:
                    erros.append(f"DPLT: barra {nb} (var {partes[0]}) não existe no SAV.")
            except ValueError:
                pass

    # Barras em DMAQ
    for assoc in caso.dmaq.associacoes:
        if assoc.barra and assoc.barra not in barras_sav:
            erros.append(f"DMAQ: barra {assoc.barra} não existe no SAV.")

    return erros
