"""
tests/test_pyanatem.py – Suite de testes para o pyanatem.
"""

import sys, tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from pyanatem import CasoAnatem, EnsaioAnatem, LeitorPLT, LeitorRelatorio
from pyanatem.blocos import BlocoDEVT, BlocoDPLT, BlocoDARQ, BlocoDSIM

# ===========================================================================
# BLOCOS – serialização básica (sessão 2)
# ===========================================================================


def test_darq_todos_subtipos():
    d = BlocoDARQ()
    d.sav = "rede.sav"
    d.rela = "saida.rela"
    d.log = "log.log"
    d.plt = "plot.plt"
    d.plt_cdu = "cdu.plt"
    d.adicionar_cdu("ctrl.cdu")
    d.adicionar_blt("bib.blt")
    t = d.serializar()
    assert "SIST" in t and "rede.sav" in t
    assert "RELA" in t and "saida.rela" in t
    assert "LOGI" in t and "log.log" in t
    assert "PLOT" in t and "plot.plt" in t
    assert "PLOC" in t and "cdu.plt" in t
    assert "DCDU" in t and "ctrl.cdu" in t
    assert "DBLT" in t and "bib.blt" in t
    assert t.strip().endswith("999999")


def test_darq_alias_out():
    d = BlocoDARQ()
    d.out = "saida.out"
    assert d.rela == "saida.out"
    assert "RELA" in d.serializar()


def test_dsim_linha_posicional():
    d = BlocoDSIM(tini=0.0, tfim=5.0, delt=0.005)
    t = d.serializar()
    assert "0.0000" in t and "5.0000" in t and "0.0050" in t


def test_dsim_opcoes():
    d = BlocoDSIM(tfim=10.0, delt=0.01)
    d.npas = 2
    d.mxit = 50
    t = d.serializar()
    assert "NPAS  2" in t and "MXIT  50" in t


def test_devt_curto_barra():
    d = BlocoDEVT()
    d.curto_barra(barra=5, tini=1.0, tipo="APCB")
    d.curto_barra(barra=5, tini=1.1, tipo="RMCB")
    t = d.serializar()
    assert "APCB" in t and "RMCB" in t and "1.0000" in t and "1.1000" in t


def test_devt_curto_circuito():
    d = BlocoDEVT()
    d.curto_circuito(de=10, para=20, circ=1, tini=2.0, tipo="APCC")
    d.curto_circuito(de=10, para=20, circ=1, tini=2.1, tipo="RMCC")
    t = d.serializar()
    assert "APCC" in t and "RMCC" in t and "10" in t and "20" in t


def test_devt_abertura_e_fechamento():
    d = BlocoDEVT()
    d.abertura_linha(de=1, para=2, tini=0.5)
    d.fechamento_linha(de=1, para=2, tini=1.5)
    t = d.serializar()
    assert "ABLN" in t and "FCLN" in t


def test_devt_shunt_e_step():
    d = BlocoDEVT()
    d.abertura_shunt(barra=7, tini=0.3)
    d.fechamento_shunt(barra=7, tini=1.3)
    d.step_referencia(barra=3, unidade=1, tini=2.0, delta=0.05)
    t = d.serializar()
    assert "ABSH" in t and "FCSH" in t and "ALTG" in t


def test_dplt_barras_maquinas_circuitos_cargas():
    d = BlocoDPLT()
    d.tensao_barra(5)
    d.angulo_barra(5)
    d.frequencia_barra(5)
    d.angulo_maquina(5, 1)
    d.velocidade_maquina(5, 1)
    d.potencia_ativa(5, 1)
    d.potencia_reativa(5, 1)
    d.corrente_campo(5, 1)
    d.tensao_excitacao(5, 1)
    d.tensao_terminal(5, 1)
    d.potencia_eletrica(5, 1)
    d.potencia_mecanica(5, 1)
    d.fluxo_ativo(10, 20, 1)
    d.fluxo_reativo(10, 20, 1)
    d.corrente_circuito(10, 20, 1)
    d.potencia_carga(3)
    d.reativo_carga(3)
    t = d.serializar()
    for cod in [
        "VBAR",
        "TBAR",
        "FREQ",
        "DELT",
        "OMEG",
        "PGER",
        "QGER",
        "ICAM",
        "EEXC",
        "VTER",
        "PELM",
        "PMEC",
        "FLXP",
        "FLXQ",
        "FLXC",
        "PCAG",
        "QCAG",
    ]:
        assert cod in t, f"Faltando {cod}"


# ===========================================================================
# BLOCOS – novidades sessão 3: OLTC / FACTS / HVDC / CDU
# ===========================================================================


def test_dplt_oltc():
    # §13.3.1: tap do transformador = TAP (régua El/Pa/Nc)
    d = BlocoDPLT()
    d.tap_oltc(de=10, para=20, circ=1)
    assert "TAP" in d.serializar()


def test_dplt_facts_svc():
    # §25.4: CER = QCES/BCES/ICES/VCES (régua barra + grupo)
    d = BlocoDPLT()
    d.reativo_svc(5)
    d.tensao_svc(5)
    d.susceptancia_svc(5)
    d.corrente_svc(5)
    t = d.serializar()
    assert "QCES" in t and "VCES" in t and "BCES" in t and "ICES" in t


def test_dplt_facts_tcsc():
    # §26.4: CSC = XCSC/BCSC/ICSC (régua De/Para/Nc)
    d = BlocoDPLT()
    d.reatancia_tcsc(10, 20, 1)
    d.susceptancia_tcsc(10, 20, 1)
    d.corrente_tcsc(10, 20, 1)
    t = d.serializar()
    assert "XCSC" in t and "BCSC" in t and "ICSC" in t


def test_dplt_facts_statcom():
    # §27.5: VSI = QVSI/PVSI/IMVSI/ETMVSI (régua conversor)
    d = BlocoDPLT()
    d.reativo_statcom(3)
    d.ativo_statcom(3)
    d.tensao_interna_statcom(3)
    t = d.serializar()
    assert "QVSI" in t and "PVSI" in t and "ETMVSI" in t


def test_dplt_hvdc():
    # §24.6.1: conversor CA-CC = VCNV/CCNV/PCNV/ALFA/GAMA (régua conversor)
    d = BlocoDPLT()
    d.tensao_cc(1)
    d.corrente_cc(1)
    d.potencia_cc(1)
    d.angulo_disparo(1)
    d.angulo_extincao(1)
    t = d.serializar()
    for cod in ["VCNV", "CCNV", "PCNV", "ALFA", "GAMA"]:
        assert cod in t


def test_dplt_saida_cdu():
    # §29.10: variável de saída/estado de CDU = tipo CDU / CDUE
    d = BlocoDPLT()
    d.saida_cdu(num_cdu=2, num_bloco=7)
    d.estado_cdu(num_cdu=2, num_bloco=8)
    t = d.serializar()
    assert "CDU " in t and "CDUE" in t and "2" in t and "7" in t


def test_dplt_facts_hvdc_roundtrip(tmp_path):
    """As linhas DPLT 4-letra sobrevivem ao roundtrip export → ler."""
    from pyanatem import CasoAnatem

    caso = CasoAnatem()
    caso.darq.sav = "rede.sav"
    caso.dplt.reativo_svc(5, grupo=1)  # QCES
    caso.dplt.reatancia_tcsc(10, 20, 1)  # XCSC
    caso.dplt.reativo_statcom(3)  # QVSI
    caso.dplt.tensao_cc(1)  # VCNV
    caso.dplt.saida_cdu(2, 7)  # CDU
    p = tmp_path / "dplt.stb"
    caso.exportar(p)

    conteudo = p.read_text(encoding="latin-1")
    for cod in ("QCES", "XCSC", "QVSI", "VCNV", "CDU"):
        assert cod in conteudo

    lido = CasoAnatem.ler(p)
    texto_lido = "\n".join(lido.dplt.linhas)
    for cod in ("QCES", "XCSC", "QVSI", "VCNV", "CDU"):
        assert cod in texto_lido


# ===========================================================================
# BLOCOS – novidade sessão 3: DARQ múltiplos arquivos
# ===========================================================================


def test_darq_multiplos_cdu():
    d = BlocoDARQ()
    d.adicionar_cdu("avr.cdu")
    d.adicionar_cdu("pss.cdu")
    d.adicionar_cdu("gov.cdu")
    assert d.cdu == "avr.cdu"
    assert d.cdu_extras == ["pss.cdu", "gov.cdu"]
    assert d.todos_cdu() == ["avr.cdu", "pss.cdu", "gov.cdu"]
    t = d.serializar()
    assert t.count("DCDU") == 3


def test_darq_multiplos_blt():
    d = BlocoDARQ()
    d.adicionar_blt("modelos1.blt")
    d.adicionar_blt("modelos2.blt")
    assert d.todos_blt() == ["modelos1.blt", "modelos2.blt"]
    assert d.serializar().count("DBLT") == 2


def test_darq_cdu_setter_direto_mais_adicionar():
    """Setar .cdu diretamente e depois usar adicionar_cdu deve empilhar."""
    d = BlocoDARQ()
    d.cdu = "principal.cdu"
    d.adicionar_cdu("extra.cdu")
    assert d.todos_cdu() == ["principal.cdu", "extra.cdu"]


# ===========================================================================
# CasoAnatem – API de alto nível
# ===========================================================================


def test_deck_estrutura():
    caso = CasoAnatem()
    caso.darq.sav = "rede.sav"
    caso.dsim.tfim = 5.0
    deck = caso.deck()
    for bloco in ["DARQ", "DEVT", "DPLT", "DSIM", "EXSI", "FIM"]:
        assert bloco in deck


def test_curto_barra_alto_nivel():
    caso = CasoAnatem()
    caso.curto_barra(barra=42, t_apl=1.0, t_rem=1.1)
    deck = caso.deck()
    assert "APCB" in deck and "RMCB" in deck and "42" in deck


def test_curto_circuito_alto_nivel():
    caso = CasoAnatem()
    caso.curto_circuito(de=10, para=20, circ=1, t_apl=1.0, t_rem=1.1)
    deck = caso.deck()
    assert "APCC" in deck and "RMCC" in deck


def test_abrir_e_fechar_linha():
    caso = CasoAnatem()
    caso.abrir_linha_e_fechar(de=10, para=20, t_aber=0.5, t_fech=1.5)
    deck = caso.deck()
    assert "ABLN" in deck and "FCLN" in deck


def test_alterar_dsim_attr_invalido():
    caso = CasoAnatem()
    try:
        caso.alterar_dsim(inexistente=1.0)
        assert False, "Deveria lançar AttributeError"
    except AttributeError:
        pass


def test_copiar_independente():
    caso = CasoAnatem()
    caso.darq.sav = "base.sav"
    copia = caso.copiar()
    copia.darq.sav = "outro.sav"
    assert caso.darq.sav == "base.sav"


# ===========================================================================
# validar() – sessão 2 + expansões sessão 3
# ===========================================================================


def test_validar_sem_sav():
    caso = CasoAnatem()
    assert any("SAV" in e for e in caso.validar())


def test_validar_tfim_invalido():
    caso = CasoAnatem()
    caso.darq.sav = "x.sav"
    caso.dsim.tini = 5.0
    caso.dsim.tfim = 3.0
    assert any("tfim" in e for e in caso.validar())


def test_validar_apcb_sem_rmcb():
    caso = CasoAnatem()
    caso.darq.sav = "x.sav"
    caso.devt.curto_barra(barra=5, tini=1.0, tipo="APCB")
    assert any("APCB" in e for e in caso.validar())


def test_validar_caso_ok():
    caso = CasoAnatem()
    caso.darq.sav = "x.sav"
    caso.dsim.tfim = 10.0
    caso.curto_barra(barra=5, t_apl=1.0, t_rem=1.1)
    assert caso.validar() == []


def test_validar_poucos_passos():
    """Novo (sessão 3): tfim muito curto perto de delt gera aviso."""
    caso = CasoAnatem()
    caso.darq.sav = "x.sav"
    caso.dsim.tini = 0.0
    caso.dsim.tfim = 0.05  # só 5 passos com delt=0.01
    caso.dsim.delt = 0.01
    erros = caso.validar()
    assert any("passos de integração" in e for e in erros)


def test_validar_eventos_sobrepostos():
    """Novo (sessão 3): dois eventos diferentes na mesma barra/instante."""
    caso = CasoAnatem()
    caso.darq.sav = "x.sav"
    caso.dsim.tfim = 10.0
    caso.devt.curto_barra(barra=5, tini=1.0, tipo="APCB")
    caso.devt.abertura_shunt(
        barra=5, tini=1.0
    )  # mesmo nb1, mesmo tini, código diferente
    erros = caso.validar()
    assert any("sobrepost" in e or "mesmo instante" in e for e in erros)


def test_validar_evento_depois_de_tfim():
    """Novo (sessão 3): evento em t > tfim nunca executa."""
    caso = CasoAnatem()
    caso.darq.sav = "x.sav"
    caso.dsim.tfim = 5.0
    caso.devt.curto_barra(barra=5, tini=6.0, tipo="APCB")
    caso.devt.curto_barra(barra=5, tini=6.1, tipo="RMCB")
    erros = caso.validar()
    assert any("depois de tfim" in e for e in erros)


# ===========================================================================
# Exportar / Ler (roundtrip)
# ===========================================================================


def test_exportar_cria_arquivo():
    caso = CasoAnatem()
    caso.darq.sav = "x.sav"
    caso.dsim.tfim = 3.0
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "teste.stb"
        caso.exportar(out)
        assert out.exists()
        txt = out.read_text(encoding="latin-1")
        assert "DARQ" in txt and "FIM" in txt


def test_roundtrip_darq_dsim():
    stb = """\
( caso de teste roundtrip
DARQ
SIST    sistema.sav
PLOT    saida.plt
LOGI    log.log
999999
DSIM
    0.0000   15.0000    0.0050
999999
DEVT
999999
DPLT
999999
EXSI
FIM
"""
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp) / "rt.stb"
        p.write_text(stb, encoding="latin-1")
        caso = CasoAnatem.ler(p)
        assert caso.darq.sav == "sistema.sav"
        assert caso.darq.plt == "saida.plt"
        assert caso.darq.log == "log.log"
        assert caso.dsim.tfim == 15.0
        assert caso.dsim.delt == 0.005


def test_roundtrip_devt_eventos():
    stb = """\
DARQ
SIST rede.sav
999999
DSIM
0.0 10.0 0.01
999999
DEVT
APCB      5      1.0000      0.0000      0.0000
RMCB      5      1.1000      0.0000      0.0000
ABLN     10     20    1      2.0000
999999
DPLT
999999
EXSI
FIM
"""
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp) / "devt.stb"
        p.write_text(stb, encoding="latin-1")
        caso = CasoAnatem.ler(p)
        codigos = [e.codigo for e in caso.devt._eventos]
        assert codigos.count("APCB") == 1 and "RMCB" in codigos and "ABLN" in codigos


def test_roundtrip_darq_multiplos_cdu():
    """Novo (sessão 3): 2 linhas DCDU devem virar 2 itens em todos_cdu()."""
    stb = """\
DARQ
SIST rede.sav
DCDU avr.cdu
DCDU pss.cdu
999999
DSIM
0.0 5.0 0.01
999999
DEVT
999999
DPLT
999999
EXSI
FIM
"""
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp) / "multicdu.stb"
        p.write_text(stb, encoding="latin-1")
        caso = CasoAnatem.ler(p)
        assert caso.darq.todos_cdu() == ["avr.cdu", "pss.cdu"]


# ===========================================================================
# EnsaioAnatem
# ===========================================================================


def test_ensaio_novo_caso_isolado():
    ensaio = EnsaioAnatem.novo()
    ensaio._template.darq.sav = "base.sav"
    c1 = ensaio.novo_caso("a")
    c2 = ensaio.novo_caso("b")
    c1.darq.sav = "alterado.sav"
    assert c2.darq.sav == "base.sav"


