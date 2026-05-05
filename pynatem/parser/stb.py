"""
parser/stb.py – Leitura de arquivos STB do ANATEM.

Suporte:
    DARQ  – 8 subtipos singulares + DCDU/DBLT com múltiplos arquivos
    DSIM  – linha posicional + NPAS + MXIT
    DEVT  – eventos estruturados: APCB, RMCB, APCC, APCL, RMCL, ABCI, FECI,
            MDSH, TRGT, TRGV; demais preservados como texto bruto
    DPLT  – 17 variáveis estruturadas (barras, máquinas, circuitos, cargas);
            demais (incluindo OLTC/FACTS/HVDC/CDU best-effort) preservadas
            como texto bruto — o roundtrip funciona igual, só não viram
            objetos estruturados no parser ainda
    DMAQ  – linhas preservadas como texto bruto
    DMDG  – MD01, MD02 e MD03 totalmente estruturados (Sessão 4)
    DRGT  – reguladores de tensão predefinidos (§16.3): MD01–MD24 genérico (v1.2.1)
    DRGV  – reguladores de velocidade/turbina (§16.4): MD01–MD07 genérico (v1.2.2)
    DEST  – estabilizadores/PSS (§16.5): MD01–MD12 genérico (v1.2.3)
    DCST  – curvas de saturação (§16.2): Nc Tp P1 P2 P3 (v1.2.5)
    DCAG  – associação CAG↔CDU (§46.13): Nc Mc[u] (v1.2.6)
    DCCT  – associação CCT↔CDU (§46.15): Nc Mc[u] (v1.2.6)
    DCAR  – cargas funcionais (§46.14): params ZIP; seleção preservada bruta (v1.3.1)
    DMTC  – controle de tap de OLTC (§14.1): MDxx genérico (v1.3.3)
    DLTC  – dados/associação de OLTC (§46.40): colunas fixas De..Kbs (v1.3.3)
    DFLA  – fluxo agregado de intercâmbio (§13.1): áreas + circuitos, FIMFLA (v1.3.4)
    DCER  – associação CER/SVC (§46.18): Nb Gr Mc[u] [Me[u]] (v1.1.1)
    DCSC  – associação CSC/TCSC (§46.22): De Pa Nc Mc[u] [Me[u]] (v1.1.1)
    DVSI  – conversores FACTS VSI (§46.64): 15 campos em colunas fixas (v1.1.1)
    DCNV  – conversores CA-CC / assoc. (§46.21): colunas fixas No..S4 (v1.1.2)
    DELO  – associação de elos CC (§46.27): Ne M+[u] [M-[u]] (v1.1.2)
    DOPC  – opções FREQ e BASE extraídas; demais preservadas
    TITU  – título extraído

Linhas de comentário (iniciadas com '(') são ignoradas.
Blocos desconhecidos são silenciosamente pulados.
"""

from __future__ import annotations
from pathlib import Path
from typing import List, Optional, Tuple


def _strip_comment(linha: str) -> str:
    idx = linha.find("(")
    return linha[:idx].rstrip() if idx >= 0 else linha.rstrip()


def _e_terminador(linha: str) -> bool:
    return linha.strip().startswith("999999")


def _e_fim(linha: str) -> bool:
    return linha.strip().upper() == "FIM"


def _safe_float(s: str, default: float = 0.0) -> float:
    try:
        return float(s)
    except (ValueError, TypeError):
        return default


def _safe_int(s: str, default: int = 0) -> int:
    try:
        return int(s)
    except (ValueError, TypeError):
        return default


def _parse_valor(token: str):
    """Converte um token de parâmetro em int, float ou str (nesta ordem).

    Preserva o tipo natural: ``"3"`` → 3, ``"1.5"`` → 1.5, ``"D"`` → "D".
    """
    try:
        return int(token)
    except ValueError:
        pass
    try:
        return float(token)
    except ValueError:
        return token


def _sep_flag_u(token: str) -> Tuple[int, bool]:
    """Separa ``<numero>[U]`` em (numero, usuario).

    A letra ``U``/``u`` colada ao número marca modelo definido pelo usuário
    (CDU). Ex.: ``"94U"`` → ``(94, True)``; ``"800"`` → ``(800, False)``.
    """
    token = token.strip()
    if token and token[-1] in ("U", "u"):
        return int(token[:-1]), True
    return int(token), False


# subtipos DARQ singulares (não incluem DCDU/DBLT, tratados à parte)
_DARQ_MAPA_SIMPLES = {
    "SIST": "sav",
    "RELA": "rela",
    "LOGI": "log",
    "PLOT": "plt",
    "PLOC": "plt_cdu",
    "PLOR": "plt_rele",
    "SNAP": "snap",
    "SINA": "sina",
    "DATO": "rela",  # alias legado
}

# Mnemônicos oficiais de eventos DEVT (manual §46.31 + capítulos 10–16)
_DEVT_COM_CIRCUITO = {"APCL", "RMCL", "ABCI", "FECI", "MDCI"}
_DEVT_SIMPLES = {"APCB", "RMCB", "APCC", "MDSH", "DBCA", "LBCA"}
_DEVT_MAQUINA = {"TRGT", "TRGV"}

_DPLT_BARRA = {"VBAR", "TBAR", "FREQ", "PCAG", "QCAG"}
_DPLT_MAQUINA = {"DELT", "OMEG", "PGER", "QGER", "ICAM", "EEXC", "VTER", "PELM", "PMEC"}
_DPLT_CIRCUITO = {"FLXP", "FLXQ", "FLXC"}


