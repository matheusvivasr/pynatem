"""
tests/test_pyanatem.py – Suite de testes para o pyanatem (Sessão 3).
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
    d.sav = "rede.sav"; d.rela = "saida.rela"; d.log = "log.log"
    d.plt = "plot.plt"; d.plt_cdu = "cdu.plt"
    d.adicionar_cdu("ctrl.cdu"); d.adicionar_blt("bib.blt")
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
    d.npas = 2; d.mxit = 50
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
    d.tensao_barra(5); d.angulo_barra(5); d.frequencia_barra(5)
    d.angulo_maquina(5, 1); d.velocidade_maquina(5, 1)
    d.potencia_ativa(5, 1); d.potencia_reativa(5, 1)
    d.corrente_campo(5, 1); d.tensao_excitacao(5, 1)
    d.tensao_terminal(5, 1); d.potencia_eletrica(5, 1); d.potencia_mecanica(5, 1)
    d.fluxo_ativo(10, 20, 1); d.fluxo_reativo(10, 20, 1); d.corrente_circuito(10, 20, 1)
    d.potencia_carga(3); d.reativo_carga(3)
    t = d.serializar()
    for cod in ["VBAR", "TBAR", "FREQ", "DELT", "OMEG", "PGER", "QGER", "ICAM",
                "EEXC", "VTER", "PELM", "PMEC", "FLXP", "FLXQ", "FLXC", "PCAG", "QCAG"]:
        assert cod in t, f"Faltando {cod}"


# ===========================================================================
# BLOCOS – novidades sessão 3: OLTC / FACTS / HVDC / CDU
# ===========================================================================

def test_dplt_oltc():
    d = BlocoDPLT()
    d.tap_oltc(de=10, para=20, circ=1)
    assert "TAPO" in d.serializar()


def test_dplt_facts_svc():
    d = BlocoDPLT()
    d.reativo_svc(5); d.tensao_svc(5); d.susceptancia_svc(5)
    t = d.serializar()
    assert "QSVC" in t and "VSVC" in t and "BSVC" in t


def test_dplt_facts_tcsc():
    d = BlocoDPLT()
    d.reatancia_tcsc(10, 20, 1); d.potencia_tcsc(10, 20, 1)
    t = d.serializar()
    assert "XTCS" in t and "PTCS" in t


def test_dplt_facts_statcom():
    d = BlocoDPLT()
    d.reativo_statcom(3); d.tensao_statcom(3)
    t = d.serializar()
    assert "QSTA" in t and "VSTA" in t


def test_dplt_hvdc():
    d = BlocoDPLT()
    d.tensao_cc(1); d.corrente_cc(1); d.potencia_cc(1)
    d.angulo_disparo(1); d.angulo_extincao(1)
    t = d.serializar()
    for cod in ["VCCD", "ICCD", "PCCD", "ALFA", "GAMA"]:
        assert cod in t


def test_dplt_saida_cdu():
    d = BlocoDPLT()
    d.saida_cdu(num_cdu=2, num_bloco=7)
    t = d.serializar()
    assert "SCDU" in t and "2" in t and "7" in t


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
    caso.darq.sav = "rede.sav"; caso.dsim.tfim = 5.0
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
    caso.darq.sav = "x.sav"; caso.dsim.tini = 5.0; caso.dsim.tfim = 3.0
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
    caso.dsim.tfim = 0.05   # só 5 passos com delt=0.01
    caso.dsim.delt = 0.01
    erros = caso.validar()
    assert any("passos de integração" in e for e in erros)


def test_validar_eventos_sobrepostos():
    """Novo (sessão 3): dois eventos diferentes na mesma barra/instante."""
    caso = CasoAnatem()
    caso.darq.sav = "x.sav"
    caso.dsim.tfim = 10.0
    caso.devt.curto_barra(barra=5, tini=1.0, tipo="APCB")
    caso.devt.abertura_shunt(barra=5, tini=1.0)  # mesmo nb1, mesmo tini, código diferente
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
    caso.darq.sav = "x.sav"; caso.dsim.tfim = 3.0
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
    c1 = ensaio.novo_caso("a"); c2 = ensaio.novo_caso("b")
    c1.darq.sav = "alterado.sav"
    assert c2.darq.sav == "base.sav"


def test_ensaio_gerar_variacoes():
    ensaio = EnsaioAnatem.novo()
    ensaio._template.darq.sav = "base.sav"; ensaio._template.dsim.tfim = 5.0

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
    testes = [(k, v) for k, v in list(globals().items())
              if k.startswith("test_") and callable(v)]
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
# DMDG – Sessão 4, Etapa 4.1
# ===========================================================================

from pyanatem import BlocoDMDG


def test_dmdg_md01_serializa_campos_basicos():
    """MD01: No, L'd, Ra, H, D, MVA presentes na saída."""
    b = BlocoDMDG()
    b.adicionar_md01(no=20, ld=20.0, h=999.0, mva=9999.0)
    t = b.serializar()
    assert "DMDG MD01" in t
    assert "20" in t
    assert "20.000" in t    # ld
    assert "999.000" in t   # h
    assert "9999.0" in t    # mva
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
        ld=170.0, lq=100.0, ld_trans=37.0,
        ld_sub=22.0, ll=15.4,
        td_trans=9.00, td_sub=0.060, tq_sub=0.200,
        ra=1.6, h=300.0, mva=100.0,
    )
    t = b.serializar()
    assert "DMDG MD02" in t
    assert "14" in t
    # valores da régua 1
    assert "170.000" in t
    assert "100.000" in t
    assert "37.000" in t
    # valores da régua 2
    assert "300.000" in t   # h
    assert "100.0" in t     # mva
    # duas linhas com "14" (régua 1 e régua 2)
    linhas_com_14 = [l for l in t.splitlines() if l.strip().startswith("14")]
    assert len(linhas_com_14) == 2