def test_ensaio_gerar_variacoes():
    ensaio = EnsaioAnatem.novo()
    ensaio._template.darq.sav = "base.sav"
    ensaio._template.dsim.tfim = 5.0

    def mod(caso, i):
        caso.dsim.tfim = 5.0 + i

    with tempfile.TemporaryDirectory() as tmp:
        paths = ensaio.gerar_variacoes(mod, n=3, diretorio=tmp, prefixo="cen")
        assert len(paths) == 3
        for i, p in enumerate(paths):
            assert p.exists()
            assert str(5 + i) in p.read_text(encoding="latin-1")


def test_ensaio_sem_exe_levanta_erro():
    ensaio = EnsaioAnatem.novo()
    with tempfile.TemporaryDirectory() as tmp:
        stb = Path(tmp) / "teste.stb"
        CasoAnatem().exportar(stb)
        try:
            ensaio.executar(stb)
            assert False, "Deveria ter lançado RuntimeError"
        except RuntimeError as e:
            assert "Executável" in str(e)


# ===========================================================================
# Pós-processamento (sessão 3): LeitorPLT / LeitorRelatorio
# ===========================================================================


def test_leitor_plt_texto_simples():
    conteudo = """\
TEMPO   VBAR5   DELT5
0.00    1.0000  0.0000
0.01    0.9998  0.1200
0.02    0.9990  0.2350
"""
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp) / "saida.plt"
        p.write_text(conteudo, encoding="latin-1")
        r = LeitorPLT.ler(p)
        assert r.variaveis == ["VBAR5", "DELT5"]
        assert r.tempo == [0.00, 0.01, 0.02]
        assert r.valores("VBAR5") == [1.0000, 0.9998, 0.9990]
        assert r.valores("DELT5")[2] == 0.2350


def test_leitor_plt_variavel_inexistente():
    conteudo = "TEMPO  X\n0.0  1.0\n"
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp) / "t.plt"
        p.write_text(conteudo, encoding="latin-1")
        r = LeitorPLT.ler(p)
        try:
            r.valores("NAO_EXISTE")
            assert False
        except KeyError as e:
            assert "NAO_EXISTE" in str(e)


def test_leitor_plt_para_dict():
    conteudo = "TEMPO  A\n0.0  1.0\n0.1  2.0\n"
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp) / "t.plt"
        p.write_text(conteudo, encoding="latin-1")
        r = LeitorPLT.ler(p)
        d = r.para_dict()
        assert d["tempo"] == [0.0, 0.1]
        assert d["A"] == [1.0, 2.0]


def test_leitor_plt_detecta_binario():
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp) / "bin.plt"
        # gera conteúdo com muitos bytes de controle (simula binário)
        conteudo_binario = bytes([0, 1, 2, 3, 4, 5, 200, 201] * 300)
        p.write_bytes(conteudo_binario)
        try:
            LeitorPLT.ler(p)
            assert False, "Deveria ter detectado formato binário"
        except ValueError as e:
            assert "binário" in str(e)


def test_leitor_relatorio_sucesso():
    conteudo = """\
INICIANDO SIMULACAO
PASSO 1 OK
CONVERGIU EM 3 ITERACOES
FIM NORMAL DA EXECUCAO
"""
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp) / "ok.rela"
        p.write_text(conteudo, encoding="latin-1")
        r = LeitorRelatorio.ler(p)
        assert r.convergiu is True
        assert r.erros == []


def test_leitor_relatorio_erro():
    conteudo = """\
INICIANDO SIMULACAO
ERRO: MATRIZ SINGULAR NA BARRA 10
SIMULACAO NAO CONVERGIU
"""
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp) / "erro.log"
        p.write_text(conteudo, encoding="latin-1")
        r = LeitorRelatorio.ler(p)
        assert r.convergiu is False
        assert len(r.erros) >= 1


def test_leitor_relatorio_aviso():
    conteudo = "AVISO: TENSAO BAIXA NA BARRA 3\nCONVERGIU\n"
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp) / "aviso.log"
        p.write_text(conteudo, encoding="latin-1")
        r = LeitorRelatorio.ler(p)
        assert len(r.avisos) == 1
        assert r.convergiu is True


def test_leitor_relatorio_indeterminado():
    conteudo = "linha qualquer sem palavras-chave\noutra linha\n"
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp) / "vazio.log"
        p.write_text(conteudo, encoding="latin-1")
        r = LeitorRelatorio.ler(p)
        assert r.convergiu is None


# ===========================================================================
# Runner manual (sem pytest)
# ===========================================================================

if __name__ == "__main__":
    import traceback

    testes = [
        (k, v)
        for k, v in list(globals().items())
        if k.startswith("test_") and callable(v)
    ]
    ok = fail = 0
    for nome, fn in testes:
        try:
            fn()
            print(f"  PASS  {nome}")
            ok += 1
        except Exception as e:
            print(f"  FAIL  {nome}: {e}")
            traceback.print_exc()
            fail += 1
    print(f"\n{ok} passed, {fail} failed")


# ===========================================================================
# DMDG – introduzido em v0.4.1 (etapa 0.4)
# ===========================================================================

from pyanatem import BlocoDMDG, BlocoDRGT

# ===========================================================================
# v1.2.1 – DRGT: reguladores de tensão predefinidos (§16.3)
# ===========================================================================


def test_drgt_md01_nomeado():
    """MD01 (§16.3): construtor nomeado emite No + parâmetros na ordem da régua."""
    b = BlocoDRGT()
    b.adicionar_md01(
        no=1,
        cs=0,
        ka=200.0,
        ke=1.0,
        kf=0.05,
        tm=0.0,
        ta=0.05,
        te=0.5,
        tf=1.0,
        lmn=-5.0,
        lmx=5.0,
        l="D",
        s="I",
    )
    t = b.serializar()
    assert "DRGT MD01" in t
    assert "200" in t and "-5" in t and "5" in t
    assert t.rstrip().endswith("999999")


def test_drgt_generico_qualquer_modelo():
    """adicionar() aceita qualquer MDxx via parâmetros posicionais."""
    b = BlocoDRGT()
    b.adicionar("MD05", 2, 0.5, 1.0, 2.0, "D")  # 4 params posicionais
    b.adicionar(7, 3, 10.0)  # inteiro 7 → 'MD07'
    t = b.serializar()
    assert "DRGT MD05" in t and "DRGT MD07" in t


def test_roundtrip_drgt(tmp_path):
    """DRGT: export → ler preserva variante, No e parâmetros (MD01 + MD05)."""
    from pyanatem import CasoAnatem

    caso = CasoAnatem()
    caso.darq.sav = "rede.sav"
    caso.drgt.adicionar_md01(
        no=1,
        cs=0,
        ka=200.0,
        ke=1.0,
        kf=0.05,
        tm=0.0,
        ta=0.05,
        te=0.5,
        tf=1.0,
        lmn=-5.0,
        lmx=5.0,
        l="D",
        s="I",
    )
    caso.drgt.adicionar("MD05", 2, 0.5, 1.0, 2.0)
    p = tmp_path / "drgt.stb"
    caso.exportar(p)

    lido = CasoAnatem.ler(p)
    assert len(lido.drgt._modelos) == 2
    m1, m5 = lido.drgt._modelos
    assert (m1.modelo, m1.no) == ("MD01", 1)
    assert m1.parametros[0] == 0  # Cs
    assert 200.0 in m1.parametros and "D" in m1.parametros and "I" in m1.parametros
    assert (m5.modelo, m5.no) == ("MD05", 2)
    assert m5.parametros == [0.5, 1.0, 2.0]

    # idempotência textual da serialização
    assert lido.drgt.serializar() == caso.drgt.serializar()


def test_drgt_aparece_no_deck_antes_de_dmaq():
    """deck() emite DRGT entre DMDG e DMAQ quando populado."""
    from pyanatem import CasoAnatem

    caso = CasoAnatem()
    caso.darq.sav = "rede.sav"
    caso.drgt.adicionar_md01(
        no=1,
        cs=0,
        ka=200.0,
        ke=1.0,
        kf=0.0,
        tm=0.0,
        ta=0.05,
        te=0.5,
        tf=1.0,
        lmn=-5.0,
        lmx=5.0,
    )
    caso.adicionar_maquina(barra=100, grupo=1, mv=1)
    stb = caso.deck()
    assert "DRGT MD01" in stb
    assert stb.find("DRGT") < stb.find("DMAQ")


def test_dmdg_md01_serializa_campos_basicos():
    """MD01: No, L'd, Ra, H, D, MVA presentes na saída."""
    b = BlocoDMDG()
    b.adicionar_md01(no=20, ld=20.0, h=999.0, mva=9999.0)
    t = b.serializar()
    assert "DMDG MD01" in t
    assert "20" in t
    assert "20.000" in t  # ld
    assert "999.000" in t  # h
    assert "9999.0" in t  # mva
    assert "999999" in t


def test_dmdg_md01_corfreq_s():
    """MD01: quando corfreq='S', o caractere 'S' aparece na linha."""
    b = BlocoDMDG()
    b.adicionar_md01(no=1, ld=25.0, h=5.0, mva=100.0, corfreq="S")
    t = b.serializar()
    assert "S" in t


def test_dmdg_md01_multiplos():
    """MD01: múltiplos modelos geram um bloco único com terminador único."""
    b = BlocoDMDG()
    b.adicionar_md01(no=1, ld=20.0, h=5.0, mva=100.0)
    b.adicionar_md01(no=2, ld=25.0, h=6.0, mva=200.0)
    t = b.serializar()
    assert t.count("DMDG MD01") == 1
    assert t.count("999999") == 1
    assert "1 " in t or "   1" in t
    assert "2 " in t or "   2" in t


def test_dmdg_md02_duas_reguas():
    """MD02: cada modelo serializa duas réguas com o mesmo No."""
    b = BlocoDMDG()
    b.adicionar_md02(
        no=14,
        ld=170.0,
        lq=100.0,
        ld_trans=37.0,
        ld_sub=22.0,
        ll=15.4,
        td_trans=9.00,
        td_sub=0.060,
        tq_sub=0.200,
        ra=1.6,
        h=300.0,
        mva=100.0,
    )
    t = b.serializar()
    assert "DMDG MD02" in t
    assert "14" in t
    # valores da régua 1
    assert "170.000" in t
    assert "100.000" in t
    assert "37.000" in t
    # valores da régua 2
    assert "300.000" in t  # h
    assert "100.0" in t  # mva
    # duas linhas com "14" (régua 1 e régua 2)
    linhas_com_14 = [l for l in t.splitlines() if l.strip().startswith("14")]
    assert len(linhas_com_14) == 2


def test_dmdg_md03_campos_extras():
    """MD03: L'q e T'q presentes na saída (diferença em relação ao MD02)."""
    b = BlocoDMDG()
    b.adicionar_md03(
        no=50,
        ld=180.0,
        lq=170.0,
        ld_trans=28.0,
        lq_trans=45.0,
        ld_sub=20.0,
        ll=14.0,
        td_trans=8.0,
        tq_trans=1.5,
        td_sub=0.04,
        tq_sub=0.07,
        h=4.5,
        mva=500.0,
    )
    t = b.serializar()
    assert "DMDG MD03" in t
    assert "45.000" in t  # lq_trans
    assert "1.5000" in t  # tq_trans


def test_dmdg_mistura_md01_md02():
    """MD01 e MD02 no mesmo BlocoDMDG geram sub-blocos independentes."""
    b = BlocoDMDG()
    b.adicionar_md01(no=10, ld=20.0, h=5.0, mva=100.0)
    b.adicionar_md02(
        no=20,
        ld=150.0,
        lq=90.0,
        ld_trans=30.0,
        ld_sub=20.0,
        ll=12.0,
        td_trans=7.0,
        td_sub=0.05,
        tq_sub=0.15,
        h=4.0,
        mva=200.0,
    )
    t = b.serializar()
    assert "DMDG MD01" in t
    assert "DMDG MD02" in t
    # cada sub-bloco tem seu próprio 999999
    assert t.count("999999") == 2


def test_dmdg_tem_dados_vazio():
    """BlocoDMDG vazio: tem_dados() retorna False."""
    b = BlocoDMDG()
    assert not b.tem_dados()


def test_dmdg_tem_dados_preenchido():
    """BlocoDMDG com modelos: tem_dados() retorna True."""
    b = BlocoDMDG()
    b.adicionar_md01(no=1, ld=20.0, h=5.0, mva=100.0)
    assert b.tem_dados()


def test_dmdg_encadeamento():
    """Métodos adicionar_mdXX retornam self para encadeamento fluente."""
    b = BlocoDMDG()
    result = b.adicionar_md01(no=1, ld=20.0, h=5.0, mva=100.0).adicionar_md02(
        no=2,
        ld=150.0,
        lq=90.0,
        ld_trans=30.0,
        ld_sub=20.0,
        ll=12.0,
        td_trans=7.0,
        td_sub=0.05,
        tq_sub=0.15,
    )
    assert result is b


def test_dmdg_aparece_no_deck():
    """BlocoDMDG com dados deve aparecer no deck gerado por CasoAnatem."""
    caso = CasoAnatem()
    caso.darq.sav = "rede.sav"
    caso.dmdg.adicionar_md01(no=1, ld=20.0, h=5.0, mva=100.0)
    d = caso.deck()
    assert "DMDG MD01" in d


def test_dmdg_nao_aparece_no_deck_vazio():
    """BlocoDMDG sem dados não deve aparecer no deck."""
    caso = CasoAnatem()
    caso.darq.sav = "rede.sav"
    assert "DMDG" not in caso.deck()


def test_dmdg_roundtrip_md01(tmp_path):
    """Roundtrip STB: DMDG MD01 escrito e relido preserva valores."""
    caso = CasoAnatem()
    caso.darq.sav = "rede.sav"
    caso.darq.plt = "saida.plt"
    caso.dsim.tfim = 5.0
    caso.dmdg.adicionar_md01(no=42, ld=22.5, h=6.0, mva=150.0, ra=0.5)

    stb = tmp_path / "caso.stb"
    caso.exportar(stb)

    lido = CasoAnatem.ler(stb)
    assert lido.dmdg.tem_dados()
    assert len(lido.dmdg._md01) == 1
    m = lido.dmdg._md01[0]
    assert m.no == 42
    assert abs(m.ld - 22.5) < 0.01
    assert abs(m.h - 6.0) < 0.01
    assert abs(m.mva - 150.0) < 0.1
    assert abs(m.ra - 0.5) < 0.01


def test_dmdg_roundtrip_md02(tmp_path):
    """Roundtrip STB: DMDG MD02 escrito e relido preserva valores."""
    caso = CasoAnatem()
    caso.darq.sav = "rede.sav"
    caso.darq.plt = "saida.plt"
    caso.dsim.tfim = 5.0
    caso.dmdg.adicionar_md02(
        no=14,
        ld=170.0,
        lq=100.0,
        ld_trans=37.0,
        ld_sub=22.0,
        ll=15.4,
        td_trans=9.00,
        td_sub=0.060,
        tq_sub=0.200,
        ra=1.6,
        h=300.0,
        mva=100.0,
    )

    stb = tmp_path / "caso.stb"
    caso.exportar(stb)

    lido = CasoAnatem.ler(stb)
    assert len(lido.dmdg._md02) == 1
    m = lido.dmdg._md02[0]
    assert m.no == 14
    assert abs(m.ld - 170.0) < 0.1
    assert abs(m.lq - 100.0) < 0.1
    assert abs(m.h - 300.0) < 0.1
    assert abs(m.td_trans - 9.00) < 0.01


def test_dmdg_roundtrip_md03(tmp_path):
    """Roundtrip STB: DMDG MD03 escrito e relido preserva valores."""
    caso = CasoAnatem()
    caso.darq.sav = "rede.sav"
    caso.darq.plt = "saida.plt"
    caso.dsim.tfim = 5.0
    caso.dmdg.adicionar_md03(
        no=50,
        ld=180.0,
        lq=170.0,
        ld_trans=28.0,
        lq_trans=45.0,
        ld_sub=20.0,
        ll=14.0,
        td_trans=8.0,
        tq_trans=1.5,
        td_sub=0.04,
        tq_sub=0.07,
        h=4.5,
        mva=500.0,
    )

    stb = tmp_path / "caso.stb"
    caso.exportar(stb)

    lido = CasoAnatem.ler(stb)
    assert len(lido.dmdg._md03) == 1
    m = lido.dmdg._md03[0]
    assert m.no == 50
    assert abs(m.lq_trans - 45.0) < 0.1
    assert abs(m.tq_trans - 1.5) < 0.01
    assert abs(m.mva - 500.0) < 0.1


