"""
reguas_mdxx.py — Réguas posicionais oficiais dos modelos predefinidos MDxx.

Cada régua é a linha de posições de campos publicada nos exemplos do Manual
ANATEM 12.10 oficial (https://see.cepel.br/manual/anatem/). Campos entre
parênteses ``(Ka )`` ocupam as colunas do grupo; rótulos soltos (``LS``,
``Fr``, ``C``...) ocupam as colunas do próprio rótulo. Valores são
right-aligned dentro do span do campo.

Cobertura: somente variantes cuja régua consta em exemplo oficial — para as
demais o manual publica apenas nome/descrição dos campos (sem colunas), e o
projeto não infere posições. A serialização dessas variantes permanece no
formato genérico (ver ``_BlocoModeloMDxx``).

Registros multilinha (ex.: DRGT MD12) têm uma régua por linha do registro.
"""

from typing import Dict, List, Optional, Tuple

# (código, variante) -> lista de réguas (uma por linha do registro)
REGUAS_MDXX: Dict[Tuple[str, str], List[str]] = {
    # ---- DMDG — modelos de gerador síncrono (§46.46) ----
    ("DMDG", "MD01"): [
        "(No)   (L'd)(Ra )( H )( D )(MVA)Fr M E",
    ],
    ("DMDG", "MD02"): [
        '(No)   (CS) (Ld )(Lq )(L\'d)     (L"d)(Ll )(T\'d)     (T"d)(T"q)',
        "(No)   (Ra )( H )( D )(MVA)Fr C",
    ],
    ("DMDG", "MD03"): [
        "(No)   (CS) (Ld )(Lq )(L'd)(L'q)(L\"d)(Ll )(T'd)(T'q)(T\"d)(T\"q)",
        "(No)   (Ra )( H )( D )(MVA)Fr C",
    ],
    # ---- DRGT — reguladores de tensão (§16.3 / §46.57) ----
    ("DRGT", "MD01"): [
        "(No)   (CS) (Ka )(Ke )(Kf )(Tm )(Ta )(Te )(Tf )(Lmn)(Lmx)LS",
    ],
    ("DRGT", "MD12"): [
        "(No)   (CS) (Ka )(Ke )(Kf )(Kp )(Ki )(Kg )(Tq )(Ta )(Te )(Tf1)(Tf2)",
        "(No)   (Ln1)(Lx1)(Ln2)(Lx2)(Ln3)(Lx3)L",
    ],
    ("DRGT", "MD15"): [
        "(No)   (Ka )(Kq1)(Kq2)(Kp )(Ki )(Ms )( T )(Ta )(Te )(Tq )(Tse)(Van)(Vax)",
    ],
    # ---- DRGV — reguladores de velocidade/turbina (§16.4 / §46.58) ----
    # DRGV MD01: régua do exemplo oficial + campos finais Pbg/Pbt documentados
    # na tabela de campos (§16.4) — o exemplo os deixa em branco; as colunas
    # seguem a grade uniforme de 5 da régua.
    ("DRGV", "MD01"): [
        "(No)   ( R )(Rp )(At )(Qnl)(Tw )(Tr )(Tf )(Tg )(Vel)(Lmn)(Lmx)(Dtb)( D )(Pbg)(Pbt)",
    ],
    ("DRGV", "MD04"): [
        "(No)   (Bp )(Bt )(At )(Qnl)(Tp )(Ty )(Td )(Ts )(Tg )(Tw )(Lmn)(Lmx)",
        "(No)   (Gmn)(Gmx)(Dtb)",
    ],
    # ---- DEST — estabilizadores/PSS (§16.5 / §46.29) ----
    ("DEST", "MD01"): [
        "(No)   ( K )( T )(T1 )(T2 )(T3 )(T4 )(Lmn)(Lmx)",
    ],
    ("DEST", "MD07"): [
        "(No)   (Kp )(T1 )(T2 )(T3 )(T4 )(T5 )(TR )(Ven)(Vex)(Vpn)(Vpx)",
    ],
    # ---- DMTC — controle de tap de OLTC (§14.1 / §46.52) ----
    ("DMTC", "MD01"): [
        "(No)   (Bm1)(Bm2)(TR )(TM )(TB )( T )(Vlm)",
    ],
    # ---- DECS — estabilizador de CSC (§46.26) ----
    ("DECS", "MD01"): [
        "(No)   ( K )(T1 )(T2 )(T3 )(T4 )(T5 )( Nb)Mq",
    ],
    # ---- DMCE — modelo de compensador estático (§46.42) ----
    ("DMCE", "MD01"): [
        "(No)   ( K )( T )(T1 )(T2 )",
    ],
    # ---- DMCS — modelo de CSC (§46.43) ----
    ("DMCS", "MD01"): [
        "(No)   (Ki )(Kp )(T1 )(T2 )",
    ],
    ("DMCS", "MD02"): [
        "(No)   (Kp )(T1 )(T2 )(DB )",
    ],
}