class ParserSTB:
    """Lê um arquivo STB e devolve um CasoAnatem populado."""

    @staticmethod
    def ler(caminho) -> "CasoAnatem":  # noqa: F821
        from pynatem.caso import CasoAnatem

        caminho = Path(caminho)
        texto = caminho.read_text(encoding="latin-1", errors="replace")
        linhas = texto.splitlines()

        caso = CasoAnatem()
        i = 0

        while i < len(linhas):
            linha = _strip_comment(linhas[i])
            kw = linha.strip().upper()

            if not kw or kw.startswith("("):
                i += 1
                continue
            if _e_fim(kw):
                break

            if kw == "DARQ":
                i = ParserSTB._ler_darq(linhas, i + 1, caso)
            elif kw == "DOPC":
                i = ParserSTB._ler_dopc(linhas, i + 1, caso)
            elif kw == "DSIM":
                i = ParserSTB._ler_dsim(linhas, i + 1, caso)
            elif kw == "DEVT":
                i = ParserSTB._ler_devt(linhas, i + 1, caso)
            elif kw == "DPLT":
                i = ParserSTB._ler_dplt(linhas, i + 1, caso)
            elif kw == "DMAQ":
                i = ParserSTB._ler_dmaq(linhas, i + 1, caso)
            elif kw.startswith("DMDG"):
                i = ParserSTB._ler_dmdg(linhas, i, caso)
            elif kw.startswith("DMEL"):
                i = ParserSTB._ler_dmel(linhas, i + 1, caso)
            elif kw == "DCLI":
                i = ParserSTB._ler_dcli(linhas, i + 1, caso)
            elif kw == "DMCV":
                i = ParserSTB._ler_dmcv(linhas, i + 1, caso)
            elif kw.startswith("DRGT"):
                i = ParserSTB._ler_modelo_mdxx(linhas, i, caso, "drgt")
            elif kw.startswith("DRGV"):
                i = ParserSTB._ler_modelo_mdxx(linhas, i, caso, "drgv")
            elif kw.startswith("DEST"):
                i = ParserSTB._ler_modelo_mdxx(linhas, i, caso, "dest")
            elif kw.startswith("DMTC"):
                i = ParserSTB._ler_modelo_mdxx(linhas, i, caso, "dmtc")
            elif kw == "DLTC":
                i = ParserSTB._ler_dltc(linhas, i + 1, caso)
            elif kw == "DFLA":
                i = ParserSTB._ler_dfla(linhas, i + 1, caso)
            elif kw == "DMOT":
                i = ParserSTB._ler_dmot(linhas, i + 1, caso)
            elif kw == "DGSE":
                i = ParserSTB._ler_dgse(linhas, i + 1, caso)
            elif kw == "DCST":
                i = ParserSTB._ler_dcst(linhas, i + 1, caso)
            elif kw.startswith("DCAR"):
                i = ParserSTB._ler_dcar(linhas, i, caso)
            elif kw.startswith("DGER"):
                i = ParserSTB._ler_dger(linhas, i, caso)
            elif kw == "DFNT":
                i = ParserSTB._ler_dfnt(linhas, i + 1, caso)
            elif kw == "DCAG":
                i = ParserSTB._ler_assoc_cdu(linhas, i + 1, caso, "dcag")
            elif kw == "DCCT":
                i = ParserSTB._ler_assoc_cdu(linhas, i + 1, caso, "dcct")
            elif kw == "TITU":
                i = ParserSTB._ler_titu(linhas, i + 1, caso)
            elif kw == "DCDU":
                i = ParserSTB._ler_dcdu(linhas, i, caso)
            elif kw == "DCER":
                i = ParserSTB._ler_dcer(linhas, i + 1, caso)
            elif kw == "DCSC":
                i = ParserSTB._ler_dcsc(linhas, i + 1, caso)
            elif kw == "DVSI":
                i = ParserSTB._ler_dvsi(linhas, i + 1, caso)
            elif kw == "DCNV":
                i = ParserSTB._ler_dcnv(linhas, i + 1, caso)
            elif kw == "DELO":
                i = ParserSTB._ler_delo(linhas, i + 1, caso)
            elif kw == "DDFM":
                i = ParserSTB._ler_ddfm(linhas, i + 1, caso)
            else:
                i = ParserSTB._pular_bloco(linhas, i + 1)

        return caso

    @staticmethod
    def _ler_darq(linhas, inicio, caso) -> int:
        i = inicio
        while i < len(linhas):
            linha = _strip_comment(linhas[i])
            if _e_terminador(linha) or _e_fim(linha):
                return i + 1
            partes = linha.split(None, 1)
            if len(partes) >= 2:
                subtipo = partes[0].upper()
                arq = partes[1].strip()
                if subtipo == "DCDU" and arq:
                    caso.darq.adicionar_cdu(arq)
                elif subtipo == "DBLT" and arq:
                    caso.darq.adicionar_blt(arq)
                else:
                    attr = _DARQ_MAPA_SIMPLES.get(subtipo)
                    if attr and arq:
                        setattr(caso.darq, attr, arq)
                    elif arq:
                        caso.darq.extras.append(linha)
            i += 1
        return i

    @staticmethod
    def _ler_dopc(linhas, inicio, caso) -> int:
        i = inicio
        while i < len(linhas):
            linha = _strip_comment(linhas[i])
            if _e_terminador(linha) or _e_fim(linha):
                return i + 1
            partes = linha.split()
            if partes:
                op = partes[0].upper()
                if op == "FREQ" and len(partes) >= 2:
                    caso.dopc.freq = _safe_float(partes[1])
                elif op == "BASE" and len(partes) >= 2:
                    caso.dopc.base_mva = _safe_float(partes[1])
                elif linha.strip():
                    caso.dopc.opcoes_extras.append(linha)
            i += 1
        return i

    @staticmethod
    def _ler_dsim(linhas, inicio, caso) -> int:
        """Lê a linha de dados do DSIM no formato oficial.

        Régua: ``( Tmax ) (Stp) ( P ) ( I ) ( F )`` — colunas 0-7, 9-13,
        15-19, 21-25 e 27-31 (fatias 0-indexadas, fim exclusivo).
        """
        i = inicio
        linha_pos_lida = False
        while i < len(linhas):
            linha = _strip_comment(linhas[i])
            if _e_terminador(linha) or _e_fim(linha):
                return i + 1
            if not linha.strip():
                i += 1
                continue
            if not linha_pos_lida:
                def fatia(a: int, b: int) -> str:
                    return linha[a:b].strip() if len(linha) > a else ""

                if fatia(0, 8):
                    caso.dsim.tmax = _safe_float(fatia(0, 8)) or caso.dsim.tmax
                if fatia(8, 14):
                    caso.dsim.stp = _safe_float(fatia(8, 14)) or caso.dsim.stp
                if fatia(14, 20):
                    caso.dsim.p = _safe_int(fatia(14, 20))
                if fatia(20, 26):
                    caso.dsim.i = _safe_int(fatia(20, 26))
                if fatia(26, 32):
                    caso.dsim.f = _safe_int(fatia(26, 32))
                linha_pos_lida = True
            i += 1
        return i

    @staticmethod
    def _ler_devt(linhas, inicio, caso) -> int:
        from pynatem.blocos import _Evento

        i = inicio
        while i < len(linhas):
            linha = _strip_comment(linhas[i])
            if _e_terminador(linha) or _e_fim(linha):
                return i + 1
            if not linha.strip():
                i += 1
                continue

            partes = linha.split()
            cod = partes[0].upper() if partes else ""

            if cod in _DEVT_SIMPLES or cod in _DEVT_COM_CIRCUITO or cod in _DEVT_MAQUINA:
                # leitura POSICIONAL pelas colunas oficiais da régua §46.31
                # (fatias 0-indexadas; fim exclusivo)
                def fatia(a: int, b: int) -> str:
                    return linha[a:b].strip() if len(linha) > a else ""

                ev = _Evento(
                    codigo=cod,
                    tini=_safe_float(fatia(5, 13)) or 0.0,
                    el=_safe_int(fatia(13, 19)) if fatia(13, 19) else None,
                    pa=_safe_int(fatia(19, 24)) if fatia(19, 24) else None,
                    nc=_safe_int(fatia(24, 26)) if fatia(24, 26) else None,
                    ex=_safe_int(fatia(26, 31)) if fatia(26, 31) else None,
                    pct=_safe_float(fatia(31, 37)) if fatia(31, 37) else None,
                    abs_=_safe_float(fatia(37, 44)) if fatia(37, 44) else None,
                    gr=_safe_int(fatia(44, 47)) if fatia(44, 47) else None,
                    uni=_safe_int(fatia(47, 51)) if fatia(47, 51) else None,
                    bl=_safe_int(fatia(59, 64)) if fatia(59, 64) else None,
                    rc=_safe_float(fatia(64, 72)) if fatia(64, 72) else None,
                    xc=_safe_float(fatia(72, 79)) if fatia(72, 79) else None,
                    bc=_safe_float(fatia(79, 86)) if fatia(79, 86) else None,
                    defas=_safe_float(fatia(86, 94)) if fatia(86, 94) else None,
                )
                if ev.el is None and len(partes) > 2:
                    # fallback tolerante para decks com espaçamento livre
                    # (fora das colunas oficiais): Tp Tempo El [Pa [Nc]]
                    ev.tini = _safe_float(partes[1])
                    ev.el = _safe_int(partes[2])
                    if cod in _DEVT_COM_CIRCUITO:
                        ev.pa = _safe_int(partes[3]) if len(partes) > 3 else None
                        ev.nc = _safe_int(partes[4]) if len(partes) > 4 else None
                caso.devt._eventos.append(ev)

            else:
                caso.devt._linhas_brutas.append(linha)

            i += 1
        return i

    @staticmethod
    def _ler_dplt(linhas, inicio, caso) -> int:
        i = inicio
        while i < len(linhas):
            linha = _strip_comment(linhas[i])
            if _e_terminador(linha) or _e_fim(linha):
                return i + 1
            if not linha.strip():
                i += 1
                continue

            partes = linha.split()
            cod = partes[0].upper() if partes else ""

            if cod in _DPLT_BARRA:
                id1 = _safe_int(partes[1]) if len(partes) > 1 else 0
                caso.dplt._add(cod, id1)
            elif cod in _DPLT_MAQUINA:
                id1 = _safe_int(partes[1]) if len(partes) > 1 else 0
                id2 = _safe_int(partes[2]) if len(partes) > 2 else 1
                caso.dplt._add(cod, id1, id2)
            elif cod in _DPLT_CIRCUITO:
                id1 = _safe_int(partes[1]) if len(partes) > 1 else 0
                id2 = _safe_int(partes[2]) if len(partes) > 2 else 0
                id3 = _safe_int(partes[3]) if len(partes) > 3 else 1
                caso.dplt._add(cod, id1, id2, id3)
            else:
                # inclui OLTC/FACTS/HVDC/CDU best-effort: preserva bruto no
                # roundtrip (não some, apenas não vira objeto estruturado)
                caso.dplt.linhas.append(linha)

            i += 1
        return i

    @staticmethod
    def _ler_dmaq(linhas, inicio, caso) -> int:
        """Parser posicional do bloco DMAQ (§46.41).

        Lê campos por fatias de coluna fixas, correspondendo ao layout emitido
        por ``_AssocMaquina.serializar()``.  Campos ausentes (espaços em branco
        na fatia) resultam em ``None``, sem deslocar os campos seguintes.

        Layout de colunas oficiais (régua §46.41, 0-based):
            Nb  : [0:5]    int
            Gr  : [5:10]   int
            P   : [10:14]  int opcional
            Q   : [14:18]  int opcional
            Und : [18:22]  int opcional
            Mg  : [22:29]  int opcional
            Mt  : [29:36]  int opcional
            cdu : [36]     'u'/'U' → mt_cdu=True
            Mv  : [37:43]  int opcional
            cdu : [43]     'u'/'U' → mv_cdu=True
            Me  : [44:50]  int opcional
            cdu : [50]     'u'/'U' → me_cdu=True
            Xvd : [51:56]  float opcional
            Nbc : [56:61]  int opcional
        """
        from pynatem.blocos import _AssocMaquina

        def _slice_int(s: str, a: int, b: int):
            """Extrai inteiro da fatia [a:b]; retorna None se vazio."""
            tok = s[a:b] if len(s) > a else ""
            tok = tok.strip()
            return int(tok) if tok else None

        def _slice_float(s: str, a: int, b: int):
            """Extrai float da fatia [a:b]; retorna None se vazio."""
            tok = s[a:b] if len(s) > a else ""
            tok = tok.strip()
            return float(tok) if tok else None

        def _slice_cdu(s: str, pos: int) -> bool:
            """Retorna True se s[pos] for 'u' ou 'U'."""
            if len(s) > pos:
                return s[pos].lower() == "u"
            return False

        i = inicio
        while i < len(linhas):
            linha = _strip_comment(linhas[i])
            if _e_terminador(linha) or _e_fim(linha):
                return i + 1
            stripped = linha.strip()
            if not stripped or stripped.startswith("("):
                i += 1
                continue
            try:
                barra = _slice_int(linha, 0, 5)
                grupo = _slice_int(linha, 5, 10)
                if barra is None or grupo is None:
                    raise ValueError("Nb ou Gr ausente")
                p = _slice_int(linha, 10, 14)
                q = _slice_int(linha, 14, 18)
                und = _slice_int(linha, 18, 22)
                mg = _slice_int(linha, 22, 29)
                mt = _slice_int(linha, 29, 36)
                mt_cdu = _slice_cdu(linha, 36)
                mv = _slice_int(linha, 37, 43)
                mv_cdu = _slice_cdu(linha, 43)
                me = _slice_int(linha, 44, 50)
                me_cdu = _slice_cdu(linha, 50)
                xvd = _slice_float(linha, 51, 56)
                nbc = _slice_int(linha, 56, 61)

                caso.dmaq.adicionar_maquina(
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
            except (ValueError, IndexError):
                # Fallback: preserva como texto bruto para não perder dados
                caso.dmaq.associacoes.append(
                    _AssocMaquina(barra=0, grupo=0, texto_bruto=linha)
                )
            i += 1
        return i

    @staticmethod
    def _ler_titu(linhas, inicio, caso) -> int:
        i = inicio
        while i < len(linhas):
            linha = _strip_comment(linhas[i])
            if _e_terminador(linha) or _e_fim(linha):
                return i + 1
            if linha.strip():
                caso._titulo = linha.strip()
                return ParserSTB._pular_bloco(linhas, i + 1)
            i += 1
        return i

    @staticmethod
    def _ler_dmdg(linhas, inicio, caso) -> int:
        """Lê um bloco DMDG MDxx completo e popula caso.dmdg.

        A linha `inicio` contém a palavra-chave "DMDG MDxx".
        Cada variante (MD01/MD02/MD03) tem layout de colunas distinto.
        """
        from pynatem.blocos import BlocoDMDG

        if not hasattr(caso, "dmdg") or caso.dmdg is None:
            caso.dmdg = BlocoDMDG()

        header = _strip_comment(linhas[inicio]).strip().upper()
        # detecta qual variante: "DMDG MD01", "DMDG MD02", "DMDG MD03"
        variante = ""
        for v in ("MD01", "MD02", "MD03"):
            if v in header:
                variante = v
                break

        i = inicio + 1  # pula a linha da palavra-chave

        if variante == "MD01":
            # Uma régua por modelo:
            # No  L'd  Ra  H  D  MVA  [Fr]  [C]
            while i < len(linhas):
                linha = _strip_comment(linhas[i])
                if _e_terminador(linha) or _e_fim(linha):
                    return i + 1
                if not linha.strip() or linha.strip().startswith("("):
                    i += 1
                    continue
                p = linha.split()
                no = _safe_int(p[0])
                ld = _safe_float(p[1]) if len(p) > 1 else 0.0
                ra = _safe_float(p[2]) if len(p) > 2 else 0.0
                h = _safe_float(p[3]) if len(p) > 3 else 0.0
                d = _safe_float(p[4]) if len(p) > 4 else 0.0
                mva = _safe_float(p[5]) if len(p) > 5 else 100.0
                fr = _safe_float(p[6]) if len(p) > 6 else 60.0
                corfreq = p[7].upper() if len(p) > 7 else "N"
                caso.dmdg.adicionar_md01(
                    no=no, ld=ld, ra=ra, h=h, d=d, mva=mva, fr=fr, corfreq=corfreq
                )
                i += 1
            return i

        elif variante == "MD02":
            # Duas réguas consecutivas com o mesmo No:
            # Régua 1: No CS Ld Lq L'd L"d Ll T'd T"d T"q
            # Régua 2: No Ra H  D  MVA [Fr] [C]
            while i < len(linhas):
                linha1 = _strip_comment(linhas[i])
                if _e_terminador(linha1) or _e_fim(linha1):
                    return i + 1
                if not linha1.strip() or linha1.strip().startswith("("):
                    i += 1
                    continue
                # procura a régua 2 (próxima linha não-comentário não-vazia)
                j = i + 1
                while j < len(linhas):
                    l2 = _strip_comment(linhas[j])
                    if _e_terminador(l2) or _e_fim(l2):
                        break
                    if l2.strip() and not l2.strip().startswith("("):
                        break
                    j += 1
                if j >= len(linhas):
                    return j
                linha2 = _strip_comment(linhas[j])
                if _e_terminador(linha2) or _e_fim(linha2):
                    return j + 1

                p1 = linha1.split()
                p2 = linha2.split()
                no = _safe_int(p1[0])
                cs = _safe_int(p1[1]) if len(p1) > 1 else 0
                ld = _safe_float(p1[2]) if len(p1) > 2 else 0.0
                lq = _safe_float(p1[3]) if len(p1) > 3 else 0.0
                ld_trans = _safe_float(p1[4]) if len(p1) > 4 else 0.0
                ld_sub = _safe_float(p1[5]) if len(p1) > 5 else 0.0
                ll = _safe_float(p1[6]) if len(p1) > 6 else 0.0
                td_trans = _safe_float(p1[7]) if len(p1) > 7 else 0.0
                td_sub = _safe_float(p1[8]) if len(p1) > 8 else 0.0
                tq_sub = _safe_float(p1[9]) if len(p1) > 9 else 0.0
                # régua 2 (No já é p2[0], ignorado — usa No da régua 1)
                ra = _safe_float(p2[1]) if len(p2) > 1 else 0.0
                h = _safe_float(p2[2]) if len(p2) > 2 else 3.0
                d = _safe_float(p2[3]) if len(p2) > 3 else 0.0
                mva = _safe_float(p2[4]) if len(p2) > 4 else 100.0
                fr = _safe_float(p2[5]) if len(p2) > 5 else 60.0
                corfreq = p2[6].upper() if len(p2) > 6 else "N"
                caso.dmdg.adicionar_md02(
                    no=no,
                    cs=cs,
                    ld=ld,
                    lq=lq,
                    ld_trans=ld_trans,
                    ld_sub=ld_sub,
                    ll=ll,
                    td_trans=td_trans,
                    td_sub=td_sub,
                    tq_sub=tq_sub,
                    ra=ra,
                    h=h,
                    d=d,
                    mva=mva,
                    fr=fr,
                    corfreq=corfreq,
                )
                i = j + 1
            return i

        elif variante == "MD03":
            # Duas réguas — igual ao MD02 + L'q + T'q
            while i < len(linhas):
                linha1 = _strip_comment(linhas[i])
                if _e_terminador(linha1) or _e_fim(linha1):
                    return i + 1
                if not linha1.strip() or linha1.strip().startswith("("):
                    i += 1
                    continue
                j = i + 1
                while j < len(linhas):
                    l2 = _strip_comment(linhas[j])
                    if _e_terminador(l2) or _e_fim(l2):
                        break
                    if l2.strip() and not l2.strip().startswith("("):
                        break
                    j += 1
                if j >= len(linhas):
                    return j
                linha2 = _strip_comment(linhas[j])
                if _e_terminador(linha2) or _e_fim(linha2):
                    return j + 1

                p1 = linha1.split()
                p2 = linha2.split()
                no = _safe_int(p1[0])
                cs = _safe_int(p1[1]) if len(p1) > 1 else 0
                ld = _safe_float(p1[2]) if len(p1) > 2 else 0.0
                lq = _safe_float(p1[3]) if len(p1) > 3 else 0.0
                ld_trans = _safe_float(p1[4]) if len(p1) > 4 else 0.0
                lq_trans = _safe_float(p1[5]) if len(p1) > 5 else 0.0
                ld_sub = _safe_float(p1[6]) if len(p1) > 6 else 0.0
                ll = _safe_float(p1[7]) if len(p1) > 7 else 0.0
                td_trans = _safe_float(p1[8]) if len(p1) > 8 else 0.0
                tq_trans = _safe_float(p1[9]) if len(p1) > 9 else 0.0
                td_sub = _safe_float(p1[10]) if len(p1) > 10 else 0.0
                tq_sub = _safe_float(p1[11]) if len(p1) > 11 else 0.0
                ra = _safe_float(p2[1]) if len(p2) > 1 else 0.0
                h = _safe_float(p2[2]) if len(p2) > 2 else 3.0
                d = _safe_float(p2[3]) if len(p2) > 3 else 0.0
                mva = _safe_float(p2[4]) if len(p2) > 4 else 100.0
                fr = _safe_float(p2[5]) if len(p2) > 5 else 60.0
                corfreq = p2[6].upper() if len(p2) > 6 else "N"
                caso.dmdg.adicionar_md03(
                    no=no,
                    cs=cs,
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
                    ra=ra,
                    h=h,
                    d=d,
                    mva=mva,
                    fr=fr,
                    corfreq=corfreq,
                )
                i = j + 1
            return i

        else:
            # variante desconhecida — pula o bloco
            return ParserSTB._pular_bloco(linhas, i)

    @staticmethod
    def _ler_dcli(linhas, inicio, caso) -> int:
        """Lê o bloco DCLI (§46.19) — linhas CC com L, C (v1.6.2).

        Formato (Listagem 46.17):
            (De) (Pa)(Nc)( L )( C )
        """
        i = inicio
        while i < len(linhas):
            linha = _strip_comment(linhas[i])
            if _e_terminador(linha) or _e_fim(linha):
                return i + 1
            stripped = linha.strip()
            if not stripped:
                i += 1
                continue
            partes = stripped.split()
            if len(partes) < 2:
                i += 1
                continue
            de = int(partes[0])
            pa = int(partes[1])
            nc = int(partes[2]) if len(partes) > 2 else 1
            l = float(partes[3]) if len(partes) > 3 else 0.0
            c = float(partes[4]) if len(partes) > 4 else 0.0
            caso.dcli.adicionar(de=de, pa=pa, nc=nc, l=l, c=c)
            i += 1
        return i

    @staticmethod
    def _ler_dmcv(linhas, inicio, caso) -> int:
        """Lê o bloco DMCV (§46.44) — modelos conversores CA-CC (v1.6.1).

        Formato: texto bruto (roundtrip garantido, parsing completo em futuro).
        """
        i = inicio
        while i < len(linhas):
            linha = _strip_comment(linhas[i])
            if _e_terminador(linha) or _e_fim(linha):
                return i + 1
            stripped = linha.strip()
            if not stripped:
                i += 1
                continue
            caso.dmcv._dados_brutos.append(stripped + "\n")
            i += 1
        return i

    @staticmethod
    def _ler_dmel(linhas, inicio, caso) -> int:
        """Lê o bloco DMEL MD01 (§46.47) — modelos predefinidos de elo CC (v1.6.1).

        Formato livre: No C [Tbp]
        """
        i = inicio
        while i < len(linhas):
            linha = _strip_comment(linhas[i])
            if _e_terminador(linha) or _e_fim(linha):
                return i + 1
            stripped = linha.strip()
            if not stripped:
                i += 1
                continue
            partes = stripped.split()
            try:
                no = int(partes[0])
                tipo = partes[1].upper() if len(partes) > 1 else "C"
                tbp = _safe_float(partes[2]) if len(partes) > 2 else 0.0
                caso.dmel.adicionar_md01(no=no, tipo=tipo, tbp=tbp)
            except (ValueError, IndexError):
                pass
            i += 1
        return i

    @staticmethod
    def _ler_modelo_mdxx(linhas, inicio, caso, atributo: str) -> int:
        """Lê um bloco de modelo predefinido ``<KW> MDxx`` (DRGT/DRGV).

        A linha ``inicio`` contém '<KW> MDxx'. Cada linha de dados é ``No`` +
        parâmetros posicionais, armazenados genericamente no bloco ``caso.<attr>``.
        """
        bloco = getattr(caso, atributo)

        header = _strip_comment(linhas[inicio]).strip().upper()
        variante = "MD01"
        for tok in header.split():
            if tok.startswith("MD"):
                variante = tok
                break

        i = inicio + 1
        while i < len(linhas):
            linha = _strip_comment(linhas[i])
            if _e_terminador(linha) or _e_fim(linha):
                return i + 1
            stripped = linha.strip()
            if not stripped or stripped.startswith("("):
                i += 1
                continue
            partes = stripped.split()
            try:
                no = int(partes[0])
                params = [_parse_valor(p) for p in partes[1:]]
                bloco.adicionar(variante, no, *params)
            except (ValueError, IndexError):
                pass
            i += 1
        return i

    @staticmethod
    def _ler_assoc_cdu(linhas, inicio, caso, atributo: str) -> int:
        """Lê um código de associação de controle de área a CDU (DCAG/DCCT).

        Formato livre: ``Nc Mc[u]`` (Listagens 46.11 / 46.13).
        """
        bloco = getattr(caso, atributo)
        i = inicio
        while i < len(linhas):
            linha = _strip_comment(linhas[i])
            if _e_terminador(linha) or _e_fim(linha):
                return i + 1
            stripped = linha.strip()
            if not stripped:
                i += 1
                continue
            partes = stripped.split()
            try:
                nc = int(partes[0])
                mc, usuario = _sep_flag_u(partes[1])
                bloco.adicionar(nc, mc, usuario=usuario)
            except (ValueError, IndexError):
                pass
            i += 1
        return i

    @staticmethod
    def _ler_dfla(linhas, inicio, caso) -> int:
        """Lê o bloco DFLA (§13.1) — fluxo agregado de intercâmbio.

        Aninhado: por área, uma linha ``NA ID`` seguida de circuitos
        ``De Pa NC [Ex]``, encerrada por ``FIMFLA``.
        """
        i = inicio
        area = None
        while i < len(linhas):
            linha = _strip_comment(linhas[i])
            if _e_terminador(linha) or _e_fim(linha):
                return i + 1
            stripped = linha.strip()
            if not stripped:
                i += 1
                continue
            if stripped.upper() == "FIMFLA":
                area = None
                i += 1
                continue
            partes = stripped.split()
            try:
                if area is None:
                    # primeira régua: NA ID
                    na = int(partes[0])
                    ident = " ".join(partes[1:]) if len(partes) > 1 else ""
                    area = caso.dfla.adicionar_area(na=na, ident=ident)
                else:
                    # segunda régua: De Pa NC [Ex]
                    de = int(partes[0])
                    pa = int(partes[1])
                    nc = int(partes[2]) if len(partes) > 2 else 1
                    ex = int(partes[3]) if len(partes) > 3 else None
                    area.adicionar_circuito(de=de, pa=pa, nc=nc, ex=ex)
            except (ValueError, IndexError):
                pass
            i += 1
        return i

    @staticmethod
    def _ler_dltc(linhas, inicio, caso) -> int:
        """Lê o bloco DLTC (§46.40) — dados de OLTC + associação a controle.

        Parser de COLUNAS FIXAS (Tmn/Tmx/Kbs opcionais). Offsets espelham
        ``_AssocOLTC.serializar()`` / ``_DLTC_COLS`` em ``blocos.py``.
        """

        def _si(s, a, b):
            tok = s[a:b].strip() if len(s) > a else ""
            return int(tok) if tok else None

        def _sf(s, a, b):
            tok = s[a:b].strip() if len(s) > a else ""
            return float(tok) if tok else None

        def _sm(s, a, b):
            tok = s[a:b].strip() if len(s) > a else ""
            return _sep_flag_u(tok) if tok else (None, False)

        i = inicio
        while i < len(linhas):
            linha = linhas[i]
            if _e_terminador(linha) or _e_fim(linha):
                return i + 1
            stripped = linha.strip()
            if not stripped or stripped.startswith("("):
                i += 1
                continue
            try:
                de = _si(linha, 0, 5)
                pa = _si(linha, 5, 13)
                mt = _si(linha, 16, 23)
                if de is None or pa is None or mt is None:
                    raise ValueError("De/Pa/Mt ausente")
                mt_u = len(linha) > 23 and linha[23].lower() == "u"
                caso.dltc.adicionar(
                    de=de,
                    pa=pa,
                    mt=mt,
                    nc=_si(linha, 13, 16),
                    nst=_si(linha, 36, 40) or 1,
                    mt_usuario=mt_u,
                    tmn=_sf(linha, 24, 30),
                    tmx=_sf(linha, 30, 36),
                    kbs=_si(linha, 40, 47),
                )
            except (ValueError, IndexError):
                pass
            i += 1
        return i

    @staticmethod
    def _ler_dcar(linhas, inicio, caso) -> int:
        """Lê o bloco DCAR (§46.14) — cargas estáticas funcionais.

        A linha ``inicio`` é 'DCAR [opções]'. Cada linha de dados usa linguagem
        de seleção (Cap. 42), preservada como texto bruto para roundtrip fiel.
        """
        header = _strip_comment(linhas[inicio]).strip().split()
        caso.dcar.opcoes = " ".join(header[1:]) if len(header) > 1 else ""

        i = inicio + 1
        while i < len(linhas):
            linha = _strip_comment(linhas[i])
            if _e_terminador(linha) or _e_fim(linha):
                return i + 1
            stripped = linha.strip()
            if not stripped or stripped.startswith("("):
                i += 1
                continue
            caso.dcar.adicionar_bruto(stripped)
            i += 1
        return i

    @staticmethod
    def _ler_dger(linhas, inicio, caso) -> int:
        """Lê o bloco DGER (§17.1) — geração funcional ZIP (v1.5.2).

        A linha ``inicio`` é 'DGER [opções]'. Cada linha de dados usa linguagem
        de seleção (Cap. 42), preservada como texto bruto para roundtrip fiel.
        Idêntico a DCAR, mas para geração.
        """
        header = _strip_comment(linhas[inicio]).strip().split()
        caso.dger.opcoes = " ".join(header[1:]) if len(header) > 1 else ""

        i = inicio + 1
        while i < len(linhas):
            linha = _strip_comment(linhas[i])
            if _e_terminador(linha) or _e_fim(linha):
                return i + 1
            stripped = linha.strip()
            if not stripped or stripped.startswith("("):
                i += 1
                continue
            caso.dger.adicionar_bruto(stripped)
            i += 1
        return i

    @staticmethod
    def _ler_dcst(linhas, inicio, caso) -> int:
        """Lê o bloco DCST (§16.2) — curvas de saturação de máquina síncrona.

        Formato plano: ``Nc Tp P1 P2 P3`` por curva.
        """
        i = inicio
        while i < len(linhas):
            linha = _strip_comment(linhas[i])
            if _e_terminador(linha) or _e_fim(linha):
                return i + 1
            stripped = linha.strip()
            if not stripped:
                i += 1
                continue
            partes = stripped.split()
            try:
                nc = int(partes[0])
                tipo = int(partes[1])
                p1 = _safe_float(partes[2]) if len(partes) > 2 else 0.0
                p2 = _safe_float(partes[3]) if len(partes) > 3 else 0.0
                p3 = _safe_float(partes[4]) if len(partes) > 4 else 0.0
                caso.dcst.adicionar(nc, tipo, p1, p2, p3)
            except (ValueError, IndexError):
                pass
            i += 1
        return i

    @staticmethod
    def _ler_dmot(linhas, inicio, caso) -> int:
        """Lê o bloco DMOT (§15) — máquinas de indução convencional (v1.5.1).

        Formato livre: duas réguas possíveis.
        - Tipo 1 (M=1):   ``Nb Gr H K0 K1 K2 EXP [M]``  (7 campos, M=1)
        - Tipo 2 (M=2):   ``Nb Gr H K0 K1 K2 EXP Rr Xr Xs Xm Xp Tr0 [M]`` (13 campos, M=2)
        """
        i = inicio
        while i < len(linhas):
            linha = _strip_comment(linhas[i])
            if _e_terminador(linha) or _e_fim(linha):
                return i + 1
            stripped = linha.strip()
            if not stripped:
                i += 1
                continue

            partes = stripped.split()
            try:
                nb = int(partes[0])
                gr = int(partes[1])
                h = _safe_float(partes[2])
                k0 = _safe_float(partes[3]) if len(partes) > 3 else 0.0
                k1 = _safe_float(partes[4]) if len(partes) > 4 else 0.0
                k2 = _safe_float(partes[5]) if len(partes) > 5 else 0.0
                exp = _safe_float(partes[6]) if len(partes) > 6 else 0.0

                # Detectar tipo pela quantidade de campos
                if len(partes) >= 13:
                    # Tipo 2 com parâmetros do rotor
                    rr = _safe_float(partes[7]) if len(partes) > 7 else 0.0
                    xr = _safe_float(partes[8]) if len(partes) > 8 else 0.0
                    xs = _safe_float(partes[9]) if len(partes) > 9 else 0.0
                    xm = _safe_float(partes[10]) if len(partes) > 10 else 0.0
                    xp = _safe_float(partes[11]) if len(partes) > 11 else 0.0
                    tr0 = _safe_float(partes[12]) if len(partes) > 12 else 0.0
                    caso.dmot.adicionar_tipo2(
                        nb, gr, h, k0, k1, k2, exp, rr, xr, xs, xm, xp, tr0
                    )
                else:
                    # Tipo 1 (padrão, sem dinâmica rotórica)
                    caso.dmot.adicionar_tipo1(nb, gr, h, k0, k1, k2, exp)

            except (ValueError, IndexError):
                pass
            i += 1
        return i

    @staticmethod
    def _ler_dfnt(linhas, inicio, caso) -> int:
        """Lê o bloco DFNT (§21/46.34) — fonte shunt controlada por CDU (v1.5.5).

        Formato livre: Nb Gr T FP% FQ% Und Mc[u] R/G X/B [Sbas]
        """
        i = inicio
        while i < len(linhas):
            linha = _strip_comment(linhas[i])
            if _e_terminador(linha) or _e_fim(linha):
                return i + 1
            stripped = linha.strip()
            if not stripped:
                i += 1
                continue
            partes = stripped.split()
            try:
                nb = int(partes[0])
                gr = int(partes[1])
                tipo = partes[2].upper() if len(partes) > 2 else "V"
                fp = _safe_float(partes[3]) if len(partes) > 3 else 100.0
                fq = _safe_float(partes[4]) if len(partes) > 4 else 100.0
                und = int(partes[5]) if len(partes) > 5 else 1
                mc, mc_u = _sep_flag_u(partes[6]) if len(partes) > 6 else (0, False)
                r_ou_g = _safe_float(partes[7]) if len(partes) > 7 else 0.0
                x_ou_b = _safe_float(partes[8]) if len(partes) > 8 else 0.0
                sbas = _safe_float(partes[9]) if len(partes) > 9 else 0.0

                caso.dfnt.adicionar(
                    nb=nb, gr=gr, tipo=tipo, fp=fp, fq=fq, und=und, mc=mc,
                    r_ou_g=r_ou_g, x_ou_b=x_ou_b, sbas=sbas, mc_usuario=mc_u
                )
            except (ValueError, IndexError):
                pass
            i += 1
        return i

    @staticmethod
    def _ler_dcer(linhas, inicio, caso) -> int:
        """Lê o bloco DCER (§46.18) — associação de CER/SVC a modelos.

        Formato livre: ``Nb Gr Mc[u] [Me[u]]`` (Listagem 46.16).
        """
        i = inicio
        while i < len(linhas):
            linha = _strip_comment(linhas[i])
            if _e_terminador(linha) or _e_fim(linha):
                return i + 1
            stripped = linha.strip()
            if not stripped:
                i += 1
                continue
            partes = stripped.split()
            try:
                nb = int(partes[0])
                gr = int(partes[1])
                mc, mc_u = _sep_flag_u(partes[2])
                me, me_u = (None, True)
                if len(partes) > 3:
                    me, me_u = _sep_flag_u(partes[3])
                caso.svc.adicionar(
                    nb=nb, gr=gr, mc=mc, me=me, mc_usuario=mc_u, me_usuario=me_u
                )
            except (ValueError, IndexError):
                pass  # linha malformada: ignora sem abortar o bloco
            i += 1
        return i

    @staticmethod
    def _ler_dcsc(linhas, inicio, caso) -> int:
        """Lê o bloco DCSC (§46.22) — associação de CSC/TCSC a modelos.

        Formato livre: ``De Pa Nc Mc[u] [Me[u]]`` (Listagem 46.20).
        """
        i = inicio
        while i < len(linhas):
            linha = _strip_comment(linhas[i])
            if _e_terminador(linha) or _e_fim(linha):
                return i + 1
            stripped = linha.strip()
            if not stripped:
                i += 1
                continue
            partes = stripped.split()
            try:
                de = int(partes[0])
                pa = int(partes[1])
                nc = int(partes[2])
                mc, mc_u = _sep_flag_u(partes[3])
                me, me_u = (None, True)
                if len(partes) > 4:
                    me, me_u = _sep_flag_u(partes[4])
                caso.tcsc.adicionar(
                    de=de, pa=pa, mc=mc, nc=nc, me=me, mc_usuario=mc_u, me_usuario=me_u
                )
            except (ValueError, IndexError):
                pass
            i += 1
        return i

    @staticmethod
    def _ler_dvsi(linhas, inicio, caso) -> int:
        """Lê o bloco DVSI (§46.64) — dados de conversores FACTS VSI.

        Parser de COLUNAS FIXAS: os campos Pa/Rv/Vpt são opcionais e um
        branco não pode deslocar os seguintes. Os offsets espelham
        ``_ConversorVSI.serializar()`` / ``_VSI_COLS`` em ``blocos.py``.
        """

        def _si(s: str, a: int, b: int):
            tok = s[a:b].strip() if len(s) > a else ""
            return int(tok) if tok else None

        def _sf(s: str, a: int, b: int):
            tok = s[a:b].strip() if len(s) > a else ""
            return float(tok) if tok else None

        def _ss(s: str, a: int, b: int, default: str = "P"):
            tok = s[a:b].strip() if len(s) > a else ""
            return tok if tok else default

        i = inicio
        while i < len(linhas):
            linha = linhas[i]
            if _e_terminador(linha) or _e_fim(linha):
                return i + 1
            stripped = linha.strip()
            if not stripped or stripped.startswith("("):
                i += 1
                continue
            try:
                nv = _si(linha, 0, 5)
                de = _si(linha, 5, 11)
                if nv is None or de is None:
                    raise ValueError("Nv ou De ausente")
                caso.statcom.adicionar(
                    nv=nv,
                    de=de,
                    np=_si(linha, 21, 25) or 1,
                    cnvk=_sf(linha, 25, 39) or 0.0,
                    vb=_sf(linha, 41, 51) or 0.0,
                    xv=_sf(linha, 61, 71) or 0.0,
                    vst=_sf(linha, 81, 91) or 0.0,
                    st=_sf(linha, 91, 101) or 0.0,
                    ne=_si(linha, 109, 115) or 0,
                    pa=_si(linha, 11, 17),
                    nx=_si(linha, 17, 21) or 1,
                    m=_ss(linha, 39, 41, "P"),
                    rv=_sf(linha, 51, 61),
                    vpt=_sf(linha, 71, 81),
                    tap=(
                        _sf(linha, 101, 109)
                        if _sf(linha, 101, 109) is not None
                        else 1.0
                    ),
                )
            except (ValueError, IndexError):
                pass
            i += 1
        return i

    @staticmethod
    def _ler_dcnv(linhas, inicio, caso) -> int:
        """Lê o bloco DCNV (§46.21) — conversores CA-CC e associação a controles.

        Parser de COLUNAS FIXAS (Gkb/Amn/Amx/Gmn e S1–S4 são opcionais). Os
        offsets espelham ``_ConversorCACC.serializar()`` / ``_CACC_COLS``.
        """

        def _si(s: str, a: int, b: int):
            tok = s[a:b].strip() if len(s) > a else ""
            return int(tok) if tok else None

        def _sf(s: str, a: int, b: int):
            tok = s[a:b].strip() if len(s) > a else ""
            return float(tok) if tok else None

        def _sm(s: str, a: int, b: int):
            """Modelo em coluna fixa: (num|None, usuario)."""
            tok = s[a:b].strip() if len(s) > a else ""
            return _sep_flag_u(tok) if tok else (None, False)

        i = inicio
        while i < len(linhas):
            linha = linhas[i]
            if _e_terminador(linha) or _e_fim(linha):
                return i + 1
            stripped = linha.strip()
            if not stripped or stripped.startswith("("):
                i += 1
                continue
            try:
                no = _si(linha, 0, 5)
                mc, mc_u = _sm(linha, 37, 44)
                if no is None or mc is None:
                    raise ValueError("No ou Mc ausente")
                s1, s1_u = _sm(linha, 44, 51)
                s2, s2_u = _sm(linha, 51, 58)
                s3, s3_u = _sm(linha, 58, 65)
                s4, s4_u = _sm(linha, 65, 72)
                caso.hvdc.adicionar(
                    no=no,
                    mc=mc,
                    gkb=_sf(linha, 5, 13),
                    amn=_sf(linha, 13, 21),
                    amx=_sf(linha, 21, 29),
                    gmn=_sf(linha, 29, 37),
                    mc_usuario=mc_u,
                    s1=s1,
                    s2=s2,
                    s3=s3,
                    s4=s4,
                    s1_usuario=s1_u,
                    s2_usuario=s2_u,
                    s3_usuario=s3_u,
                    s4_usuario=s4_u,
                )
            except (ValueError, IndexError):
                pass
            i += 1
        return i

    @staticmethod
    def _ler_delo(linhas, inicio, caso) -> int:
        """Lê o bloco DELO (§46.27) — associação de elos CC aos modelos de polo.

        Formato livre: ``Ne M+[u] [M-[u]]`` (Listagem 46.25).
        """
        i = inicio
        while i < len(linhas):
            linha = _strip_comment(linhas[i])
            if _e_terminador(linha) or _e_fim(linha):
                return i + 1
            stripped = linha.strip()
            if not stripped:
                i += 1
                continue
            partes = stripped.split()
            try:
                ne = int(partes[0])
                mp, mp_u = _sep_flag_u(partes[1])
                mm, mm_u = (None, False)
                if len(partes) > 2:
                    mm, mm_u = _sep_flag_u(partes[2])
                caso.delo.adicionar(
                    ne=ne, mp=mp, mm=mm, mp_usuario=mp_u, mm_usuario=mm_u
                )
            except (ValueError, IndexError):
                pass
            i += 1
        return i

    @staticmethod
    def _ler_ddfm(linhas, inicio, caso) -> int:
        """Lê o bloco DDFM (§19.2) — associação de geradores eólicos DFIG (v1.5.3).

        Formato livre: Nb Gr P Q Und Mg Mt[u] Mc[u] Xvd Nbc Slip[u] R I
        """
        i = inicio
        while i < len(linhas):
            linha = _strip_comment(linhas[i])
            if _e_terminador(linha) or _e_fim(linha):
                return i + 1
            stripped = linha.strip()
            if not stripped:
                i += 1
                continue
            partes = stripped.split()
            try:
                nb = int(partes[0])
                gr = int(partes[1])
                p = _safe_float(partes[2]) if len(partes) > 2 else 0.0
                q = _safe_float(partes[3]) if len(partes) > 3 else 0.0
                und = int(partes[4]) if len(partes) > 4 else 1
                mg = int(partes[5]) if len(partes) > 5 else 0
                mt, mt_u = _sep_flag_u(partes[6]) if len(partes) > 6 else (0, False)
                mc, mc_u = _sep_flag_u(partes[7]) if len(partes) > 7 else (0, False)
                xvd = _safe_float(partes[8]) if len(partes) > 8 else 0.0
                nbc = int(partes[9]) if len(partes) > 9 else 0
                # Slip pode ser float (escorregamento) ou int com 'u' (CDU)
                slip_val = partes[10] if len(partes) > 10 else "0"
                if slip_val.endswith("U") or slip_val.endswith("u"):
                    slip = float(slip_val[:-1])
                    slip_u = True
                else:
                    slip = _safe_float(slip_val)
                    slip_u = False
                r = int(partes[11]) if len(partes) > 11 else 0
                i_val = int(partes[12]) if len(partes) > 12 else 0

                caso.ddfm.adicionar(
                    nb=nb, gr=gr, p=p, q=q, und=und, mg=mg, mt=mt, mc=mc,
                    mt_usuario=mt_u, mc_usuario=mc_u, xvd=xvd, nbc=nbc,
                    slip=slip, slip_usuario=slip_u, r=r, i=i_val
                )
            except (ValueError, IndexError):
                pass
            i += 1
        return i

    @staticmethod
    def _ler_dgse(linhas, inicio, caso) -> int:
        """Lê o bloco DGSE (§20.2) — associação de geradores síncronos eólicos (v1.5.4).

        Formato livre: Nb Gr P Q Und Mg Mt[u] Mv[u] Mc1[u] Mc2[u] Freq Vtr0 Vcap0
        """
        i = inicio
        while i < len(linhas):
            linha = _strip_comment(linhas[i])
            if _e_terminador(linha) or _e_fim(linha):
                return i + 1
            stripped = linha.strip()
            if not stripped:
                i += 1
                continue
            partes = stripped.split()
            try:
                nb = int(partes[0])
                gr = int(partes[1])
                p = _safe_float(partes[2]) if len(partes) > 2 else 100.0
                q = _safe_float(partes[3]) if len(partes) > 3 else 100.0
                und = int(partes[4]) if len(partes) > 4 else 1
                mg = int(partes[5]) if len(partes) > 5 else 0
                mt, mt_u = _sep_flag_u(partes[6]) if len(partes) > 6 else (0, False)
                mv, mv_u = _sep_flag_u(partes[7]) if len(partes) > 7 else (0, False)
                mc1, mc1_u = _sep_flag_u(partes[8]) if len(partes) > 8 else (0, False)
                mc2, mc2_u = _sep_flag_u(partes[9]) if len(partes) > 9 else (0, False)
                freq = _safe_float(partes[10]) if len(partes) > 10 else 0.0
                vtr0 = _safe_float(partes[11]) if len(partes) > 11 else 0.0
                vcap0 = _safe_float(partes[12]) if len(partes) > 12 else 0.0

                caso.dgse.adicionar(
                    nb=nb, gr=gr, p=p, q=q, und=und, mg=mg, mt=mt, mv=mv, mc1=mc1, mc2=mc2,
                    freq=freq, vtr0=vtr0, vcap0=vcap0,
                    mt_usuario=mt_u, mv_usuario=mv_u, mc1_usuario=mc1_u, mc2_usuario=mc2_u
                )
            except (ValueError, IndexError):
                pass
            i += 1
        return i

    @staticmethod
    def _ler_dcdu(linhas, inicio, caso) -> int:
        """Lê um bloco DCDU e popula caso.dcdu (se existir) ou ignora graciosamente."""
        from pynatem.cdu import parsear_dcdu, BlocoDCDU

        try:
            dcdu, proximo = parsear_dcdu(linhas, inicio)
            # Armazena em caso.dcdu se o atributo existir; caso contrário ignora
            if hasattr(caso, "dcdu"):
                caso.dcdu = dcdu
        except Exception:
            proximo = ParserSTB._pular_bloco(linhas, inicio + 1)
        return proximo

    @staticmethod
    def _pular_bloco(linhas, inicio) -> int:
        i = inicio
        while i < len(linhas):
            linha = _strip_comment(linhas[i])
            if _e_terminador(linha) or _e_fim(linha):
                return i + 1
            i += 1
        return i