# ===========================================================================
# v0.4.2 (etapa 0.4) – BlocoDMAQ completo
# ===========================================================================

from pyanatem.blocos import BlocoDMAQ


def test_dmaq_adicionar_maquina_simples():
    """DMAQ: associação básica sem AVR nem gov."""
    d = BlocoDMAQ()
    d.adicionar_maquina(barra=1432, grupo=10, und=1, mg=751)
    t = d.serializar()
    assert "DMAQ" in t
    assert "1432" in t
    assert "751" in t
    assert "999999" in t


def test_dmaq_adicionar_maquina_avr_cdu():
    """DMAQ: Mt com flag CDU (u) serializa corretamente."""
    d = BlocoDMAQ()
    d.adicionar_maquina(
        barra=3500, grupo=10, p=60, q=60, und=3, mg=753, mt=144, mt_cdu=True, mv=126
    )
    t = d.serializar()
    assert "144u" in t or "144U" in t or "144" in t
    assert "3500" in t


def test_dmaq_adicionar_maquina_com_pss():
    """DMAQ: Me (estabilizador) preenchido."""
    d = BlocoDMAQ()
    d.adicionar_maquina(
        barra=3500, grupo=20, p=40, q=40, und=2, mg=753, mt=81, mv=126, me=39
    )
    t = d.serializar()
    assert "39" in t


def test_dmaq_multiplas_maquinas_mesma_barra():
    """DMAQ: múltiplas linhas para a mesma barra."""
    d = BlocoDMAQ()
    d.adicionar_maquina(barra=3500, grupo=10, p=60, mg=753, mt=78)
    d.adicionar_maquina(barra=3500, grupo=20, p=40, mg=753, mt=81)
    t = d.serializar()
    assert t.count("3500") == 2


def test_dmaq_api_alto_nivel(tmp_path):
    """CasoAnatem.adicionar_maquina() atalho funciona."""
    from pyanatem import CasoAnatem

    caso = CasoAnatem()
    caso.darq.sav = "rede.sav"
    caso.adicionar_maquina(barra=100, grupo=1, mg=5)
    d = caso.deck()
    assert "DMAQ" in d
    assert "100" in d


def test_dmaq_roundtrip(tmp_path):
    """Roundtrip DMAQ: escrito e relido preserva dados."""
    from pyanatem import CasoAnatem

    caso = CasoAnatem()
    caso.darq.sav = "rede.sav"
    caso.darq.plt = "saida.plt"
    caso.dsim.tfim = 5.0
    caso.adicionar_maquina(barra=1432, grupo=10, und=1, mg=751)
    caso.adicionar_maquina(
        barra=3500, grupo=10, p=60, q=60, und=3, mg=753, mt=144, mt_cdu=True, mv=126
    )

    stb = tmp_path / "caso.stb"
    caso.exportar(stb)
    lido = CasoAnatem.ler(stb)
    assert lido.dmaq.tem_dados()
    barras = [a.barra for a in lido.dmaq.associacoes]
    assert 1432 in barras
    assert 3500 in barras


# ===========================================================================
# Etapa 0.5 – Serialização e parsing posicional do DMAQ  (metas v0.5.1–v0.5.3)
# ===========================================================================
#
# Testa todas as combinações relevantes de campos opcionais no DMAQ.
# Cada teste verifica roundtrip completo: objeto → serializar → reler → objeto.
#
# Casos cobertos (§46.41):
#   5a) Apenas Nb e Gr (todos opcionais omitidos)
#   5b) Nb, Gr e Mg (P, Q, Und omitidos) ← bug original: Mg era lido como P
#   5c) Nb, Gr, Mg e Mt sem CDU (P, Q, Und omitidos)
#   5d) Nb, Gr, Mg, Mt com flag CDU (P, Q, Und omitidos)
#   5e) Nb, Gr, P, Q, Und, Mg (Mt, Mv, Me omitidos)
#   5f) Todos os campos presentes (Nb, Gr, P, Q, Und, Mg, Mt, Mv, Me, Xvd, Nbc)
#   5g) Lista mista: múltiplas associações em combinações variadas
#   5h) Serialização posicional: campos ausentes emitem espaços na posição correta


def _roundtrip_dmaq(tmp_path, **kwargs):
    """Auxiliar: monta caso mínimo com uma associação, exporta, relê e retorna a associação."""
    from pyanatem import CasoAnatem

    caso = CasoAnatem()
    caso.darq.sav = "rede.sav"
    caso.darq.plt = "saida.plt"
    caso.dsim.tfim = 5.0
    caso.dmaq.adicionar_maquina(**kwargs)
    stb = tmp_path / "caso.stb"
    caso.exportar(stb)
    lido = CasoAnatem.ler(stb)
    assert len(lido.dmaq.associacoes) == 1
    return lido.dmaq.associacoes[0]


def test_dmaq_posicional_5a_apenas_nb_gr(tmp_path):
    """v0.5.3-5a: Apenas Nb e Gr; todos os campos opcionais omitidos."""
    a = _roundtrip_dmaq(tmp_path, barra=100, grupo=1)
    assert a.barra == 100
    assert a.grupo == 1
    assert a.p is None
    assert a.q is None
    assert a.und is None
    assert a.mg is None
    assert a.mt is None
    assert a.mv is None
    assert a.me is None
    assert a.xvd is None
    assert a.nbc is None


def test_dmaq_posicional_5b_mg_sem_pqu(tmp_path):
    """v0.5.3-5b: Nb, Gr e Mg presentes; P, Q, Und omitidos — caso do bug original."""
    a = _roundtrip_dmaq(tmp_path, barra=3500, grupo=10, mg=753)
    assert a.barra == 3500
    assert a.grupo == 10
    assert a.p is None, f"P deveria ser None, got {a.p}"
    assert a.q is None, f"Q deveria ser None, got {a.q}"
    assert a.und is None, f"Und deveria ser None, got {a.und}"
    assert a.mg == 753, f"Mg deveria ser 753, got {a.mg}"


def test_dmaq_posicional_5c_mg_mt_sem_pqu(tmp_path):
    """v0.5.3-5c: Nb, Gr, Mg e Mt (sem CDU); P, Q, Und omitidos."""
    a = _roundtrip_dmaq(tmp_path, barra=3500, grupo=10, mg=753, mt=78)
    assert a.mg == 753
    assert a.mt == 78
    assert a.mt_cdu is False
    assert a.p is None
    assert a.q is None
    assert a.und is None


def test_dmaq_posicional_5d_mg_mt_cdu_sem_pqu(tmp_path):
    """v0.5.3-5d: Nb, Gr, Mg, Mt com flag CDU; P, Q, Und omitidos."""
    a = _roundtrip_dmaq(tmp_path, barra=3500, grupo=10, mg=753, mt=144, mt_cdu=True)
    assert a.mg == 753
    assert a.mt == 144
    assert a.mt_cdu is True
    assert a.p is None
    assert a.q is None
    assert a.und is None


def test_dmaq_posicional_5e_pqu_mg_sem_controles(tmp_path):
    """v0.5.3-5e: Nb, Gr, P, Q, Und, Mg presentes; Mt, Mv, Me omitidos."""
    a = _roundtrip_dmaq(tmp_path, barra=1432, grupo=10, p=100, q=100, und=1, mg=751)
    assert a.barra == 1432
    assert a.p == 100
    assert a.q == 100
    assert a.und == 1
    assert a.mg == 751
    assert a.mt is None
    assert a.mv is None
    assert a.me is None


def test_dmaq_posicional_5f_todos_os_campos(tmp_path):
    """v0.5.3-5f: Todos os campos presentes."""
    a = _roundtrip_dmaq(
        tmp_path,
        barra=3500,
        grupo=10,
        p=60,
        q=60,
        und=3,
        mg=753,
        mt=78,
        mt_cdu=False,
        mv=126,
        mv_cdu=False,
        me=39,
        me_cdu=False,
        xvd=0.05,
        nbc=0,
    )
    assert a.barra == 3500
    assert a.grupo == 10
    assert a.p == 60
    assert a.q == 60
    assert a.und == 3
    assert a.mg == 753
    assert a.mt == 78
    assert a.mt_cdu is False
    assert a.mv == 126
    assert a.mv_cdu is False
    assert a.me == 39
    assert a.me_cdu is False
    assert abs(a.xvd - 0.05) < 1e-6
    assert a.nbc == 0


def test_dmaq_posicional_5f_todos_cdu(tmp_path):
    """v0.5.3-5f (variante CDU): Todos os modelos via CDU."""
    a = _roundtrip_dmaq(
        tmp_path,
        barra=3500,
        grupo=10,
        p=60,
        q=60,
        und=3,
        mg=753,
        mt=144,
        mt_cdu=True,
        mv=126,
        mv_cdu=True,
        me=39,
        me_cdu=True,
    )
    assert a.mt == 144 and a.mt_cdu is True
    assert a.mv == 126 and a.mv_cdu is True
    assert a.me == 39 and a.me_cdu is True


def test_dmaq_posicional_5g_lista_mista(tmp_path):
    """v0.5.3-5g: Lista mista com múltiplas associações em combinações variadas."""
    from pyanatem import CasoAnatem

    caso = CasoAnatem()
    caso.darq.sav = "rede.sav"
    caso.darq.plt = "saida.plt"
    caso.dsim.tfim = 5.0

    # Linha 1: só Nb, Gr
    caso.dmaq.adicionar_maquina(barra=100, grupo=1)
    # Linha 2: bug original — Mg sem P,Q,Und
    caso.dmaq.adicionar_maquina(barra=200, grupo=2, mg=50)
    # Linha 3: completa com CDU
    caso.dmaq.adicionar_maquina(
        barra=300,
        grupo=3,
        p=100,
        q=100,
        und=2,
        mg=51,
        mt=144,
        mt_cdu=True,
        mv=126,
        mv_cdu=False,
    )
    # Linha 4: P,Q,Und,Mg mas sem Mt
    caso.dmaq.adicionar_maquina(barra=400, grupo=4, p=50, q=50, und=1, mg=52)

    stb = tmp_path / "caso.stb"
    caso.exportar(stb)
    lido = CasoAnatem.ler(stb)
    assocs = lido.dmaq.associacoes
    assert len(assocs) == 4

    a1 = assocs[0]
    assert a1.barra == 100 and a1.grupo == 1
    assert a1.mg is None and a1.p is None

    a2 = assocs[1]
    assert a2.barra == 200 and a2.grupo == 2
    assert a2.mg == 50, f"Mg deveria ser 50, got {a2.mg} (bug de deslocamento)"
    assert a2.p is None, f"P deveria ser None, got {a2.p}"

    a3 = assocs[2]
    assert a3.barra == 300 and a3.p == 100 and a3.und == 2
    assert a3.mg == 51 and a3.mt == 144 and a3.mt_cdu is True
    assert a3.mv == 126 and a3.mv_cdu is False

    a4 = assocs[3]
    assert a4.barra == 400 and a4.p == 50 and a4.mg == 52
    assert a4.mt is None


def test_dmaq_posicional_5h_espacos_em_branco_na_posicao(tmp_path):
    """v0.5.3-5h: Serialização posicional emite espaços na posição correta.

    Verifica diretamente o STB gerado, não apenas o roundtrip, para garantir
    que campos ausentes não deslocam os campos seguintes.
    """
    from pyanatem import CasoAnatem
    from pyanatem.blocos import BlocoDMAQ

    caso = CasoAnatem()
    caso.darq.sav = "rede.sav"
    caso.darq.plt = "saida.plt"
    caso.dsim.tfim = 5.0
    # Associação com Mg mas sem P, Q, Und: o bug original deslocava Mg para coluna de P
    caso.dmaq.adicionar_maquina(barra=3500, grupo=10, mg=753, mt=144, mt_cdu=True)

    stb = tmp_path / "caso.stb"
    caso.exportar(stb)
    conteudo = stb.read_text()

    # Localiza a linha de dados do DMAQ (começa com espaços + "3500")
    linha_dados = None
    in_dmaq = False
    for linha in conteudo.splitlines():
        if linha.strip() == "DMAQ":
            in_dmaq = True
            continue
        if in_dmaq and "3500" in linha and not linha.strip().startswith("("):
            linha_dados = linha
            break

    assert linha_dados is not None, "Linha de dados do DMAQ não encontrada no STB"

    # Nb (cols 0-5) deve conter 3500; Gr (6-9) deve conter 10
    # P (10-13), Q (14-17), Und (18-21) devem ser brancos
    # Mg (22-27) deve conter 753
    nb_str = linha_dados[0:6].strip()
    gr_str = linha_dados[6:10].strip()
    p_str = linha_dados[10:14].strip()
    q_str = linha_dados[14:18].strip()
    und_str = linha_dados[18:22].strip()
    mg_str = linha_dados[22:28].strip()
    mt_str = linha_dados[28:34].strip()
    cdu_str = linha_dados[34:35] if len(linha_dados) > 34 else " "

    assert nb_str == "3500", f"Nb incorreto: {repr(nb_str)}"
    assert gr_str == "10", f"Gr incorreto: {repr(gr_str)}"
    assert p_str == "", f"P deveria estar em branco: {repr(p_str)}"
    assert q_str == "", f"Q deveria estar em branco: {repr(q_str)}"
    assert und_str == "", f"Und deveria estar em branco: {repr(und_str)}"
    assert mg_str == "753", f"Mg incorreto: {repr(mg_str)}"
    assert mt_str == "144", f"Mt incorreto: {repr(mt_str)}"
    assert cdu_str.lower() == "u", f"Flag CDU deveria ser 'u': {repr(cdu_str)}"


# ===========================================================================
# v0.4.3 (etapa 0.4) – FACTS e HVDC
# ===========================================================================

from pyanatem import BlocoSVC, BlocoTCSC, BlocoSTATCOM, BlocoHVDC


def test_svc_serializa():
    # DCER §46.18 — associação de CER/SVC (Listagem 46.16)
    b = BlocoSVC()
    b.adicionar(nb=500, gr=10, mc=800, me=94)
    t = b.serializar()
    assert "DCER" in t
    assert "500" in t and "800" in t
    assert "94U" in t  # estabilizador é sempre definido pelo usuário
    assert "999999" in t


def test_tcsc_serializa():
    # DCSC §46.22 — associação de CSC/TCSC (Listagem 46.20)
    b = BlocoTCSC()
    b.adicionar(de=500, pa=501, mc=800, nc=1, me=94)
    t = b.serializar()
    assert "DCSC" in t
    assert "500" in t and "501" in t and "800" in t
    assert "94U" in t


def test_statcom_serializa():
    # DVSI §46.64 — conversor FACTS VSI (Listagem 46.61)
    b = BlocoSTATCOM()
    b.adicionar(
        nv=21, de=2, np=8, cnvk=0.779696801, vb=138.0, xv=10.0, vst=30.0, st=80.0, ne=11
    )
    t = b.serializar()
    assert "DVSI" in t
    assert "21" in t
    assert "0.779696801" in t


def test_hvdc_serializa():
    # DCNV §46.21 — conversor CA-CC + associação (Listagem 46.19)
    b = BlocoHVDC()
    b.adicionar(no=25, mc=100, mc_usuario=True, gkb=5.0, amx=90.0)
    t = b.serializar()
    assert "DCNV" in t
    assert "25" in t
    assert "100U" in t


def test_facts_encadeamento():
    """Métodos adicionar retornam self para encadeamento."""
    b = BlocoSVC()
    result = b.adicionar(nb=100, gr=1, mc=800).adicionar(nb=200, gr=1, mc=801)
    assert result is b
    assert len(b._equipamentos) == 2