def test_dmdg_md03_campos_extras():
    """MD03: L'q e T'q presentes na saída (diferença em relação ao MD02)."""
    b = BlocoDMDG()
    b.adicionar_md03(
        no=50,
        ld=180.0, lq=170.0,
        ld_trans=28.0, lq_trans=45.0,
        ld_sub=20.0, ll=14.0,
        td_trans=8.0, tq_trans=1.5,
        td_sub=0.04, tq_sub=0.07,
        h=4.5, mva=500.0,
    )
    t = b.serializar()
    assert "DMDG MD03" in t
    assert "45.000" in t    # lq_trans
    assert "1.5000" in t    # tq_trans


def test_dmdg_mistura_md01_md02():
    """MD01 e MD02 no mesmo BlocoDMDG geram sub-blocos independentes."""
    b = BlocoDMDG()
    b.adicionar_md01(no=10, ld=20.0, h=5.0, mva=100.0)
    b.adicionar_md02(
        no=20,
        ld=150.0, lq=90.0, ld_trans=30.0, ld_sub=20.0, ll=12.0,
        td_trans=7.0, td_sub=0.05, tq_sub=0.15,
        h=4.0, mva=200.0,
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
    result = b.adicionar_md01(no=1, ld=20.0, h=5.0, mva=100.0) \
              .adicionar_md02(
                  no=2, ld=150.0, lq=90.0, ld_trans=30.0, ld_sub=20.0, ll=12.0,
                  td_trans=7.0, td_sub=0.05, tq_sub=0.15,
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
        ld=170.0, lq=100.0, ld_trans=37.0,
        ld_sub=22.0, ll=15.4,
        td_trans=9.00, td_sub=0.060, tq_sub=0.200,
        ra=1.6, h=300.0, mva=100.0,
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
        ld=180.0, lq=170.0,
        ld_trans=28.0, lq_trans=45.0,
        ld_sub=20.0, ll=14.0,
        td_trans=8.0, tq_trans=1.5,
        td_sub=0.04, tq_sub=0.07,
        h=4.5, mva=500.0,
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
# ETAPA 4.2 – BlocoDMAQ completo
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
    d.adicionar_maquina(barra=3500, grupo=10, p=60, q=60, und=3,
                        mg=753, mt=144, mt_cdu=True, mv=126)
    t = d.serializar()
    assert "144u" in t or "144U" in t or "144" in t
    assert "3500" in t

def test_dmaq_adicionar_maquina_com_pss():
    """DMAQ: Me (estabilizador) preenchido."""
    d = BlocoDMAQ()
    d.adicionar_maquina(barra=3500, grupo=20, p=40, q=40, und=2,
                        mg=753, mt=81, mv=126, me=39)
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
    caso.adicionar_maquina(barra=3500, grupo=10, p=60, q=60, und=3,
                           mg=753, mt=144, mt_cdu=True, mv=126)

    stb = tmp_path / "caso.stb"
    caso.exportar(stb)
    lido = CasoAnatem.ler(stb)
    assert lido.dmaq.tem_dados()
    barras = [a.barra for a in lido.dmaq.associacoes]
    assert 1432 in barras
    assert 3500 in barras


# ===========================================================================
# ETAPA 5 – Serialização e parsing posicional do DMAQ  (sub-metas v0.5.1–0.5.3 → entrega v0.6.0)
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
        barra=3500, grupo=10, p=60, q=60, und=3,
        mg=753, mt=78, mt_cdu=False,
        mv=126, mv_cdu=False,
        me=39, me_cdu=False,
        xvd=0.05, nbc=0,
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
        barra=3500, grupo=10, p=60, q=60, und=3,
        mg=753, mt=144, mt_cdu=True,
        mv=126, mv_cdu=True,
        me=39, me_cdu=True,
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
    caso.dmaq.adicionar_maquina(barra=300, grupo=3, p=100, q=100, und=2,
                                mg=51, mt=144, mt_cdu=True, mv=126, mv_cdu=False)
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
    nb_str  = linha_dados[0:6].strip()
    gr_str  = linha_dados[6:10].strip()
    p_str   = linha_dados[10:14].strip()
    q_str   = linha_dados[14:18].strip()
    und_str = linha_dados[18:22].strip()
    mg_str  = linha_dados[22:28].strip()
    mt_str  = linha_dados[28:34].strip()
    cdu_str = linha_dados[34:35] if len(linha_dados) > 34 else " "

    assert nb_str == "3500", f"Nb incorreto: {repr(nb_str)}"
    assert gr_str == "10",   f"Gr incorreto: {repr(gr_str)}"
    assert p_str  == "",     f"P deveria estar em branco: {repr(p_str)}"
    assert q_str  == "",     f"Q deveria estar em branco: {repr(q_str)}"
    assert und_str == "",    f"Und deveria estar em branco: {repr(und_str)}"
    assert mg_str == "753",  f"Mg incorreto: {repr(mg_str)}"
    assert mt_str == "144",  f"Mt incorreto: {repr(mt_str)}"
    assert cdu_str.lower() == "u", f"Flag CDU deveria ser 'u': {repr(cdu_str)}"


# ===========================================================================
# ETAPA 4.3 – FACTS e HVDC
# ===========================================================================

from pyanatem import BlocoSVC, BlocoTCSC, BlocoSTATCOM, BlocoHVDC

def test_svc_serializa():
    b = BlocoSVC()
    b.adicionar(no=1, nb=100, bmin=-0.5, bmax=0.5, vref=1.0, modelo=1)
    t = b.serializar()
    assert "DCER" in t
    assert "100" in t
    assert "999999" in t

def test_tcsc_serializa():
    b = BlocoTCSC()
    b.adicionar(no=1, de=100, para=200, circ=1, xcmin=0.0, xcmax=0.3)
    t = b.serializar()
    assert "DCSC" in t
    assert "100" in t and "200" in t

def test_statcom_serializa():
    b = BlocoSTATCOM()
    b.adicionar(no=1, nb=50, tipo_vsi="STATCOM", qmin=-0.2, qmax=0.2)
    t = b.serializar()
    assert "DVSI" in t
    assert "STATCOM" in t
    assert "50" in t

def test_hvdc_serializa():
    b = BlocoHVDC()
    b.adicionar(no=1, nb_ret=10, nb_inv=20, pcc=900.0, vcc=600.0)
    t = b.serializar()
    assert "DCNV" in t
    assert "900" in t
    assert "600" in t

def test_facts_encadeamento():
    """Métodos adicionar retornam self para encadeamento."""
    b = BlocoSVC()
    result = b.adicionar(no=1, nb=100).adicionar(no=2, nb=200)
    assert result is b
    assert len(b._equipamentos) == 2

def test_facts_tem_dados():
    b = BlocoSVC()
    assert not b.tem_dados()
    b.adicionar(no=1, nb=100)
    assert b.tem_dados()


# ===========================================================================
# ETAPA 4.4 / 4.5 – BlocoDCDU e CDU
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
    b = BlocoCDU(nb=20, tipo="LEDLAG", vent="E", vsai="Y",
                 p1=200.0, p2=0.0, p3=1.0, p4=0.05,
                 vmin="Emin", vmax="Emax")
    t = b.serializar()
    assert "LEDLAG" in t
    assert "200" in t
    assert "Emin" in t

def test_cdu_bloco_wshout():
    b = BlocoCDU(nb=30, tipo="WSHOUT", vent="W", vsai="Ypss",
                 p1=5.0, p2=2.0, p3=2.0, vmin="Lmn", vmax="Lmx")
    t = b.serializar()
    assert "WSHOUT" in t

def test_cdu_controlador_avr_simples():
    """Constrói AVR com WSHOUT + LEDLAG + limites."""
    ctrl = ControladorCDU(ncdu=100, nome="AVR_G1")
    ctrl.defpar("#Vref", 1.0, "Tensão de referência")
    ctrl.bloco(10, "IMPORT", stip="VOLT", vsai="Vt")
    b_soma = ctrl.bloco(20, "SOMA", vent="Vref", vsai="Erro")
    b_soma.adicionar_entrada("Vt", polaridade="-")
    ctrl.bloco(30, "LEDLAG", vent="Erro", vsai="Efd",
               p1=200.0, p2=0.0, p3=1.0, p4=0.05,
               vmin="Emin", vmax="Emax")
    ctrl.bloco(40, "EXPORT", stip="EFD", vent="Efd")
    ctrl.defval("Vref",  1.0)
    ctrl.defval("Emin", -5.0)
    ctrl.defval("Emax",  5.0)

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
    pss.bloco(10, "WSHOUT", vent="W", vsai="Ypss",
              p1=5.0, p2=2.0, p3=2.0, vmin="Lmn", vmax="Lmx")
    pss.defval("Lmn", -0.1)
    pss.defval("Lmx",  0.1)

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
    b_exp = BlocoCDU(nb=2, tipo="EXPORT", stip="EFD",  vent="Efd")
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
# ETAPA 4.6 – Análise de contingências automatizada
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
        {"nome": "C4", "tipo": "abertura_linha", "de": 10, "para": 30,
         "t_aber": 0.5, "t_fech": 1.0},
        {"nome": "C5", "tipo": "step", "barra": 5, "unidade": 1, "t_ini": 2.0, "delta": 0.05},
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
        {"nome": "CONT_A", "tipo": "curto_barra", "barra": 5, "t_apl": 1.0, "t_rem": 1.1},
        {"nome": "CONT_B", "tipo": "curto_barra", "barra": 6, "t_apl": 1.0, "t_rem": 1.1},
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
        {"arquivo": "/tmp/C1.stb", "convergiu": True,  "erros": [], "avisos": [], "passou": True},
        {"arquivo": "/tmp/C2.stb", "convergiu": False, "erros": ["ERRO X"], "avisos": [], "passou": False},
    ]
    rel = ensaio.relatorio_consolidado(resultados)
    assert "C1" in rel
    assert "C2" in rel
    assert "Sim" in rel
    assert "Não" in rel


# ===========================================================================
# ETAPA 4.7 – LeitorSAV e validação cruzada
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
    sav_path.write_text("DBAR\n5 BUS5 GD 1 1 138. 0 0 100 0\n99999\n", encoding="latin-1")

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
    sav_path.write_text("DBAR\n5 BUS5 GD 1 1 138. 0 0 100 0\n99999\n", encoding="latin-1")

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
        encoding="latin-1"
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
        encoding="latin-1"
    )
    r = LeitorSAV.ler(sav_path)
    assert 1 in r.barras
    assert 2 in r.barras
    assert (1, 2, 1) in r.chaves_circuitos()


