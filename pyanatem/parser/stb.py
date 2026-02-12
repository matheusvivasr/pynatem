"""
parser/stb.py – Leitura de arquivos STB do ANATEM.

Suporte:
    DARQ  – 8 subtipos singulares + DCDU/DBLT com múltiplos arquivos
    DSIM  – linha posicional + NPAS + MXIT
    DEVT  – eventos estruturados: APCB, RMCB, APCC, RMCC, ABLN, FCLN,
            ABSH, FCSH, ALTG; demais preservados como texto bruto
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

_DEVT_COM_CIRCUITO = {"APCC", "RMCC", "ABLN", "FCLN", "ABCI", "FECI", "MDCI"}
_DEVT_SIMPLES = {"APCB", "RMCB", "ABSH", "FCSH", "MDSH"}
_DEVT_MAQUINA = {"ALTG"}

_DPLT_BARRA = {"VBAR", "TBAR", "FREQ", "PCAG", "QCAG"}
_DPLT_MAQUINA = {"DELT", "OMEG", "PGER", "QGER", "ICAM", "EEXC", "VTER", "PELM", "PMEC"}
_DPLT_CIRCUITO = {"FLXP", "FLXQ", "FLXC"}


class ParserSTB:
    """Lê um arquivo STB e devolve um CasoAnatem populado."""

    @staticmethod
    def ler(caminho) -> "CasoAnatem":  # noqa: F821
        from pyanatem.caso import CasoAnatem

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
            elif kw == "DCST":
                i = ParserSTB._ler_dcst(linhas, i + 1, caso)
            elif kw.startswith("DCAR"):
                i = ParserSTB._ler_dcar(linhas, i, caso)
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
        i = inicio
        linha_pos_lida = False
        while i < len(linhas):
            linha = _strip_comment(linhas[i])
            if _e_terminador(linha) or _e_fim(linha):
                return i + 1
            partes = linha.split()
            if not partes:
                i += 1
                continue
            op = partes[0].upper()
            if op == "NPAS" and len(partes) >= 2:
                caso.dsim.npas = _safe_int(partes[1])
            elif op == "MXIT" and len(partes) >= 2:
                caso.dsim.mxit = _safe_int(partes[1])
            elif not linha_pos_lida:
                try:
                    vals = [float(p) for p in partes[:3]]
                    if len(vals) >= 1:
                        caso.dsim.tini = vals[0]
                    if len(vals) >= 2:
                        caso.dsim.tfim = vals[1]
                    if len(vals) >= 3:
                        caso.dsim.delt = vals[2]
                    linha_pos_lida = True
                except ValueError:
                    pass
            i += 1
        return i

    @staticmethod
    def _ler_devt(linhas, inicio, caso) -> int:
        from pyanatem.blocos import _Evento

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

            if cod in _DEVT_SIMPLES:
                tini = _safe_float(partes[1]) if len(partes) > 1 else 0.0
                nb1 = _safe_int(partes[2]) if len(partes) > 2 else 0
                r = _safe_float(partes[3]) if len(partes) > 3 else 0.0
                x = _safe_float(partes[4]) if len(partes) > 4 else 0.0
                caso.devt._eventos.append(
                    _Evento(codigo=cod, nb1=nb1, tini=tini, p1=r, p2=x)
                )

            elif cod in _DEVT_COM_CIRCUITO:
                tini = _safe_float(partes[1]) if len(partes) > 1 else 0.0
                nb1 = _safe_int(partes[2]) if len(partes) > 2 else 0
                nb2 = _safe_int(partes[3]) if len(partes) > 3 else 0
                nc = _safe_int(partes[4]) if len(partes) > 4 else 1
                p1 = _safe_float(partes[5]) if len(partes) > 5 else 0.0
                p2 = _safe_float(partes[6]) if len(partes) > 6 else 0.0
                caso.devt._eventos.append(
                    _Evento(
                        codigo=cod, nb1=nb1, nb2=nb2, nc=nc, tini=tini, p1=p1, p2=p2
                    )
                )

            elif cod in _DEVT_MAQUINA:
                tini = _safe_float(partes[1]) if len(partes) > 1 else 0.0
                nb1 = _safe_int(partes[2]) if len(partes) > 2 else 0
                nb2 = _safe_int(partes[3]) if len(partes) > 3 else 1
                p1 = _safe_float(partes[4]) if len(partes) > 4 else 0.0
                caso.devt._eventos.append(
                    _Evento(codigo=cod, nb1=nb1, nb2=nb2, tini=tini, p1=p1)
                )

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

        Layout de colunas (0-based, relativo ao início da linha de dados):
            Nb  : [0:6]    int
            Gr  : [6:10]   int
            P   : [10:14]  int opcional
            Q   : [14:18]  int opcional
            Und : [18:22]  int opcional
            Mg  : [22:28]  int opcional
            Mt  : [28:34]  int opcional
            cdu : [34]     'u'/'U' → mt_cdu=True
            Mv  : [35:41]  int opcional
            cdu : [41]     'u'/'U' → mv_cdu=True
            Me  : [42:48]  int opcional
            cdu : [48]     'u'/'U' → me_cdu=True
            Xvd : [49:57]  float opcional
            Nbc : [57:63]  int opcional
        """
        from pyanatem.blocos import _AssocMaquina

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
                barra = _slice_int(linha, 0, 6)
                grupo = _slice_int(linha, 6, 10)
                if barra is None or grupo is None:
                    raise ValueError("Nb ou Gr ausente")
                p = _slice_int(linha, 10, 14)
                q = _slice_int(linha, 14, 18)
                und = _slice_int(linha, 18, 22)
                mg = _slice_int(linha, 22, 28)
                mt = _slice_int(linha, 28, 34)
                mt_cdu = _slice_cdu(linha, 34)
                mv = _slice_int(linha, 35, 41)
                mv_cdu = _slice_cdu(linha, 41)
                me = _slice_int(linha, 42, 48)
                me_cdu = _slice_cdu(linha, 48)
                xvd = _slice_float(linha, 49, 57)
                nbc = _slice_int(linha, 57, 63)

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
        from pyanatem.blocos import BlocoDMDG

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
                de = _si(linha, 0, 6)
                pa = _si(linha, 6, 12)
                mt, mt_u = _sm(linha, 16, 23)
                if de is None or pa is None or mt is None:
                    raise ValueError("De/Pa/Mt ausente")
                caso.dltc.adicionar(
                    de=de,
                    pa=pa,
                    mt=mt,
                    nc=_si(linha, 12, 16) or 1,
                    nst=_si(linha, 39, 44) or 1,
                    mt_usuario=mt_u,
                    tmn=_sf(linha, 23, 31),
                    tmx=_sf(linha, 31, 39),
                    kbs=_si(linha, 44, 51),
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
    def _ler_dcdu(linhas, inicio, caso) -> int:
        """Lê um bloco DCDU e popula caso.dcdu (se existir) ou ignora graciosamente."""
        from pyanatem.cdu import parsear_dcdu, BlocoDCDU

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