def test_facts_tem_dados():
    b = BlocoSVC()
    assert not b.tem_dados()
    b.adicionar(nb=100, gr=1, mc=800)
    assert b.tem_dados()


# ===========================================================================
# v0.4.4 / v0.4.5 (etapa 0.4) – BlocoDCDU e CDU
# ===========================================================================

from pyanatem import BlocoCDU, ParametroCDU, ValorInicialCDU, ControladorCDU, BlocoDCDU


def test_cdu_parametro_defpar():
    p = ParametroCDU(nome="#Vref", valor=1.0, comentario="Ref de tensão [pu]")
    t = p.serializar()
    assert "DEFPAR" in t
    assert "#Vref" in t
    assert "1" in t


def test_cdu_defval_simples():
    d = ValorInicialCDU(vdef="Vref", d1=1.0)
    t = d.serializar()
    assert "DEFVAL" in t
    assert "Vref" in t
    assert "1" in t


def test_cdu_bloco_ganho():
    b = BlocoCDU(nb=10, tipo="GANHO", vent="Vent", vsai="Vsai", p1=2.0)
    t = b.serializar()
    assert "GANHO" in t
    assert "Vent" in t
    assert "Vsai" in t
    assert "2" in t


def test_cdu_bloco_ledlag():
    b = BlocoCDU(
        nb=20,
        tipo="LEDLAG",
        vent="E",
        vsai="Y",
        p1=200.0,
        p2=0.0,
        p3=1.0,
        p4=0.05,
        vmin="Emin",
        vmax="Emax",
    )
    t = b.serializar()
    assert "LEDLAG" in t
    assert "200" in t
    assert "Emin" in t


def test_cdu_bloco_wshout():
    b = BlocoCDU(
        nb=30,
        tipo="WSHOUT",
        vent="W",
        vsai="Ypss",
        p1=5.0,
        p2=2.0,
        p3=2.0,
        vmin="Lmn",
        vmax="Lmx",
    )
    t = b.serializar()
    assert "WSHOUT" in t


def test_cdu_controlador_avr_simples():
    """Constrói AVR com WSHOUT + LEDLAG + limites."""
    ctrl = ControladorCDU(ncdu=100, nome="AVR_G1")
    ctrl.defpar("#Vref", 1.0, "Tensão de referência")
    ctrl.bloco(10, "IMPORT", stip="VOLT", vsai="Vt")
    b_soma = ctrl.bloco(20, "SOMA", vent="Vref", vsai="Erro")
    b_soma.adicionar_entrada("Vt", polaridade="-")
    ctrl.bloco(
        30,
        "LEDLAG",
        vent="Erro",
        vsai="Efd",
        p1=200.0,
        p2=0.0,
        p3=1.0,
        p4=0.05,
        vmin="Emin",
        vmax="Emax",
    )
    ctrl.bloco(40, "EXPORT", stip="EFD", vent="Efd")
    ctrl.defval("Vref", 1.0)
    ctrl.defval("Emin", -5.0)
    ctrl.defval("Emax", 5.0)

    t = ctrl.serializar()
    assert "100" in t
    assert "AVR_G1" in t
    assert "DEFPAR" in t
    assert "LEDLAG" in t
    assert "FIMCDU" in t
    assert "DEFVAL" in t


def test_cdu_bloco_dcdu_completo():
    """BlocoDCDU com dois controladores serializa corretamente."""
    dcdu = BlocoDCDU()

    avr = dcdu.novo_controlador(ncdu=100, nome="AVR")
    avr.defpar("#Ka", 200.0)
    avr.bloco(10, "GANHO", vent="Vent", vsai="Vsai", p1=200.0)
    avr.defval("Lim", 5.0)

    pss = dcdu.novo_controlador(ncdu=200, nome="PSS")
    pss.bloco(
        10,
        "WSHOUT",
        vent="W",
        vsai="Ypss",
        p1=5.0,
        p2=2.0,
        p3=2.0,
        vmin="Lmn",
        vmax="Lmx",
    )
    pss.defval("Lmn", -0.1)
    pss.defval("Lmx", 0.1)

    t = dcdu.serializar()
    assert "DCDU" in t
    assert "AVR" in t
    assert "PSS" in t
    assert t.count("FIMCDU") == 2
    assert "999999" in t


def test_cdu_tem_dados():
    d = BlocoDCDU()
    assert not d.tem_dados()
    d.novo_controlador(ncdu=1, nome="X")
    assert d.tem_dados()


def test_cdu_roundtrip_basico(tmp_path):
    """BlocoDCDU: serialização e re-parse preserva ncdu e número de blocos."""
    from pyanatem.cdu import parsear_dcdu

    dcdu = BlocoDCDU()
    ctrl = dcdu.novo_controlador(ncdu=42, nome="TESTE")
    ctrl.bloco(10, "GANHO", vent="Vent", vsai="Vsai", p1=1.5)
    ctrl.defval("Vent", 0.0)

    texto = dcdu.serializar()
    linhas = texto.splitlines()
    dcdu2, _ = parsear_dcdu(linhas, 0)

    assert len(dcdu2._controladores) == 1
    assert dcdu2._controladores[0].ncdu == 42
    assert dcdu2._controladores[0].nome == "TESTE"
    assert len(dcdu2._controladores[0]._blocos) == 1


def test_cdu_bloco_init_flag():
    b = BlocoCDU(nb=5, tipo="GANHO", vent="X", vsai="Y", p1=1.0, init_flag=True)
    t = b.serializar()
    assert "*" in t


def test_cdu_bloco_import_export():
    """Blocos de interface serializam com stip."""
    b_imp = BlocoCDU(nb=1, tipo="IMPORT", stip="VOLT", vsai="Vt")
    b_exp = BlocoCDU(nb=2, tipo="EXPORT", stip="EFD", vent="Efd")
    assert "IMPORT" in b_imp.serializar()
    assert "VOLT" in b_imp.serializar()
    assert "EXPORT" in b_exp.serializar()
    assert "EFD" in b_exp.serializar()


def test_cdu_defvdf():
    from pyanatem.cdu import ValorDefaultCDU

    d = ValorDefaultCDU(vdef="Lim", valor=1.0)
    t = d.serializar()
    assert "DEFVDF" in t
    assert "Lim" in t


# ===========================================================================
# v0.4.6 (etapa 0.4) – Análise de contingências automatizada
# ===========================================================================


def test_contingencias_de_contingencias():
    """de_contingencias() gera o número correto de casos."""
    from pyanatem import CasoAnatem, EnsaioAnatem

    base = CasoAnatem()
    base.darq.sav = "rede.sav"
    base.dsim.tfim = 10.0

    conts = [
        {"nome": "C1", "tipo": "curto_barra", "barra": 10, "t_apl": 1.0, "t_rem": 1.1},
        {"nome": "C2", "tipo": "curto_barra", "barra": 20, "t_apl": 1.0, "t_rem": 1.1},
        {"nome": "C3", "tipo": "abertura_linha", "de": 10, "para": 20, "t_aber": 0.5},
        {
            "nome": "C4",
            "tipo": "abertura_linha",
            "de": 10,
            "para": 30,
            "t_aber": 0.5,
            "t_fech": 1.0,
        },
        {
            "nome": "C5",
            "tipo": "step",
            "barra": 5,
            "unidade": 1,
            "t_ini": 2.0,
            "delta": 0.05,
        },
    ]
    ensaio = EnsaioAnatem.de_contingencias(base, conts)
    assert len(ensaio.casos()) == 5
    assert "C1" in ensaio.casos()
    assert "C5" in ensaio.casos()


def test_contingencias_nomes_arquivo(tmp_path):
    """Arquivos STB exportados têm os nomes corretos."""
    from pyanatem import CasoAnatem, EnsaioAnatem

    base = CasoAnatem()
    base.darq.sav = "rede.sav"
    base.dsim.tfim = 10.0

    conts = [
        {
            "nome": "CONT_A",
            "tipo": "curto_barra",
            "barra": 5,
            "t_apl": 1.0,
            "t_rem": 1.1,
        },
        {
            "nome": "CONT_B",
            "tipo": "curto_barra",
            "barra": 6,
            "t_apl": 1.0,
            "t_rem": 1.1,
        },
    ]
    ensaio = EnsaioAnatem.de_contingencias(base, conts)
    paths = ensaio.exportar_todos(diretorio=tmp_path)
    nomes = {p.stem for p in paths}
    assert "CONT_A" in nomes
    assert "CONT_B" in nomes


def test_contingencias_isoladas():
    """Cada caso é independente (modificar um não afeta outro)."""
    from pyanatem import CasoAnatem, EnsaioAnatem

    base = CasoAnatem()
    base.darq.sav = "rede.sav"
    base.dsim.tfim = 10.0

    conts = [
        {"nome": "A", "tipo": "curto_barra", "barra": 10, "t_apl": 1.0, "t_rem": 1.1},
        {"nome": "B", "tipo": "curto_barra", "barra": 20, "t_apl": 1.0, "t_rem": 1.1},
    ]
    ensaio = EnsaioAnatem.de_contingencias(base, conts)
    casos = ensaio.casos()
    # Barra 10 só no caso A
    ev_a = [ev.nb1 for ev in casos["A"].devt._eventos]
    ev_b = [ev.nb1 for ev in casos["B"].devt._eventos]
    assert 10 in ev_a and 10 not in ev_b
    assert 20 in ev_b and 20 not in ev_a


def test_relatorio_consolidado():
    """relatorio_consolidado() produz tabela legível."""
    from pyanatem import EnsaioAnatem

    ensaio = EnsaioAnatem.novo()
    resultados = [
        {
            "arquivo": "/tmp/C1.stb",
            "convergiu": True,
            "erros": [],
            "avisos": [],
            "passou": True,
        },
        {
            "arquivo": "/tmp/C2.stb",
            "convergiu": False,
            "erros": ["ERRO X"],
            "avisos": [],
            "passou": False,
        },
    ]
    rel = ensaio.relatorio_consolidado(resultados)
    assert "C1" in rel
    assert "C2" in rel
    assert "Sim" in rel
    assert "Não" in rel


# ===========================================================================
# v0.4.7 (etapa 0.4) – LeitorSAV e validação cruzada
# ===========================================================================

from pyanatem import LeitorSAV, ResultadoSAV


def test_leitor_sav_barras_minimo():
    """LeitorSAV lê barras de um .sav sintético mínimo."""
    sav_texto = """\
( caso sintético
DBAR
1 BARRA_A GD 1 1 138.0 0 0 100 0
2 BARRA_B GD 1 1 138.0 0 0  50 0
99999
"""
    r = LeitorSAV.ler_texto(sav_texto)
    assert 1 in r.barras
    assert 2 in r.barras
    assert r.barras[1].nome == "BARRA_A"


def test_leitor_sav_circuitos():
    """LeitorSAV lê circuitos de DLIN."""
    sav_texto = """\
DLIN
1   2   1  0  0  0.01  0.05  0.0
1   3   1  0  0  0.02  0.08  0.0
99999
"""
    r = LeitorSAV.ler_texto(sav_texto)
    assert len(r.circuitos) == 2
    chaves = r.chaves_circuitos()
    assert (1, 2, 1) in chaves
    assert (1, 3, 1) in chaves


def test_leitor_sav_barras_e_circuitos():
    """LeitorSAV parseia tanto DBAR quanto DLIN no mesmo arquivo."""
    sav_texto = """\
DBAR
10 BUS_A GD 1 1 230. 0 0 200 0
20 BUS_B GD 1 1 230. 0 0 100 0
99999
DLIN
10  20  1  0  0  0.01  0.05  0.0
99999
"""
    r = LeitorSAV.ler_texto(sav_texto)
    assert 10 in r.barras
    assert 20 in r.barras
    assert (10, 20, 1) in r.chaves_circuitos()


def test_validar_contra_sav_ok(tmp_path):
    """validar_contra_sav: caso consistente retorna lista vazia."""
    from pyanatem import CasoAnatem

    sav_path = tmp_path / "rede.sav"
    sav_path.write_text(
        "DBAR\n5 BUS5 GD 1 1 138. 0 0 100 0\n99999\n", encoding="latin-1"
    )

    caso = CasoAnatem()
    caso.darq.sav = str(sav_path)
    caso.dsim.tfim = 10.0
    caso.curto_barra(barra=5, t_apl=1.0, t_rem=1.1)

    erros = caso.validar_contra_sav(sav_path)
    assert erros == []


def test_validar_contra_sav_barra_inexistente(tmp_path):
    """validar_contra_sav: detecta barra inexistente em evento."""
    from pyanatem import CasoAnatem

    sav_path = tmp_path / "rede.sav"
    sav_path.write_text(
        "DBAR\n5 BUS5 GD 1 1 138. 0 0 100 0\n99999\n", encoding="latin-1"
    )

    caso = CasoAnatem()
    caso.darq.sav = str(sav_path)
    caso.dsim.tfim = 10.0
    caso.curto_barra(barra=999, t_apl=1.0, t_rem=1.1)  # barra 999 não existe

    erros = caso.validar_contra_sav(sav_path)
    assert any("999" in e for e in erros)


def test_validar_contra_sav_circuito_inexistente(tmp_path):
    """validar_contra_sav: detecta circuito inexistente em evento DEVT."""
    from pyanatem import CasoAnatem

    sav_path = tmp_path / "rede.sav"
    sav_path.write_text(
        "DBAR\n10 A GD 1 1 138. 0 0 0 0\n20 B GD 1 1 138. 0 0 0 0\n99999\n"
        "DLIN\n10 20 1  0 0 0.01 0.05 0.0\n99999\n",
        encoding="latin-1",
    )

    caso = CasoAnatem()
    caso.darq.sav = str(sav_path)
    caso.dsim.tfim = 10.0
    # circuito nc=99 não existe
    caso.devt.curto_circuito(de=10, para=20, circ=99, tini=1.0, tipo="APCC")

    erros = caso.validar_contra_sav(sav_path)
    assert any("99" in e for e in erros)


def test_leitor_sav_arquivo_real(tmp_path):
    """Parsing de .sav sintético salvo em disco funciona via LeitorSAV.ler()."""
    sav_path = tmp_path / "mini.sav"
    sav_path.write_text(
        "DBAR\n1 A GD 1 1 138. 0 0 100 0\n2 B GD 1 1 138. 0 0 50 0\n99999\n"
        "DLIN\n1 2 1 0 0 0.01 0.05 0.0\n99999\n",
        encoding="latin-1",
    )
    r = LeitorSAV.ler(sav_path)
    assert 1 in r.barras
    assert 2 in r.barras
    assert (1, 2, 1) in r.chaves_circuitos()


# ---- v1.1.3: robustez por colunas fixas + resolução de tensão-base (DGBT) ----


def test_leitor_sav_colunas_fixas_dbar_dgbt():
    """DBAR em colunas fixas: nome com espaço preservado + tensão via DGBT.

    O split por espaços do parser antigo quebrava nomes com espaço (pegava
    só "SAO"); o parser de colunas fixas preserva "SAO PAULO". A tensão-base
    vem do grupo Gb resolvido contra a tabela DGBT (não está no DBAR).
    """
    #     No=1  tipo=2  Gb=01  nome="SAO PAULO" (col 11+)
    sav = "DGBT\n01 138.\n99999\n" "DBAR\n" "    1  201SAO PAULO\n" "99999\n"
    r = LeitorSAV.ler_texto(sav)
    b = r.barras[1]
    assert b.nome == "SAO PAULO"  # nome com espaço preservado
    assert b.tipo == 2
    assert b.grupo_base == "01"
    assert b.tensao_base == 138.0  # resolvido via DGBT


def test_leitor_sav_dlin_colunas_fixas():
    """DLIN em colunas fixas: De[0:5] Para[10:15] Nc[15:17]."""
    sav = "DLIN\n" "   10        20 1\n" "99999\n"
    r = LeitorSAV.ler_texto(sav)
    assert (10, 20, 1) in r.chaves_circuitos()