# Réguas oficiais de códigos de associação/dados (linha única) — colhidas
# dos exemplos do manual online oficial.
REGUAS_CODIGOS: Dict[str, str] = {
    "DVSI": "(Nv)   ( De) ( Pa) Nx np (  Cnvk  )M(Vb ) ( Rv)( Xv)(Vpt)(Vst)(St )(Tap) (Ne)",
    "DCNV": "(No)   (Gkb)(Amn)(Amx)(Gmn)( Mc )u( S1 )u( S2 )u( S3 )u( S4 )u",
    "DDFM": "( Nb)   Gr (P) (Q) Und ( Mg ) ( Mt )u( Mc )u(Xvd )(Nbc) ( Slip )uR I",
    "DGSE": "( Nb)   Gr (P) (Q) Und ( Mg ) ( Mt )u( Mv )u( Mc1)u( Mc2)u(Freq0)(Vtr0 )(Vcap0)",
    "DMOT": "( Nb)   Gr (  H ) ( K0 ) ( K1 ) ( K2 ) ( EXP) M ( Mt )",
}


def serializar_linha(regua: str, valores: list) -> str:
    """Serializa uma linha completa pelas colunas da régua (todos os campos).

    ``valores`` na ordem dos campos da régua; ``None`` deixa em branco.
    """
    campos = campos_da_regua(regua)
    fim_total = campos[-1][2] + 1 if campos else len(regua)
    canvas = [" "] * max(fim_total, len(regua))
    for (nome, a, b), v in zip(campos, valores):
        if v is None:
            continue
        larg = b - a + 1
        s = f"{_ajustar_valor(v, larg):>{larg}}"
        canvas[a : b + 1] = s
    return "".join(canvas).rstrip()


def campos_da_regua(regua: str) -> List[Tuple[str, int, int]]:
    """Extrai os campos de uma régua: lista de (nome, início, fim) inclusivos.

    Grupos ``(...)`` ocupam da abertura ao fechamento; rótulos soltos ocupam
    as próprias colunas do rótulo. O primeiro campo é sempre o identificador
    ``No`` (colunas 0-3).
    """
    campos: List[Tuple[str, int, int]] = []
    i = 0
    n = len(regua)
    while i < n:
        ch = regua[i]
        if ch == "(":
            j = regua.find(")", i)
            if j == -1:
                break
            campos.append((regua[i + 1 : j].strip(), i, j))
            i = j + 1
        elif ch != " ":
            j = i
            while j < n and regua[j] != " " and regua[j] != "(":
                j += 1
            token = regua[i:j].strip()
            if len(token) > 1 and token.isupper():
                # flags glued de 1 coluna cada (ex.: "LS" = campos L e S)
                for k, letra in enumerate(token):
                    campos.append((letra, i + k, i + k))
            elif len(token) > 1 and "u" in token:
                # 'u' minúsculo é flag de 1 coluna (ex.: "uR" = u + campo R)
                pos = i
                for letra in token:
                    campos.append((letra, pos, pos))
                    pos += 1
            else:
                campos.append((token, i, j - 1))
            i = j
        else:
            i += 1
    return campos


