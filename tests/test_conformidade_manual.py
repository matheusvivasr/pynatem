"""
tests/test_conformidade_manual.py — Conformidade dos serializadores com o
Manual ANATEM 12.10 OFICIAL (https://see.cepel.br/manual/anatem/).

Cada teste reproduz, via API do pynatem, os MESMOS dados do exemplo oficial
do código correspondente e compara a saída char-a-char com as linhas do
manual (fontes .rst, espaçamento de colunas exato).

Diferente dos demais testes (consistência interna), estes validam
conformidade EXTERNA — se falharem, o deck gerado divergiu do formato que o
ANATEM espera.
"""

from pynatem.blocos import (
    BlocoDCAR,
    BlocoDEVT,
    BlocoDFLA,
    BlocoDLTC,
    BlocoDMAQ,
    BlocoDSIM,
)

_IGNORAR = {"DEVT", "DCAR", "DCAR IMPR", "DSIM", "DLTC", "DFLA", "DMAQ", "999999", "FIMFLA"}


def _linhas_dados(texto: str):
    """Extrai só as linhas de dados (sem cabeçalho, comentários, terminador)."""
    return [
        l.rstrip()
        for l in texto.split("\n")
        if l.strip() and not l.strip().startswith("(") and l.strip() not in _IGNORAR
    ]


def _igual(oficial: str, gerado: str) -> bool:
    # flag u/U: o próprio manual alterna a caixa (94U no DCER, 5300u no DLTC)
    return oficial.replace("u", "U") == gerado.replace("u", "U")


def _conferir(oficial: list, gerado: str):
    dados = _linhas_dados(gerado)
    assert len(dados) == len(oficial), f"nº de linhas: {len(dados)} != {len(oficial)}"
    for of, ger in zip(oficial, dados):
        assert _igual(of, ger), f"\noficial |{of}|\ngerado  |{ger}|"


def test_dmaq_conforme_manual():
    """DMAQ §46.41 — exemplo oficial da página codigos_execucao/dmaq."""
    b = BlocoDMAQ()
    b.adicionar_maquina(barra=1432, grupo=10, mg=751)
    b.adicionar_maquina(barra=3500, grupo=10, p=60, q=60, und=3, mg=753,
                        mt=78, mv=126, me=144, me_cdu=True)
    b.adicionar_maquina(barra=3500, grupo=20, p=40, q=40, und=2, mg=753,
                        mt=81, mv=126, me=39)
    _conferir([
        " 1432   10                751",
        " 3500   10  60  60   3    753     78    126    144u",
        " 3500   20  40  40   2    753     81    126     39",
    ], b.serializar())


def test_devt_conforme_manual():
    """DEVT §46.31 — exemplo oficial (APCB/RMCB/ABCI, colunas da régua)."""
    b = BlocoDEVT()
    b.curto_barra(barra=2, tini=0.05, tipo="APCB")
    b.curto_barra(barra=2, tini=0.25, tipo="RMCB")
    b.abertura_linha(de=2, para=3, tini=0.25)
    _conferir([
        "APCB      .05     2",
        "RMCB      .25     2",
        "ABCI      .25     2    3",
    ], b.serializar())


def test_dcar_conforme_manual():
    """DCAR §46.14 — parâmetros A/B/C/D em colunas fixas (52+)."""
    b = BlocoDCAR()
    b.adicionar(selecao="BARR     1 A BARR  9998", a=100, b=0, c=0, d=100)
    _conferir([
        "BARR     1 A BARR  9998                             100   0   0 100",
    ], b.serializar())


def test_dsim_conforme_manual():
    """DSIM — régua oficial ( Tmax ) (Stp) ( P ) ( I ) ( F )."""
    b = BlocoDSIM(tmax=10.0, stp=0.005, p=5)
    _conferir(["   10.00  .005     5"], b.serializar())


def test_dltc_conforme_manual():
    """DLTC §46.40 — exemplo oficial (OLTCs com e sem Tmn/Tmx/Kbs)."""
    b = BlocoDLTC()
    b.adicionar(de=4, pa=2, mt=1, nst=40)
    b.adicionar(de=6, pa=18, mt=3, tmn=0.9, tmx=1.1, nst=40, kbs=-20)
    b.adicionar(de=1, pa=2, mt=5300, mt_usuario=True, nst=1)
    _conferir([
        "    4       2         1               40",
        "    6      18         3    0.9   1.1  40    -20",
        "    1       2      5300u               1",
    ], b.serializar())


def test_dfla_conforme_manual():
    """DFLA §46.33 — exemplo oficial (área FRJ + 5 circuitos)."""
    b = BlocoDFLA()
    area = b.adicionar_area(na=20, ident="FRJ - Area RJ")
    area.adicionar_circuito(de=138, pa=140, nc=1)
    area.adicionar_circuito(de=138, pa=140, nc=2)
    area.adicionar_circuito(de=104, pa=183, nc=57)
    area.adicionar_circuito(de=104, pa=183, nc=59)
    area.adicionar_circuito(de=385, pa=149)
    _conferir([
        "  20 FRJ - Area RJ",
        "  138   140  1",
        "  138   140  2",
        "  104   183 57",
        "  104   183 59",
        "  385   149",
    ], b.serializar())


def test_mnemonicos_eventos_oficiais():
    """Nenhum evento emitido pode usar mnemônico inexistente no manual.

    Mnemônicos inválidos removidos: ABLN, FCLN, ABSH, FCSH, RMCC, ALTG.
    Oficiais: ABCI/FECI (circuito), APCL/RMCL (curto em circuito),
    MDSH (shunt), TRGT/TRGV (referência de regulador).
    """
    b = BlocoDEVT()
    b.curto_circuito(de=1, para=2, circ=1, tini=1.0)          # APCL
    b.curto_circuito(de=1, para=2, circ=1, tini=1.1, tipo="RMCL")
    b.abertura_linha(de=1, para=2, tini=0.5)                   # ABCI
    b.fechamento_linha(de=1, para=2, tini=1.5)                 # FECI
    b.modificacao_shunt(barra=7, tini=0.3, valor=-50.0)        # MDSH
    b.step_referencia(barra=3, unidade=1, tini=2.0, delta=5.0)  # TRGT
    t = b.serializar()
    oficiais = {"APCL", "RMCL", "ABCI", "FECI", "MDSH", "TRGT"}
    invalidos = {"ABLN", "FCLN", "ABSH", "FCSH", "RMCC", "ALTG"}
    for m in oficiais:
        assert m in t
    for m in invalidos:
        assert m not in t