def test_leitor_sav_ignora_blocos_extras():
    """Blocos ANAREDE não-alvo (DGER, DCAR, DARE) são ignorados sem erro."""
    sav = (
        "DBAR\n    1  201BARRA A\n99999\n"
        "DGER\n1 100. 50.\n99999\n"
        "DCAR\n1 10. 5.\n99999\n"
        "DARE\n1 SUDESTE\n99999\n"
    )
    r = LeitorSAV.ler_texto(sav)
    assert 1 in r.barras
    assert r.erros == []  # blocos extras não geram erros


# ===========================================================================
# v0.6.4 — Testes de integração FACTS, HVDC e CDU no CasoAnatem
# ===========================================================================


def test_caso_tem_atributos_facts_hvdc():
    """CasoAnatem expõe svc, tcsc, statcom, hvdc e dcdu após __init__."""
    from pyanatem import CasoAnatem
    from pyanatem.blocos import BlocoSVC, BlocoTCSC, BlocoSTATCOM, BlocoHVDC
    from pyanatem.cdu import BlocoDCDU

    caso = CasoAnatem()
    assert isinstance(caso.svc, BlocoSVC)
    assert isinstance(caso.tcsc, BlocoTCSC)
    assert isinstance(caso.statcom, BlocoSTATCOM)
    assert isinstance(caso.hvdc, BlocoHVDC)
    assert isinstance(caso.dcdu, BlocoDCDU)


def test_svc_populado_aparece_no_deck():
    """deck() emite bloco SVC (DCER) quando populado."""
    from pyanatem import CasoAnatem

    caso = CasoAnatem()
    caso.darq.sav = "rede.sav"
    caso.svc.adicionar(nb=100, gr=1, mc=800)
    stb = caso.deck()
    assert "DCER" in stb


def test_tcsc_populado_aparece_no_deck():
    """deck() emite bloco TCSC (DCSC) quando populado."""
    from pyanatem import CasoAnatem

    caso = CasoAnatem()
    caso.darq.sav = "rede.sav"
    caso.tcsc.adicionar(de=10, pa=20, mc=800, nc=1)
    stb = caso.deck()
    assert "DCSC" in stb


def test_statcom_populado_aparece_no_deck():
    """deck() emite bloco STATCOM (DVSI) quando populado."""
    from pyanatem import CasoAnatem

    caso = CasoAnatem()
    caso.darq.sav = "rede.sav"
    caso.statcom.adicionar(
        nv=1,
        de=200,
        np=1,
        cnvk=0.612372436,
        vb=138.0,
        xv=10.0,
        vst=13.8,
        st=80.0,
        ne=12,
    )
    stb = caso.deck()
    assert "DVSI" in stb


def test_hvdc_populado_aparece_no_deck():
    """deck() emite bloco HVDC (DCNV) quando populado."""
    from pyanatem import CasoAnatem

    caso = CasoAnatem()
    caso.darq.sav = "rede.sav"
    caso.hvdc.adicionar(no=25, mc=100, mc_usuario=True, gkb=5.0)
    stb = caso.deck()
    assert "DCNV" in stb


def test_facts_blocos_vazios_nao_aparecem_no_deck():
    """deck() omite cabeçalhos de blocos FACTS/HVDC quando vazios."""
    from pyanatem import CasoAnatem

    caso = CasoAnatem()
    caso.darq.sav = "rede.sav"
    stb = caso.deck()
    # Nenhum cabeçalho de bloco FACTS deve aparecer quando nenhum foi populado
    assert "CER" not in stb
    assert "TCSC" not in stb
    assert "STATCOM" not in stb
    assert "HVDC" not in stb


def test_facts_ordem_no_deck():
    """Blocos FACTS/HVDC aparecem entre DMAQ e DEVT no STB."""
    from pyanatem import CasoAnatem

    caso = CasoAnatem()
    caso.darq.sav = "rede.sav"
    caso.svc.adicionar(nb=100, gr=1, mc=800)
    caso.devt.curto_barra(barra=5, tini=1.0, tipo="APCB")
    stb = caso.deck()

    # Confirma que DCER aparece antes de DEVT
    idx_dcer = stb.find("DCER")
    idx_devt = stb.find("DEVT")
    assert idx_dcer != -1
    assert idx_devt != -1
    assert idx_dcer < idx_devt


# ===========================================================================
# v1.1.1 – FACTS (DCER/DCSC/DVSI) validados contra o manual §46 + roundtrip
# ===========================================================================


def test_dcer_exemplo_manual(tmp_path):
    """Valores da Listagem 46.16: DCER ``500 10 800 94U``."""
    from pyanatem import CasoAnatem

    stb = (
        "DARQ\nSIST rede.sav\n999999\n"
        "DCER\n( Nb) Gr ( Mc )u( Me )u\n500 10 800 94U\n999999\nFIM\n"
    )
    p = tmp_path / "dcer_manual.stb"
    p.write_text(stb, encoding="latin-1")
    caso = CasoAnatem.ler(p)
    e = caso.svc._equipamentos[0]
    assert (e.nb, e.gr, e.mc, e.me) == (500, 10, 800, 94)
    assert e.mc_usuario is False  # 800 sem 'U' → modelo predefinido (DMCE)
    assert e.me_usuario is True  # 94U → estabilizador do usuário


def test_dcsc_exemplo_manual(tmp_path):
    """Valores da Listagem 46.20: DCSC ``500 501 01 800 94U``."""
    from pyanatem import CasoAnatem

    stb = (
        "DARQ\nSIST rede.sav\n999999\n"
        "DCSC\n( De) ( Pa) Nc ( Mc )u ( Me )u\n500 501 01 800 94U\n999999\nFIM\n"
    )
    p = tmp_path / "dcsc_manual.stb"
    p.write_text(stb, encoding="latin-1")
    caso = CasoAnatem.ler(p)
    e = caso.tcsc._equipamentos[0]
    assert (e.de, e.pa, e.nc, e.mc, e.me) == (500, 501, 1, 800, 94)
    assert e.mc_usuario is False and e.me_usuario is True


def test_roundtrip_dcer(tmp_path):
    """DCER: serializa → exporta → lê, preservando campos e flags U."""
    from pyanatem import CasoAnatem

    caso = CasoAnatem()
    caso.darq.sav = "rede.sav"
    caso.svc.adicionar(nb=500, gr=10, mc=800, me=94)  # com estabilizador
    caso.svc.adicionar(
        nb=600, gr=1, mc=94, mc_usuario=True
    )  # modelo do usuário, sem estab.
    p = tmp_path / "dcer.stb"
    caso.exportar(p)

    lido = CasoAnatem.ler(p)
    assert len(lido.svc._equipamentos) == 2
    e0, e1 = lido.svc._equipamentos
    assert (e0.nb, e0.gr, e0.mc, e0.me) == (500, 10, 800, 94)
    assert e0.mc_usuario is False and e0.me_usuario is True
    assert (e1.nb, e1.gr, e1.mc, e1.me) == (600, 1, 94, None)
    assert e1.mc_usuario is True


def test_roundtrip_dcsc(tmp_path):
    """DCSC: circuito default vs. explícito; com e sem estabilizador."""
    from pyanatem import CasoAnatem

    caso = CasoAnatem()
    caso.darq.sav = "rede.sav"
    caso.tcsc.adicionar(de=500, pa=501, mc=800, nc=1, me=94)
    caso.tcsc.adicionar(de=10, pa=20, mc=801, nc=2)  # circuito 2, sem estab.
    p = tmp_path / "dcsc.stb"
    caso.exportar(p)

    lido = CasoAnatem.ler(p)
    assert len(lido.tcsc._equipamentos) == 2
    e0, e1 = lido.tcsc._equipamentos
    assert (e0.de, e0.pa, e0.nc, e0.mc, e0.me) == (500, 501, 1, 800, 94)
    assert (e1.de, e1.pa, e1.nc, e1.mc, e1.me) == (10, 20, 2, 801, None)


def test_roundtrip_dvsi_shunt(tmp_path):
    """DVSI shunt (STATCOM): Pa em branco; Rv/Vpt em branco (valores Lst. 46.61)."""
    from pyanatem import CasoAnatem

    caso = CasoAnatem()
    caso.darq.sav = "rede.sav"
    caso.statcom.adicionar(
        nv=21,
        de=2,
        nx=1,
        np=8,
        cnvk=0.779696801,
        vb=138.0,
        xv=10.0,
        vst=30.0,
        st=80.0,
        tap=1.0,
        ne=11,
    )
    p = tmp_path / "dvsi_shunt.stb"
    caso.exportar(p)

    lido = CasoAnatem.ler(p)
    c = lido.statcom._conversores[0]
    assert (c.nv, c.de, c.pa, c.nx, c.np, c.ne) == (21, 2, None, 1, 8, 11)
    assert c.cnvk == 0.779696801
    assert c.vb == 138.0 and c.vst == 30.0 and c.st == 80.0
    assert c.rv is None and c.vpt is None  # brancos preservados como None
    assert c.m == "P"


def test_roundtrip_dvsi_serie(tmp_path):
    """DVSI série (SSSC): Pa presente, Rv em branco (valores Lst. 46.61)."""
    from pyanatem import CasoAnatem

    caso = CasoAnatem()
    caso.darq.sav = "rede.sav"
    caso.statcom.adicionar(
        nv=22,
        de=3,
        pa=4,
        nx=1,
        np=1,
        cnvk=0.612372436,
        vb=138.0,
        xv=10.0,
        vpt=138.0,
        vst=13.8,
        st=80.0,
        tap=1.0,
        ne=12,
    )
    p = tmp_path / "dvsi_serie.stb"
    caso.exportar(p)

    lido = CasoAnatem.ler(p)
    c = lido.statcom._conversores[0]
    assert (c.nv, c.de, c.pa, c.np, c.ne) == (22, 3, 4, 1, 12)
    assert c.cnvk == 0.612372436
    assert c.vb == 138.0 and c.vpt == 138.0 and c.vst == 13.8
    assert c.rv is None  # Rv deixado em branco (recomendação do manual)


# ===========================================================================
# v1.1.2 – HVDC (DCNV/DELO) validados contra o manual §46 + roundtrip
# ===========================================================================


def test_dcnv_roundtrip(tmp_path):
    """DCNV: conversor 25 com Mc do usuário e ângulos (Listagem 46.19)."""
    from pyanatem import CasoAnatem

    caso = CasoAnatem()
    caso.darq.sav = "rede.sav"
    caso.hvdc.adicionar(no=25, mc=100, mc_usuario=True, gkb=5.0, amx=90.0)
    p = tmp_path / "dcnv.stb"
    caso.exportar(p)

    lido = CasoAnatem.ler(p)
    c = lido.hvdc._conversores[0]
    assert (c.no, c.mc, c.mc_usuario) == (25, 100, True)
    assert c.gkb == 5.0 and c.amx == 90.0
    assert c.amn is None and c.gmn is None  # brancos → None
    assert c.s1 is None and c.s2 is None


def test_dcnv_roundtrip_sinais(tmp_path):
    """DCNV: sinais de modulação S1 (usuário) + S2 (predefinido)."""
    from pyanatem import CasoAnatem

    caso = CasoAnatem()
    caso.darq.sav = "rede.sav"
    caso.hvdc.adicionar(
        no=1,
        mc=50,
        amn=5.0,
        amx=90.0,
        gmn=15.0,
        s1=200,
        s1_usuario=True,
        s2=201,
    )
    p = tmp_path / "dcnv_sinais.stb"
    caso.exportar(p)

    lido = CasoAnatem.ler(p)
    c = lido.hvdc._conversores[0]
    assert (c.no, c.mc) == (1, 50)
    assert (c.amn, c.amx, c.gmn) == (5.0, 90.0, 15.0)
    assert (c.s1, c.s1_usuario) == (200, True)
    assert (c.s2, c.s2_usuario) == (201, False)
    assert c.s3 is None and c.s4 is None


def test_delo_exemplo_manual(tmp_path):
    """Parse literal da Listagem 46.25 (DELO é formato livre)."""
    from pyanatem import CasoAnatem

    stb = (
        "DARQ\nSIST rede.sav\n999999\n"
        "DELO\n(Ne) ( M+ )u( M- )u\n"
        "0001 10 10\n0002 10 20\n0003 10 100u\n0004 110u\n999999\nFIM\n"
    )
    p = tmp_path / "delo_manual.stb"
    p.write_text(stb, encoding="latin-1")
    caso = CasoAnatem.ler(p)
    elos = caso.delo._elos
    assert len(elos) == 4
    assert (elos[0].ne, elos[0].mp, elos[0].mm) == (1, 10, 10)  # bipolar predefinido
    assert (elos[2].ne, elos[2].mp, elos[2].mm, elos[2].mm_usuario) == (
        3,
        10,
        100,
        True,
    )
    assert (elos[3].ne, elos[3].mp, elos[3].mp_usuario, elos[3].mm) == (
        4,
        110,
        True,
        None,
    )


def test_roundtrip_delo(tmp_path):
    """DELO: elo bipolar e elo monopolar (só polo +)."""
    from pyanatem import CasoAnatem

    caso = CasoAnatem()
    caso.darq.sav = "rede.sav"
    caso.delo.adicionar(ne=1, mp=10, mm=20)  # bipolar
    caso.delo.adicionar(ne=2, mp=110, mp_usuario=True)  # monopolar, usuário
    p = tmp_path / "delo.stb"
    caso.exportar(p)

    lido = CasoAnatem.ler(p)
    assert len(lido.delo._elos) == 2
    e0, e1 = lido.delo._elos
    assert (e0.ne, e0.mp, e0.mm) == (1, 10, 20)
    assert (e1.ne, e1.mp, e1.mp_usuario, e1.mm) == (2, 110, True, None)


def test_salvar_cdu_cria_arquivo(tmp_path):
    """salvar_cdu() grava o arquivo .cdu no caminho indicado."""
    from pyanatem import CasoAnatem

    caso = CasoAnatem()
    caso.darq.sav = "rede.sav"

    avr = caso.dcdu.novo_controlador(ncdu=100, nome="AVR_G1")
    avr.defpar("#Vref", 1.0, "Tensão de referência [pu]")
    avr.defval("Vref", 1.0)

    cdu_path = tmp_path / "controles.cdu"
    resultado = caso.salvar_cdu(cdu_path)

    assert resultado == cdu_path
    assert cdu_path.exists()
    conteudo = cdu_path.read_text(encoding="latin-1")
    assert "DCDU" in conteudo
    assert "AVR_G1" in conteudo


def test_salvar_cdu_dcdu_vazio(tmp_path):
    """salvar_cdu() grava arquivo mesmo com BlocoDCDU vazio."""
    from pyanatem import CasoAnatem

    caso = CasoAnatem()
    cdu_path = tmp_path / "vazio.cdu"
    caso.salvar_cdu(cdu_path)
    # Arquivo criado, conteúdo pode ser vazio string
    assert cdu_path.exists()


def test_salvar_cdu_cria_diretorio(tmp_path):
    """salvar_cdu() cria diretórios intermediários se necessário."""
    from pyanatem import CasoAnatem

    caso = CasoAnatem()
    cdu_path = tmp_path / "subdir" / "controles.cdu"
    caso.salvar_cdu(cdu_path)
    assert cdu_path.exists()


# ===========================================================================
# v0.7.1 — Validação cruzada DMAQ ↔ DMDG em validar()
# ===========================================================================


def test_validar_dmaq_mg_ausente_no_dmdg():
    """validar() detecta mg referenciando modelo inexistente no DMDG."""
    from pyanatem import CasoAnatem

    caso = CasoAnatem()
    caso.darq.sav = "rede.sav"
    caso.dsim.tfim = 10.0
    # Adiciona máquina com mg=999, mas DMDG está vazio
    caso.adicionar_maquina(barra=100, grupo=1, mg=999)

    erros = caso.validar()
    assert any("mg=999" in e for e in erros)
    assert any("DMDG" in e for e in erros)