def _ajustar_valor(v, largura: int) -> str:
    """Formata um valor para caber em ``largura`` colunas (right-aligned).

    Ints ficam inteiros; floats usam a forma mais curta que preserva o valor
    e cabe no campo (reduzindo casas decimais e removendo o zero à esquerda
    quando necessário — estilos presentes nos exemplos oficiais).
    """
    if isinstance(v, str):
        return v[:largura]
    if isinstance(v, int):
        s = str(v)
        return s[:largura] if len(s) > largura else s
    if isinstance(v, float) and v.is_integer():
        s = f"{v:.1f}"  # estilo predominante dos exemplos oficiais: 7.0, 0.0
        if len(s) <= largura:
            return s
        return str(int(v))[:largura]
    # float não inteiro: tentar formas decrescentes de precisão
    for prec in range(min(largura, 12), -1, -1):
        s = f"{v:.{prec}f}"
        s = s.rstrip("0").rstrip(".") if "." in s else s
        if len(s) <= largura and float(s) == float(f"{v:.{prec}f}"):
            return s
        # sem o zero à esquerda (estilo .060 do manual)
        if s.startswith("0."):
            s2 = s[1:]
            if len(s2) <= largura:
                return s2
        elif s.startswith("-0."):
            s2 = "-" + s[2:]
            if len(s2) <= largura:
                return s2
    return f"{v:.0f}"[:largura]


def serializar_registro(
    codigo: str, variante: str, no: int, parametros: list, linha_idx: int = 0
) -> Optional[str]:
    """Serializa uma linha de registro MDxx nas colunas da régua oficial.

    Args:
        codigo: "DRGT", "DRGV", "DEST", "DMTC", "DMDG", ...
        variante: "MD01"...
        no: número de identificação do modelo (campo No, colunas 0-3).
        parametros: valores posicionais na ordem dos campos da régua
            (excluindo o No). ``None`` deixa o campo em branco.
        linha_idx: índice da linha do registro (registros multilinha).

    Retorna a linha serializada, ou ``None`` se não há régua oficial para a
    variante (chamador usa o fallback genérico).
    """
    reguas = REGUAS_MDXX.get((codigo.upper(), variante.upper()))
    if not reguas or linha_idx >= len(reguas):
        return None
    regua = reguas[linha_idx]
    campos = campos_da_regua(regua)
    fim_total = campos[-1][2] + 1 if campos else 80
    canvas = [" "] * max(fim_total, len(regua))

    # campo No (primeiro da régua)
    _, ini, fim = campos[0]
    s_no = f"{no:>{fim - ini + 1}}"
    canvas[ini : fim + 1] = s_no[-(fim - ini + 1) :]

    for (nome, ini, fim), valor in zip(campos[1:], parametros):
        if valor is None:
            continue
        larg = fim - ini + 1
        s = _ajustar_valor(valor, larg)
        s = f"{s:>{larg}}"
        canvas[ini : fim + 1] = s
    return "".join(canvas).rstrip()


def n_linhas_registro(codigo: str, variante: str) -> int:
    """Número de linhas de um registro da variante (1 se régua desconhecida)."""
    reguas = REGUAS_MDXX.get((codigo.upper(), variante.upper()))
    return len(reguas) if reguas else 1


def regua_oficial(codigo: str, variante: str, linha_idx: int = 0) -> Optional[str]:
    """Devolve a régua oficial (linha-comentário) da variante, se conhecida."""
    reguas = REGUAS_MDXX.get((codigo.upper(), variante.upper()))
    if reguas and linha_idx < len(reguas):
        return reguas[linha_idx]
    return None