def test_validar_dmaq_mg_presente_no_dmdg():
    """validar() não reporta erro quando mg está corretamente definido no DMDG."""
    from pyanatem import CasoAnatem

    caso = CasoAnatem()
    caso.darq.sav = "rede.sav"
    caso.dsim.tfim = 10.0
    caso.dmdg.adicionar_md01(no=10, ld=20.0, h=5.0, mva=100.0)
    caso.adicionar_maquina(barra=100, grupo=1, mg=10)

    erros = caso.validar()
    mg_erros = [e for e in erros if "mg=" in e]
    assert mg_erros == []


def test_validar_dmaq_mt_predefinido_ausente_no_dmdg():
    """validar() detecta mt predefinido (mt_cdu=False) ausente no DMDG."""
    from pyanatem import CasoAnatem

    caso = CasoAnatem()
    caso.darq.sav = "rede.sav"
    caso.dsim.tfim = 10.0
    caso.dmdg.adicionar_md01(no=10, ld=20.0, h=5.0, mva=100.0)
    # mt=50 não está no DMDG, e mt_cdu=False (modelo predefinido)
    caso.adicionar_maquina(barra=100, grupo=1, mg=10, mt=50, mt_cdu=False)

    erros = caso.validar()
    assert any("mt=50" in e for e in erros)


def test_validar_dmaq_mt_cdu_nao_valida_contra_dmdg():
    """validar() não verifica mt quando mt_cdu=True (modelo CDU, não DMDG)."""
    from pyanatem import CasoAnatem

    caso = CasoAnatem()
    caso.darq.sav = "rede.sav"
    caso.dsim.tfim = 10.0
    caso.dmdg.adicionar_md01(no=10, ld=20.0, h=5.0, mva=100.0)
    # mt_cdu=True: modelo é CDU, não precisa estar no DMDG
    caso.adicionar_maquina(barra=100, grupo=1, mg=10, mt=999, mt_cdu=True)

    erros = caso.validar()
    mt_erros = [e for e in erros if "mt=" in e]
    assert mt_erros == []


def test_validar_dmaq_mv_me_ausentes_no_dmdg():
    """validar() detecta mv e me predefinidos ausentes no DMDG."""
    from pyanatem import CasoAnatem

    caso = CasoAnatem()
    caso.darq.sav = "rede.sav"
    caso.dsim.tfim = 10.0
    caso.dmdg.adicionar_md01(no=10, ld=20.0, h=5.0, mva=100.0)
    caso.adicionar_maquina(
        barra=100,
        grupo=1,
        mg=10,
        mv=77,
        mv_cdu=False,  # mv=77 não no DMDG
        me=88,
        me_cdu=False,  # me=88 não no DMDG
    )

    erros = caso.validar()
    assert any("mv=77" in e for e in erros)
    assert any("me=88" in e for e in erros)


def test_validar_dmaq_sem_associacoes_nao_gera_erro():
    """validar() não gera erros de DMAQ↔DMDG quando DMAQ está vazio."""
    from pyanatem import CasoAnatem

    caso = CasoAnatem()
    caso.darq.sav = "rede.sav"
    caso.dsim.tfim = 10.0

    erros = caso.validar()
    dmaq_dmdg_erros = [e for e in erros if "DMAQ" in e and "DMDG" in e]
    assert dmaq_dmdg_erros == []


def test_validar_dmaq_multiplas_maquinas_erros_individuais():
    """validar() reporta erro individualmente para cada associação inválida."""
    from pyanatem import CasoAnatem

    caso = CasoAnatem()
    caso.darq.sav = "rede.sav"
    caso.dsim.tfim = 10.0
    # DMDG vazio, duas máquinas com mg inválido
    caso.adicionar_maquina(barra=100, grupo=1, mg=10)
    caso.adicionar_maquina(barra=200, grupo=1, mg=20)

    erros = caso.validar()
    mg_erros = [e for e in erros if "mg=" in e]
    assert len(mg_erros) == 2


# ===========================================================================
# v0.7.2 / v0.7.3 — Caminho correto do relatório em executar_contingencias
# ===========================================================================


def test_executar_contingencias_usa_darq_rela(tmp_path):
    """executar_contingencias usa caso.darq.rela quando definido."""
    import subprocess
    from unittest.mock import patch, MagicMock
    from pyanatem import CasoAnatem
    from pyanatem.ensaio import EnsaioAnatem

    # Prepara caso com darq.rela definido
    template = CasoAnatem()
    template.darq.sav = "rede.sav"
    template.darq.rela = "resultado_especial.rela"
    template.dsim.tfim = 5.0

    ensaio = EnsaioAnatem(template=template, anatem_exe="/fake/anatem")

    stb_path = tmp_path / "caso.stb"
    stb_path.write_text("dummy", encoding="latin-1")

    # Cria o arquivo de relatório no caminho esperado (mesmo dir, nome do darq.rela)
    rela_esperado = tmp_path / "resultado_especial.rela"
    rela_esperado.write_text(
        "ANATEM - Relatorio\nEXECUCAO CONCLUIDA COM SUCESSO.\n", encoding="latin-1"
    )

    proc_mock = MagicMock(spec=subprocess.CompletedProcess)
    proc_mock.returncode = 0

    with patch.object(ensaio, "executar", return_value=proc_mock):
        resultados = ensaio.executar_contingencias([stb_path])

    assert len(resultados) == 1
    # Verificamos que o caminho do relatório foi encontrado (convergiu não é None)
    assert resultados[0]["convergiu"] is not None


def test_executar_contingencias_fallback_sem_darq_rela(tmp_path):
    """executar_contingencias faz fallback para .rela quando darq.rela não definido."""
    import subprocess
    from unittest.mock import patch, MagicMock
    from pyanatem import CasoAnatem
    from pyanatem.ensaio import EnsaioAnatem

    template = CasoAnatem()
    template.darq.sav = "rede.sav"
    # darq.rela NÃO definido
    template.dsim.tfim = 5.0

    ensaio = EnsaioAnatem(template=template, anatem_exe="/fake/anatem")

    stb_path = tmp_path / "caso.stb"
    stb_path.write_text("dummy", encoding="latin-1")

    # Cria o arquivo de relatório como fallback: mesmo nome do .stb, extensão .rela
    rela_fallback = tmp_path / "caso.rela"
    rela_fallback.write_text(
        "ANATEM - Relatorio\nEXECUCAO CONCLUIDA COM SUCESSO.\n", encoding="latin-1"
    )

    proc_mock = MagicMock(spec=subprocess.CompletedProcess)
    proc_mock.returncode = 0

    with patch.object(ensaio, "executar", return_value=proc_mock):
        resultados = ensaio.executar_contingencias([stb_path])

    assert len(resultados) == 1
    assert resultados[0]["convergiu"] is not None


def test_executar_contingencias_sem_rela_usa_returncode(tmp_path):
    """executar_contingencias usa returncode quando nenhum .rela existe."""
    import subprocess
    from unittest.mock import patch, MagicMock
    from pyanatem import CasoAnatem
    from pyanatem.ensaio import EnsaioAnatem

    template = CasoAnatem()
    template.darq.sav = "rede.sav"
    template.dsim.tfim = 5.0

    ensaio = EnsaioAnatem(template=template, anatem_exe="/fake/anatem")

    stb_path = tmp_path / "caso.stb"
    stb_path.write_text("dummy", encoding="latin-1")
    # Nenhum .rela criado

    proc_mock = MagicMock(spec=subprocess.CompletedProcess)
    proc_mock.returncode = 0

    with patch.object(ensaio, "executar", return_value=proc_mock):
        resultados = ensaio.executar_contingencias([stb_path])

    assert len(resultados) == 1
    # Sem .rela, convergiu deriva do returncode (0 = True)
    assert resultados[0]["convergiu"] is True


# ===========================================================================
# Etapa 0.8 – Cobertura de testes CDU (casos reais / avançados)
#
# Escopo da etapa: exclusivamente testes do módulo CDU. Nenhuma alteração em
# código de produção. Todos os controladores usados nos testes de roundtrip
# têm blocos com vent E vsai populados e nomes de variável que não colidem
# com as palavras-chave de stip reconhecidas pelo parser (VOLT/EFD/VTR/WMAQ/
# PMEC/PGER), condição necessária para equivalência estrutural completa após
# serializar -> parsear_dcdu (o parser é baseado em split()).
# ===========================================================================

from pyanatem.cdu import parsear_dcdu, ValorDefaultCDU


def _roundtrip_dcdu(dcdu):
    """Serializa um BlocoDCDU e o relê via parsear_dcdu(); devolve o relido."""
    linhas = dcdu.serializar().splitlines()
    dcdu2, _ = parsear_dcdu(linhas, 0)
    return dcdu2


# ---------------------------------------------------------------------------
# v0.8.1 – Operadores com múltiplas entradas (3 ou mais)
# ---------------------------------------------------------------------------


def test_cdu_soma_tres_entradas_roundtrip():
    """SOMA com 3 entradas (vent + 2 extras): serialização, parsing e roundtrip."""
    dcdu = BlocoDCDU()
    ctrl = dcdu.novo_controlador(ncdu=1, nome="SOMA3")
    b = ctrl.bloco(10, "SOMA", vent="A", vsai="S")
    b.adicionar_entrada("B")
    b.adicionar_entrada("C", polaridade="-")

    texto = dcdu.serializar()
    assert "SOMA" in texto
    assert "A" in texto and "B" in texto and "C" in texto

    b2 = _roundtrip_dcdu(dcdu)._controladores[0]._blocos[0]
    assert b2.tipo == "SOMA"
    assert b2.vent == "A"
    assert len(b2.linhas_extras) == 2  # 2 entradas extras preservadas
    assert "-C" in b2.linhas_extras[1]  # polaridade preservada
    assert b == b2  # equivalência estrutural completa


def test_cdu_soma_quatro_entradas_roundtrip():
    """SOMA com 4 entradas — acima do mínimo de 3."""
    dcdu = BlocoDCDU()
    ctrl = dcdu.novo_controlador(ncdu=1, nome="SOMA4")
    b = ctrl.bloco(10, "SOMA", vent="A", vsai="S")
    for v in ("B", "C", "D"):
        b.adicionar_entrada(v)

    b2 = _roundtrip_dcdu(dcdu)._controladores[0]._blocos[0]
    assert len(b2.linhas_extras) == 3
    assert b == b2


def test_cdu_curva_tempo_inverso_roundtrip():
    """Bloco CURVA (§29.3.13) com todos os subtipos de tempo inverso.

    Regressão v1.1.4: antes o tipo era "RELINV" (inexistente no manual) e o
    parser só reconhecia stip IEC/IEEE — IEC2/IEEE2 eram tratados como vent,
    deslocando todos os campos. Agora o tipo é CURVA e os 4 subtipos
    (Listagens 29.97–29.100) fazem roundtrip completo.
    """
    for stip in ("IEC", "IEC2", "IEEE", "IEEE2"):
        dcdu = BlocoDCDU()
        ctrl = dcdu.novo_controlador(ncdu=1, nome=f"CURVA_{stip}")
        ctrl.bloco(
            10,
            "CURVA",
            stip=stip,
            vent="Uin",
            vsai="Ysai",
            p1="#Uref",
            p2="#Tipo",
            p3="#Dial",
        )
        texto = dcdu.serializar()
        assert "CURVA" in texto and stip in texto

        b2 = _roundtrip_dcdu(dcdu)._controladores[0]._blocos[0]
        assert b2.tipo == "CURVA", stip
        assert b2.stip == stip, stip  # subtipo preservado (IEC2/IEEE2 inclusive)
        assert b2.vent == "Uin", stip  # vent não confundido com stip
        assert b2.vsai == "Ysai", stip
        assert (b2.p1, b2.p2, b2.p3) == ("#Uref", "#Tipo", "#Dial"), stip


def test_cdu_relinv_alias_legado():
    """RELINV segue reconhecido como alias legado do tipo CURVA."""
    dcdu = BlocoDCDU()
    ctrl = dcdu.novo_controlador(ncdu=1, nome="LEGADO")
    ctrl.bloco(
        10,
        "RELINV",
        stip="IEC",
        vent="Uin",
        vsai="Ysai",
        p1="#Uref",
        p2="#Tipo",
        p3="#Dial",
    )
    b2 = _roundtrip_dcdu(dcdu)._controladores[0]._blocos[0]
    assert b2.tipo == "RELINV"
    assert b2.stip == "IEC"
    assert b2.vent == "Uin" and b2.vsai == "Ysai"


def test_cdu_multpl_tres_entradas_roundtrip():
    """MULTPL com 3 entradas: serialização, parsing e roundtrip."""
    dcdu = BlocoDCDU()
    ctrl = dcdu.novo_controlador(ncdu=2, nome="MULT3")
    b = ctrl.bloco(10, "MULTPL", vent="A", vsai="P")
    b.adicionar_entrada("B")
    b.adicionar_entrada("C")

    assert "MULTPL" in dcdu.serializar()
    b2 = _roundtrip_dcdu(dcdu)._controladores[0]._blocos[0]
    assert b2.tipo == "MULTPL"
    assert len(b2.linhas_extras) == 2
    assert b == b2


def test_cdu_divsao_tres_entradas_roundtrip():
    """DIVSAO com 3 entradas: serialização, parsing e roundtrip."""
    dcdu = BlocoDCDU()
    ctrl = dcdu.novo_controlador(ncdu=3, nome="DIV3")
    b = ctrl.bloco(10, "DIVSAO", vent="Num", vsai="Q")
    b.adicionar_entrada("Den1")
    b.adicionar_entrada("Den2")

    assert "DIVSAO" in dcdu.serializar()
    b2 = _roundtrip_dcdu(dcdu)._controladores[0]._blocos[0]
    assert b2.tipo == "DIVSAO"
    assert len(b2.linhas_extras) == 2
    assert b == b2


# ---------------------------------------------------------------------------
# v0.8.2 – INTRES com as três entradas simultâneas (Sinal, RESET, VINIC)
# ---------------------------------------------------------------------------


def test_cdu_intres_tres_entradas_roundtrip():
    """INTRES com Sinal, RESET e VINIC presentes ao mesmo tempo."""
    dcdu = BlocoDCDU()
    ctrl = dcdu.novo_controlador(ncdu=1, nome="INTRES3")
    b = ctrl.bloco(20, "INTRES", vent="Sinal", vsai="Yint", p1=1.0)
    b.adicionar_entrada("RESET")
    b.adicionar_entrada("VINIC")

    texto = dcdu.serializar()
    assert "INTRES" in texto
    assert "Sinal" in texto and "RESET" in texto and "VINIC" in texto

    b2 = _roundtrip_dcdu(dcdu)._controladores[0]._blocos[0]
    assert b2.tipo == "INTRES"
    assert b2.vent == "Sinal"
    assert len(b2.linhas_extras) == 2  # RESET + VINIC
    assert "RESET" in b2.linhas_extras[0]
    assert "VINIC" in b2.linhas_extras[1]
    assert b == b2


# ---------------------------------------------------------------------------
# v0.8.3 – Roundtrip de controlador completo via parsear_dcdu()
# ---------------------------------------------------------------------------


def test_cdu_controlador_completo_roundtrip():
    """Controlador AVR completo com vários blocos interconectados sobrevive a
    serializar -> parsear_dcdu() com equivalência estrutural completa."""
    dcdu = BlocoDCDU()
    ctrl = dcdu.novo_controlador(ncdu=100, nome="AVR_COMPLETO")
    ctrl.defpar("#Ka", 200.0)
    ctrl.defpar("#Ta", 0.05)
    soma = ctrl.bloco(10, "SOMA", vent="Vref", vsai="Err")
    soma.adicionar_entrada("Vt", polaridade="-")
    ctrl.bloco(
        20,
        "LEDLAG",
        vent="Err",
        vsai="Vla",
        p1=200.0,
        p2=0.0,
        p3=1.0,
        p4=0.05,
        vmin="Emin",
        vmax="Emax",
    )
    ctrl.bloco(30, "GANHO", vent="Vla", vsai="Vfd", p1=1.0)
    mult = ctrl.bloco(40, "MULTPL", vent="Vfd", vsai="Vfdc")
    mult.adicionar_entrada("Kfd")
    ctrl.defval("Emin", -5.0)
    ctrl.defval("Emax", 5.0)

    dcdu2 = _roundtrip_dcdu(dcdu)
    assert len(dcdu2._controladores) == 1
    ctrl2 = dcdu2._controladores[0]

    # identificação e contagens
    assert ctrl2.ncdu == 100
    assert ctrl2.nome == "AVR_COMPLETO"
    assert len(ctrl2._blocos) == 4
    assert len(ctrl2._parametros) == 2
    assert len(ctrl2._defvals) == 2

    # cadeia de interconexão preservada
    b = ctrl2._blocos
    assert b[0].vsai == b[1].vent  # SOMA  -> LEDLAG
    assert b[1].vsai == b[2].vent  # LEDLAG -> GANHO
    assert b[2].vsai == b[3].vent  # GANHO  -> MULTPL

    # parâmetros do LEDLAG e limites preservados
    assert b[1].p1 == 200.0 and b[1].p4 == 0.05
    assert b[1].vmin == "Emin" and b[1].vmax == "Emax"

    # equivalência estrutural completa
    assert ctrl == ctrl2


# ---------------------------------------------------------------------------
# v0.8.4 – init_flag, DEFVDF e variáveis cruzadas
# ---------------------------------------------------------------------------


def test_cdu_init_flag_sobrevive_roundtrip():
    """Bloco com init_flag=True mantém a flag após serializar -> parsear_dcdu."""
    dcdu = BlocoDCDU()
    ctrl = dcdu.novo_controlador(ncdu=1, nome="INITFLAG")
    ctrl.bloco(10, "GANHO", vent="A", vsai="B", p1=2.0, init_flag=True)
    ctrl.bloco(20, "GANHO", vent="B", vsai="C", p1=1.0, init_flag=False)

    ctrl2 = _roundtrip_dcdu(dcdu)._controladores[0]
    assert ctrl2._blocos[0].init_flag is True  # flag preservada
    assert ctrl2._blocos[1].init_flag is False  # ausência de flag preservada
    assert ctrl == ctrl2


def test_cdu_defvdf_variavel_de_estado_roundtrip():
    """DEFVDF definindo o valor default da variável de estado (saída de um
    bloco dinâmico ORD1) sobrevive ao roundtrip."""
    dcdu = BlocoDCDU()
    ctrl = dcdu.novo_controlador(ncdu=2, nome="ESTADO")
    ctrl.bloco(10, "ORD1", vent="In", vsai="Xs", p1=1.0, p2=0.5)
    ctrl.defvdf("Xs", 0.0)  # default da variável de estado Xs

    texto = dcdu.serializar()
    assert "DEFVDF" in texto and "Xs" in texto

    ctrl2 = _roundtrip_dcdu(dcdu)._controladores[0]
    assert len(ctrl2._defvdfs) == 1
    assert ctrl2._defvdfs[0].vdef == "Xs"
    assert ctrl2._defvdfs[0].valor == 0.0
    # a variável do DEFVDF é a saída do bloco dinâmico (variável de estado)
    assert ctrl2._blocos[0].vsai == ctrl2._defvdfs[0].vdef
    assert ctrl == ctrl2


def test_cdu_variaveis_cruzadas_roundtrip():
    """Dois sub-blocos que referenciam variáveis um do outro (realimentação):
    a saída de cada bloco é a entrada do outro."""
    dcdu = BlocoDCDU()
    ctrl = dcdu.novo_controlador(ncdu=3, nome="CRUZADO")
    ctrl.bloco(10, "GANHO", vent="Vfb", vsai="Ymid", p1=2.0)
    ctrl.bloco(20, "LEDLAG", vent="Ymid", vsai="Vfb", p1=1.0, p2=0.0, p3=1.0, p4=0.1)

    ctrl2 = _roundtrip_dcdu(dcdu)._controladores[0]
    b = ctrl2._blocos
    assert b[0].vsai == b[1].vent  # bloco 10 alimenta bloco 20
    assert b[1].vsai == b[0].vent  # bloco 20 realimenta bloco 10
    assert ctrl == ctrl2


# ===========================================================================
# Etapa 0.11 — Validação de nomes de variáveis/parâmetros CDU (v0.11.3)
#
# Nomes de variáveis começam com letra; nomes de parâmetros com '#' + letra.
# A validação vale apenas na API de construção; o parser continua leniente.
# ===========================================================================

import pytest


def test_cdu_nome_variavel_invalido_em_bloco_levanta():
    ctrl = ControladorCDU(ncdu=1, nome="V")
    with pytest.raises(ValueError):
        ctrl.bloco(10, "GANHO", vent="1A", vsai="B", p1=1.0)  # vent começa com dígito
    with pytest.raises(ValueError):
        ctrl.bloco(10, "GANHO", vent="A", vsai="_B", p1=1.0)  # vsai começa com '_'


def test_cdu_nome_variavel_invalido_em_limites_levanta():
    ctrl = ControladorCDU(ncdu=1, nome="V")
    with pytest.raises(ValueError):
        ctrl.bloco(
            10,
            "LEDLAG",
            vent="A",
            vsai="B",
            p1=1.0,
            p2=0.0,
            p3=1.0,
            p4=0.1,
            vmin="9min",
            vmax="Lmx",
        )


def test_cdu_nome_variavel_invalido_em_entrada_levanta():
    ctrl = ControladorCDU(ncdu=1, nome="V")
    b = ctrl.bloco(10, "SOMA", vent="A", vsai="S")
    with pytest.raises(ValueError):
        b.adicionar_entrada("2B")  # entrada começa com dígito


def test_cdu_nome_variavel_invalido_em_defval_defvdf_levanta():
    ctrl = ControladorCDU(ncdu=1, nome="V")
    with pytest.raises(ValueError):
        ctrl.defval("0x", 1.0)
    with pytest.raises(ValueError):
        ctrl.defvdf("#x", 0.0)  # variável não pode começar com '#'


def test_cdu_nome_parametro_invalido_levanta():
    ctrl = ControladorCDU(ncdu=1, nome="V")
    with pytest.raises(ValueError):
        ctrl.defpar("Ka", 200.0)  # falta o '#'
    with pytest.raises(ValueError):
        ctrl.defpar("#1", 200.0)  # '#' seguido de dígito
    with pytest.raises(ValueError):
        ctrl.defpar("", 200.0)  # vazio


def test_cdu_nomes_validos_nao_levantam():
    ctrl = ControladorCDU(ncdu=1, nome="V")
    ctrl.defpar("#Ka", 200.0)
    b = ctrl.bloco(
        10,
        "LEDLAG",
        vent="Vref",
        vsai="Err",
        p1=1.0,
        p2=0.0,
        p3=1.0,
        p4=0.1,
        vmin="Emin",
        vmax="Emax",
    )
    b.adicionar_entrada("Vt", polaridade="-")
    ctrl.defval("Emin", -5.0)
    ctrl.defvdf("Xs", 0.0)
    # nomes vazios (campos opcionais não informados) são permitidos
    ctrl.bloco(20, "GANHO", vent="Err", vsai="", p1=1.0)


def test_cdu_parser_permanece_leniente():
    """O parser não deve aplicar a validação de nomes (arquivos existentes)."""
    from pyanatem.cdu import BlocoDCDU, parsear_dcdu

    ctrl = ControladorCDU(ncdu=1, nome="V")
    ctrl.bloco(10, "GANHO", vent="A", vsai="B", p1=1.0)
    dcdu = BlocoDCDU()
    dcdu.adicionar(ctrl)
    # parsear de volta não levanta, mesmo que o texto tivesse nomes atípicos
    dcdu2, _ = parsear_dcdu(dcdu.serializar().splitlines(), 0)
    assert len(dcdu2._controladores) == 1


# ---------------------------------------------------------------------------
# v0.12.1 – Parsing posicional para IMPORT/EXPORT (vent/vsai vazio)
# ---------------------------------------------------------------------------


def test_cdu_import_vent_vazio_roundtrip():
    """IMPORT com vent=vazio, vsai preenchido faz roundtrip (v0.12.1)."""
    dcdu = BlocoDCDU()
    ctrl = dcdu.novo_controlador(ncdu=1, nome="IMPORT_TEST")
    # IMPORT tem stip (tipo de sinal) e vsai (saída), mas vent é vazio
    ctrl.bloco(10, "IMPORT", stip="VOLT", vsai="Vt")

    ctrl2 = _roundtrip_dcdu(dcdu)._controladores[0]
    b = ctrl2._blocos[0]
    assert b.tipo == "IMPORT"
    assert b.stip == "VOLT"
    assert b.vent == ""  # v0.12.1: vent preservado como vazio
    assert b.vsai == "Vt"  # vsai correto
    assert ctrl == ctrl2  # equivalência estrutural


def test_cdu_export_vsai_vazio_roundtrip():
    """EXPORT com vsai=vazio, vent preenchido faz roundtrip (v0.12.1)."""
    dcdu = BlocoDCDU()
    ctrl = dcdu.novo_controlador(ncdu=1, nome="EXPORT_TEST")
    # EXPORT tem stip (tipo de sinal) e vent (entrada), mas vsai é vazio
    ctrl.bloco(20, "EXPORT", stip="EFD", vent="Efd")

    ctrl2 = _roundtrip_dcdu(dcdu)._controladores[0]
    b = ctrl2._blocos[0]
    assert b.tipo == "EXPORT"
    assert b.stip == "EFD"
    assert b.vent == "Efd"  # vent correto
    assert b.vsai == ""  # v0.12.1: vsai preservado como vazio
    assert ctrl == ctrl2  # equivalência estrutural


def test_cdu_import_export_combinados_roundtrip():
    """IMPORT e EXPORT no mesmo controlador, preservando vent/vsai vazios."""
    dcdu = BlocoDCDU()
    ctrl = dcdu.novo_controlador(ncdu=1, nome="IMPORT_EXPORT")
    ctrl.bloco(10, "IMPORT", stip="VOLT", vsai="Vt")  # vent vazio
    ctrl.bloco(20, "EXPORT", stip="EFD", vent="Efd")  # vsai vazio
    ctrl.bloco(30, "GANHO", vent="Vt", vsai="Vref_calc", p1=1.0)

    ctrl2 = _roundtrip_dcdu(dcdu)._controladores[0]
    assert ctrl2._blocos[0].vent == "" and ctrl2._blocos[0].vsai == "Vt"
    assert ctrl2._blocos[1].vent == "Efd" and ctrl2._blocos[1].vsai == ""
    assert ctrl2._blocos[2].vent == "Vt" and ctrl2._blocos[2].vsai == "Vref_calc"
    assert ctrl == ctrl2


# ---------------------------------------------------------------------------
# v0.12.2 – Desambiguação parâmetros vs. limites
# ---------------------------------------------------------------------------


def test_cdu_wshout_3params_com_limites_roundtrip():
    """WSHOUT com 3 parâmetros + vmin/vmax faz roundtrip (v0.12.2)."""
    dcdu = BlocoDCDU()
    ctrl = dcdu.novo_controlador(ncdu=1, nome="WSHOUT_TEST")
    # WSHOUT: 3 parâmetros (p1, p2, p3), depois vmin/vmax (nomes de variáveis)
    ctrl.bloco(
        10,
        "WSHOUT",
        vent="X",
        vsai="Y",
        p1=1.0,
        p2=2.0,
        p3=3.0,
        vmin="Xmin",
        vmax="Xmax",
    )

    ctrl2 = _roundtrip_dcdu(dcdu)._controladores[0]
    b = ctrl2._blocos[0]
    assert b.tipo == "WSHOUT"
    assert b.p1 == 1.0 and b.p2 == 2.0 and b.p3 == 3.0
    assert b.p4 is None or b.p4 == 0  # p4 não é usado em WSHOUT
    assert b.vmin == "Xmin" and b.vmax == "Xmax"
    assert ctrl == ctrl2


def test_cdu_intres_com_limites_roundtrip():
    """INTRES com vmin/vmax faz roundtrip (v0.12.2)."""
    dcdu = BlocoDCDU()
    ctrl = dcdu.novo_controlador(ncdu=1, nome="INTRES_TEST")
    # INTRES: 4 parâmetros por default (como blocos normais)
    # Com vmin/vmax como limites
    ctrl.bloco(
        20,
        "INTRES",
        vent="A",
        vsai="B",
        p1=1.0,
        p2=2.0,
        p3=3.0,
        p4=4.0,
        vmin="Amin",
        vmax="Amax",
    )

    ctrl2 = _roundtrip_dcdu(dcdu)._controladores[0]
    b = ctrl2._blocos[0]
    assert b.tipo == "INTRES"
    assert b.p1 == 1.0 and b.p2 == 2.0 and b.p3 == 3.0 and b.p4 == 4.0
    assert b.vmin == "Amin" and b.vmax == "Amax"
    assert ctrl == ctrl2


def test_cdu_bloco_normal_4params_sem_mudanca_roundtrip():
    """Bloco normal com 4 parâmetros continua funcionando (v0.12.2 sem regressão)."""
    dcdu = BlocoDCDU()
    ctrl = dcdu.novo_controlador(ncdu=1, nome="NORMAL_TEST")
    # LEDLAG: 4 parâmetros fixos
    ctrl.bloco(
        30,
        "LEDLAG",
        vent="In",
        vsai="Out",
        p1=1.0,
        p2=2.0,
        p3=3.0,
        p4=4.0,
        vmin="Emin",
        vmax="Emax",
    )

    ctrl2 = _roundtrip_dcdu(dcdu)._controladores[0]
    b = ctrl2._blocos[0]
    assert b.tipo == "LEDLAG"
    assert b.p1 == 1.0 and b.p2 == 2.0 and b.p3 == 3.0 and b.p4 == 4.0
    assert b.vmin == "Emin" and b.vmax == "Emax"
    assert ctrl == ctrl2


# ---------------------------------------------------------------------------
# v0.12.3 – Colisão nome variável com stip
# ---------------------------------------------------------------------------


def test_cdu_variavel_volt_nao_confundida_com_stip_roundtrip():
    """Variável chamada 'Volt' não é confundida com stip=VOLT (v0.12.3)."""
    dcdu = BlocoDCDU()
    ctrl = dcdu.novo_controlador(ncdu=1, nome="VOLT_VAR")
    # Bloco LEDLAG com vent="Volt" (variável, não stip)
    # stip não deveria ser detectado aqui
    ctrl.bloco(10, "LEDLAG", vent="Volt", vsai="Out", p1=1.0, p2=2.0, p3=3.0, p4=4.0)

    ctrl2 = _roundtrip_dcdu(dcdu)._controladores[0]
    b = ctrl2._blocos[0]
    assert b.tipo == "LEDLAG"
    assert b.vent == "Volt"  # v0.12.3: "Volt" é vent, não stip
    assert b.stip == ""  # stip vazio
    assert b.vsai == "Out"
    assert ctrl == ctrl2


def test_cdu_variavel_efd_nao_confundida_com_stip_roundtrip():
    """Variável chamada 'Efd' não é confundida com stip=EFD (v0.12.3)."""
    dcdu = BlocoDCDU()
    ctrl = dcdu.novo_controlador(ncdu=1, nome="EFD_VAR")
    # Bloco GANHO com vent="Efd" (variável)
    ctrl.bloco(20, "GANHO", vent="Efd", vsai="Efd_ref", p1=10.0)

    ctrl2 = _roundtrip_dcdu(dcdu)._controladores[0]
    b = ctrl2._blocos[0]
    assert b.tipo == "GANHO"
    assert b.vent == "Efd"  # v0.12.3: "Efd" é vent, não stip
    assert b.stip == ""  # stip vazio
    assert b.vsai == "Efd_ref"
    assert ctrl == ctrl2


def test_cdu_bloco_import_com_stip_volt_roundtrip():
    """IMPORT com stip=VOLT (contexto diferente, é realmente stip) (v0.12.3)."""
    dcdu = BlocoDCDU()
    ctrl = dcdu.novo_controlador(ncdu=1, nome="IMPORT_VOLT")
    # IMPORT tem stip obrigatório, então "VOLT" é detectado como stip, não vent
    ctrl.bloco(30, "IMPORT", stip="VOLT", vsai="Vterminal")

    ctrl2 = _roundtrip_dcdu(dcdu)._controladores[0]
    b = ctrl2._blocos[0]
    assert b.tipo == "IMPORT"
    assert b.stip == "VOLT"  # stip corretamente detectado
    assert b.vent == ""  # vent vazio (IMPORT)
    assert b.vsai == "Vterminal"
    assert ctrl == ctrl2


# ---------------------------------------------------------------------------
# v0.14.2 – Desambiguação de stip por tipo de bloco (conclui a meta v0.12.3)
# Referências: blocos_CDU_completo.md (Cap. 29) e
# 02_controladores_def_usuario.md (subtipos PELE/QELE/PTER/... §29.3)
# ---------------------------------------------------------------------------


def test_cdu_export_stip_fora_do_conjunto_roundtrip():
    """EXPORT com stip fora do antigo conjunto de palavras-chave (ex: PELE).

    Regressão v0.14.2: o parser antigo só reconhecia stip pertencente a um
    conjunto fixo; 'PELE' (potência elétrica, §29.3 do manual) era consumido
    como vent e a variável real era perdida silenciosamente.
    """
    dcdu = BlocoDCDU()
    ctrl = dcdu.novo_controlador(ncdu=1, nome="EXPORT_PELE")
    ctrl.bloco(10, "EXPORT", stip="PELE", vent="Pele_mq")

    ctrl2 = _roundtrip_dcdu(dcdu)._controladores[0]
    b = ctrl2._blocos[0]
    assert b.tipo == "EXPORT"
    assert b.stip == "PELE"
    assert b.vent == "Pele_mq"
    assert b.vsai == ""
    assert ctrl == ctrl2


def test_cdu_import_stip_fora_do_conjunto_roundtrip():
    """IMPORT com stip fora do antigo conjunto (ex: QELE) faz roundtrip."""
    dcdu = BlocoDCDU()
    ctrl = dcdu.novo_controlador(ncdu=1, nome="IMPORT_QELE")
    ctrl.bloco(10, "IMPORT", stip="QELE", vsai="Qele_mq")

    ctrl2 = _roundtrip_dcdu(dcdu)._controladores[0]
    b = ctrl2._blocos[0]
    assert b.tipo == "IMPORT"
    assert b.stip == "QELE"
    assert b.vent == ""
    assert b.vsai == "Qele_mq"
    assert ctrl == ctrl2


def test_cdu_input_roundtrip():
    """INPUT: stip + vsai + P1 (Listagem 29.22 do manual: INPUT VOLT Vsai 9950)."""
    dcdu = BlocoDCDU()
    ctrl = dcdu.novo_controlador(ncdu=1, nome="CDU_INPUT")
    ctrl.bloco(10, "INPUT", stip="VOLT", vsai="Vsai", p1=9950.0)

    ctrl2 = _roundtrip_dcdu(dcdu)._controladores[0]
    b = ctrl2._blocos[0]
    assert b.tipo == "INPUT"
    assert b.stip == "VOLT"
    assert b.vent == ""
    assert b.vsai == "Vsai"
    assert b.p1 == 9950.0
    assert ctrl == ctrl2


def test_cdu_output_roundtrip():
    """OUTPUT: stip + vent + P1/P2 (Listagem 29.23 do manual: OUTPUT EFD Vent 4 10)."""
    dcdu = BlocoDCDU()
    ctrl = dcdu.novo_controlador(ncdu=1, nome="CDU_OUTPUT")
    ctrl.bloco(10, "OUTPUT", stip="EFD", vent="Vent", p1=4.0, p2=10.0)

    ctrl2 = _roundtrip_dcdu(dcdu)._controladores[0]
    b = ctrl2._blocos[0]
    assert b.tipo == "OUTPUT"
    assert b.stip == "EFD"
    assert b.vent == "Vent"
    assert b.vsai == ""
    assert b.p1 == 4.0 and b.p2 == 10.0
    assert ctrl == ctrl2


def test_cdu_seriet_roundtrip():
    """SERIET: stip + vsai + P1..P3 (§29.3 do manual, séries temporais)."""
    dcdu = BlocoDCDU()
    ctrl = dcdu.novo_controlador(ncdu=1, nome="CDU_SERIET")
    ctrl.bloco(10, "SERIET", stip="VOLT", vsai="Vserie", p1=1.0, p2=2.0, p3=0.98)

    ctrl2 = _roundtrip_dcdu(dcdu)._controladores[0]
    b = ctrl2._blocos[0]
    assert b.tipo == "SERIET"
    assert b.stip == "VOLT"
    assert b.vent == ""
    assert b.vsai == "Vserie"
    assert b.p1 == 1.0 and b.p2 == 2.0 and b.p3 == 0.98
    assert ctrl == ctrl2


def test_cdu_compar_gt_roundtrip():
    """COMPAR subtipo .GT. (Listagem 29.31: COMPAR .GT. Vent1 Vsai + entrada extra).

    Regressão v0.14.2: '.GT.' não pertencia ao antigo conjunto de palavras-chave
    e era consumido como vent, deslocando todos os campos seguintes.
    """
    dcdu = BlocoDCDU()
    ctrl = dcdu.novo_controlador(ncdu=1, nome="CDU_GT")
    ctrl.bloco(10, "COMPAR", stip=".GT.", vent="Vent1", vsai="Vsai").adicionar_entrada(
        "Vent2"
    )

    ctrl2 = _roundtrip_dcdu(dcdu)._controladores[0]
    b = ctrl2._blocos[0]
    assert b.tipo == "COMPAR"
    assert b.stip == ".GT."
    assert b.vent == "Vent1"
    assert b.vsai == "Vsai"
    assert len(b.linhas_extras) == 1
    assert ctrl == ctrl2


def test_cdu_logic_nand_roundtrip():
    """LOGIC subtipo .NAND. (§29.3): subtipo fora do antigo conjunto de palavras."""
    dcdu = BlocoDCDU()
    ctrl = dcdu.novo_controlador(ncdu=1, nome="CDU_NAND")
    ctrl.bloco(10, "LOGIC", stip=".NAND.", vent="Vent1", vsai="Vsai").adicionar_entrada(
        "Vent2"
    )

    ctrl2 = _roundtrip_dcdu(dcdu)._controladores[0]
    b = ctrl2._blocos[0]
    assert b.tipo == "LOGIC"
    assert b.stip == ".NAND."
    assert b.vent == "Vent1"
    assert b.vsai == "Vsai"
    assert ctrl == ctrl2


# ---------------------------------------------------------------------------
# v0.12 – Testes de Integração (todas as 3 metas juntas)
# ---------------------------------------------------------------------------


def test_cdu_integracao_v0_12_todas_metas():
    """Integração v0.12: IMPORT/EXPORT + <4 params + colisão nome (v0.12.1+2+3)."""
    dcdu = BlocoDCDU()
    ctrl = dcdu.novo_controlador(ncdu=1, nome="INTEGRACAO_V012")

    # v0.12.1: IMPORT com vent vazio
    ctrl.bloco(10, "IMPORT", stip="VOLT", vsai="Vt")

    # v0.12.2: WSHOUT com 3 parâmetros + vmin/vmax
    ctrl.bloco(
        20,
        "WSHOUT",
        vent="Vt",
        vsai="Vout_limited",
        p1=1.0,
        p2=2.0,
        p3=3.0,
        vmin="Vmin",
        vmax="Vmax",
    )

    # v0.12.3: Bloco com variável "Volt" (não confundida com stip)
    ctrl.bloco(
        30, "LEDLAG", vent="Volt", vsai="Volt_ref", p1=10.0, p2=0.1, p3=1.0, p4=0.05
    )

    # v0.12.1: EXPORT com vsai vazio
    ctrl.bloco(40, "EXPORT", stip="EFD", vent="Volt_ref")

    ctrl2 = _roundtrip_dcdu(dcdu)._controladores[0]

    # Validar bloco 1 (IMPORT)
    b1 = ctrl2._blocos[0]
    assert b1.tipo == "IMPORT"
    assert b1.stip == "VOLT" and b1.vsai == "Vt" and b1.vent == ""

    # Validar bloco 2 (WSHOUT 3 params)
    b2 = ctrl2._blocos[1]
    assert b2.tipo == "WSHOUT"
    assert b2.p1 == 1.0 and b2.p2 == 2.0 and b2.p3 == 3.0
    assert b2.p4 is None or b2.p4 == 0
    assert b2.vmin == "Vmin" and b2.vmax == "Vmax"

    # Validar bloco 3 (LEDLAG com Volt como vent, não stip)
    b3 = ctrl2._blocos[2]
    assert b3.tipo == "LEDLAG"
    assert b3.stip == ""
    assert b3.vent == "Volt" and b3.vsai == "Volt_ref"

    # Validar bloco 4 (EXPORT)
    b4 = ctrl2._blocos[3]
    assert b4.tipo == "EXPORT"
    assert b4.stip == "EFD" and b4.vent == "Volt_ref" and b4.vsai == ""

    # Equivalência estrutural
    assert ctrl == ctrl2


# ---------------------------------------------------------------------------
# v0.14 – Robustez I/O (codificação latin-1)
# ---------------------------------------------------------------------------


def test_caso_exportar_com_encoding_latin1():
    """Caso exportado em latin-1 pode ser lido de volta (roundtrip I/O)."""
    import tempfile
    from pathlib import Path

    caso = CasoAnatem()
    caso.titulo = "Caso de Teste Codificação"
    caso.darq.sav = "rede.sav"
    caso.dsim.tini = 0.0
    caso.dsim.tfim = 10.0

    # Exportar para arquivo temporário
    with tempfile.TemporaryDirectory() as tmpdir:
        arquivo = Path(tmpdir) / "teste_encoding.stb"
        caso.exportar(arquivo)

        # Verificar que arquivo foi criado
        assert arquivo.exists()

        # Verificar que arquivo está em latin-1
        conteudo_bytes = arquivo.read_bytes()
        # Header começa com comentário "("
        assert conteudo_bytes.startswith(b"(") or conteudo_bytes.startswith(b"CASO")

        # Ler de volta
        caso2 = CasoAnatem.ler(arquivo)

        # Validar roundtrip
        assert caso2.titulo == caso.titulo
        assert caso2.darq.sav == caso.darq.sav
        assert caso2.dsim.tini == caso.dsim.tini
        assert caso2.dsim.tfim == caso.dsim.tfim


def test_caso_deck_exportar_encoding_latin1():
    """Exportação preserva conteúdo em latin-1 (sem corrupção)."""
    import tempfile
    from pathlib import Path

    caso = CasoAnatem()
    caso.titulo = "Teste de Caracteres"
    caso.darq.sav = "rede.sav"
    caso.dsim.tini = 0.0
    caso.dsim.tfim = 10.0

    with tempfile.TemporaryDirectory() as tmpdir:
        arquivo = Path(tmpdir) / "teste_chars.stb"
        caso.exportar(arquivo)

        # Verificar que arquivo foi criado
        assert arquivo.exists()

        # Ler conteúdo com encoding latin-1
        conteudo = arquivo.read_text(encoding="latin-1")

        # Verificar que conteúdo está presente
        assert "Teste de Caracteres" in conteudo
        assert "rede.sav" in conteudo


def test_caso_exportar_char_fora_latin1_valueerror_descritivo():
    """exportar() com caractere fora de latin-1 levanta ValueError claro (v0.14.1).

    Antes, o usuário recebia um UnicodeEncodeError obscuro do codec; a meta
    v0.14.1 exige mensagem descritiva apontando o caractere e a linha.
    """
    import pytest
    import tempfile
    from pathlib import Path

    caso = CasoAnatem()
    caso.titulo = "Curto trifásico — barra 5"  # em-dash U+2014 fora de latin-1

    with tempfile.TemporaryDirectory() as tmpdir:
        arquivo = Path(tmpdir) / "teste_unicode.stb"
        with pytest.raises(ValueError) as excinfo:
            caso.exportar(arquivo)

        msg = str(excinfo.value)
        # Mensagem descritiva: identifica o caractere, o codepoint e a linha
        assert "'—'" in msg or "—" in msg
        assert "U+2014" in msg
        assert "latin-1" in msg
        assert "linha" in msg
        # Não é o UnicodeEncodeError bruto do codec
        assert not isinstance(excinfo.value, UnicodeEncodeError)
        # Nenhum arquivo corrompido deixado para trás
        assert not arquivo.exists()


def test_caso_salvar_cdu_char_fora_latin1_valueerror_descritivo():
    """salvar_cdu() também valida latin-1 com mensagem clara (v0.14.1)."""
    import pytest
    import tempfile
    from pathlib import Path
    from pyanatem import BlocoDCDU

    caso = CasoAnatem()
    dcdu = BlocoDCDU()
    dcdu.novo_controlador(ncdu=1, nome="AVR—01")  # em-dash fora de latin-1
    caso.dcdu = dcdu

    with tempfile.TemporaryDirectory() as tmpdir:
        arquivo = Path(tmpdir) / "teste_unicode.cdu"
        with pytest.raises(ValueError) as excinfo:
            caso.salvar_cdu(arquivo)

        msg = str(excinfo.value)
        assert "U+2014" in msg
        assert "latin-1" in msg
        assert not isinstance(excinfo.value, UnicodeEncodeError)
        assert not arquivo.exists()


def test_caso_multiplos_ciclos_io_roundtrip():
    """Múltiplos ciclos de exportar/ler mantêm integridade (no drift)."""
    import tempfile
    from pathlib import Path

    caso_orig = CasoAnatem()
    caso_orig.titulo = "Ciclos I/O"
    caso_orig.darq.sav = "rede.sav"
    caso_orig.darq.plt = "saida.plt"
    caso_orig.dsim.tini = 0.0
    caso_orig.dsim.tfim = 15.0
    caso_orig.dsim.delt = 0.01

    with tempfile.TemporaryDirectory() as tmpdir:
        arquivo = Path(tmpdir) / "ciclos.stb"

        # Ciclo 1: exportar
        caso_orig.exportar(arquivo)

        # Ciclo 2: ler
        caso1 = CasoAnatem.ler(arquivo)
        assert caso1.titulo == caso_orig.titulo
        assert caso1.dsim.tfim == caso_orig.dsim.tfim

        # Ciclo 3: re-exportar
        caso1.exportar(arquivo)

        # Ciclo 4: ler novamente
        caso2 = CasoAnatem.ler(arquivo)
        assert caso2.titulo == caso1.titulo
        assert caso2.dsim.tfim == caso1.dsim.tfim

        # Verificar que não houve drift nos valores
        assert caso2.dsim.tini == caso_orig.dsim.tini
        assert caso2.dsim.delt == caso_orig.dsim.delt


def test_parser_stb_encoding_latin1_leitura():
    """Parser lê arquivos latin-1 sem corrupção (errors='replace' tratado)."""
    import tempfile
    from pathlib import Path

    # Criar arquivo com conteúdo latin-1 e verificar que pode ser lido
    with tempfile.TemporaryDirectory() as tmpdir:
        arquivo = Path(tmpdir) / "latin1_test.stb"

        # Escrever com conteúdo básico em latin-1
        conteudo = """( Teste de encoding com caracteres
TITU
Caso de teste latin-1
DARQ
SIST    rede.sav
PLOT    saida.plt
DSIM
    0.0000   10.0000    0.0100
DEVT
999999
DPLT
999999
FIM
999999
"""
        arquivo.write_text(conteudo, encoding="latin-1")

        # Verificar que arquivo foi salvo em latin-1
        conteudo_lido = arquivo.read_text(encoding="latin-1")
        assert "Teste de encoding" in conteudo_lido
        assert "Caso de teste latin-1" in conteudo_lido

        # Parser lê com latin-1 (sem erro)
        from pyanatem.parser.stb import ParserSTB

        caso = ParserSTB.ler(arquivo)

        # Validar que foi parseado (título deve estar presente)
        assert caso.titulo == "Caso de teste latin-1"
