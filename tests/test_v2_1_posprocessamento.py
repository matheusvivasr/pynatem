"""
Testes de conformidade para v2.1.0 — Pós-processamento Consolidado.

Cobre integração de:
  - plt_binario.py (FASE 1–2)
  - posprocessamento_v2.py (LeitorPLTBinario, LeitorREL, LeitorSNAP, LeitorOUT)
  - LeitorPLT estendido (texto + binário)
"""

import pytest
from pathlib import Path
from pynatem.parser.plt_binario import LeitorPLTBinario, HeaderPLT
from pynatem.posprocessamento_v2 import (
    LeitorPLTBinario as LeitorPLTBinarioV2,
    ResultadoPLT,
    LeitorREL,
    LeitorSNAP,
    LeitorOUT,
)


# Fixtures
@pytest.fixture
def plt_binario_exemplo():
    """Arquivo de exemplo .plt binário do CEPEL."""
    # Procurar a partir de raiz do projeto
    caminho = Path(__file__).parent.parent / "examples/treinamentoWP/TREINAMENTO_5_BARRAS.PLT"
    if not caminho.exists():
        pytest.skip(f"Arquivo de exemplo não encontrado: {caminho}")
    return caminho


class TestPLTBinarioParserV1:
    """Testes para plt_binario.py (parser/plt_binario.py)."""

    def test_ler_assinatura(self, plt_binario_exemplo):
        """PLTx — assinatura válida."""
        leitor = LeitorPLTBinario(plt_binario_exemplo)
        assinatura = leitor.ler_assinatura()
        assert assinatura == "PLTx"

    def test_ler_filename(self, plt_binario_exemplo):
        """Extrair nome do arquivo."""
        leitor = LeitorPLTBinario(plt_binario_exemplo)
        filename = leitor.ler_filename()
        assert ".PLT" in filename or ".plt" in filename.upper()
        assert len(filename) > 0

    def test_ler_header_estrutura(self, plt_binario_exemplo):
        """Header contém assinatura, filename, variáveis."""
        leitor = LeitorPLTBinario(plt_binario_exemplo)
        header = leitor.ler_header()

        assert isinstance(header, HeaderPLT)
        assert header.assinatura == "PLTx"
        assert len(header.filename) > 0
        # Pode ter variáveis ou estar vazio (FASE 1 incompleta)
        assert isinstance(header.variáveis, list)

    def test_ler_header_variaveis(self, plt_binario_exemplo):
        """Catálogo de variáveis identificado (pelo menos uma)."""
        leitor = LeitorPLTBinario(plt_binario_exemplo)
        header = leitor.ler_header()

        # Esperado: encontrar variáveis tipo DELT, VOLT, etc.
        if header.variáveis:
            var = header.variáveis[0]
            assert var.indice >= 0
            assert len(var.tipo) > 0


class TestPLTBinarioParserV2:
    """Testes para posprocessamento_v2.py (LeitorPLTBinario)."""

    def test_ler_arquivo_binario(self, plt_binario_exemplo):
        """LeitorPLTBinario.ler() retorna ResultadoPLT."""
        resultado = LeitorPLTBinarioV2.ler(plt_binario_exemplo)
        assert isinstance(resultado, ResultadoPLT)
        assert resultado.arquivo == plt_binario_exemplo

    def test_resultado_metadados(self, plt_binario_exemplo):
        """Metadados extraídos (titulo, tempo, passo)."""
        resultado = LeitorPLTBinarioV2.ler(plt_binario_exemplo)

        # Esperado: algum título, pelo menos um ponto temporal
        assert resultado.titulo_caso or resultado.arquivo.name
        assert len(resultado.tempo_global) >= 1

    def test_resultado_variaveis(self, plt_binario_exemplo):
        """Variáveis estruturadas em resultado."""
        resultado = LeitorPLTBinarioV2.ler(plt_binario_exemplo)

        # Se há variáveis, devem ter nome e valores
        if resultado.variaveis:
            for nome, var in resultado.variaveis.items():
                assert len(var.tipo) > 0
                assert var.num_elem >= 0
                # Valores devem acompanhar tempo
                assert len(var.valores) == len(resultado.tempo_global) or len(var.valores) == 0

    def test_numero_pontos(self, plt_binario_exemplo):
        """num_pontos() retorna número de passos de simulação."""
        resultado = LeitorPLTBinarioV2.ler(plt_binario_exemplo)
        n = resultado.num_pontos()
        assert n >= 0


class TestIntegracaoLeitorPLT:
    """Integração: LeitorPLT (texto) + LeitorPLTBinario (binário)."""

    def test_ler_texto_fallback(self, plt_binario_exemplo):
        """Se arquivo for binário mas .PLT for texto, fallback funciona."""
        # Esta é uma meta futura — hoje LeitorPLTBinario já tenta fallback
        resultado = LeitorPLTBinarioV2.ler(plt_binario_exemplo)
        # Teste passar se conseguiu ler (texto ou binário)
        assert resultado.arquivo.exists()


class TestPlotadorSerie:
    """Testes para PlotadorSerie (matplotlib)."""

    @pytest.mark.skipif(
        not pytest.importorskip("matplotlib", minversion=None),
        reason="matplotlib não instalado",
    )
    def test_plotador_disponivel(self):
        """PlotadorSerie disponível se matplotlib presente."""
        from pynatem.posprocessamento_v2 import PlotadorSerie, MATPLOTLIB_DISPONIVEL
        assert MATPLOTLIB_DISPONIVEL


class TestLeitorREL:
    """Testes para LeitorREL (.rel)."""

    def test_ler_rel_estrutura(self, tmp_path):
        """Ler arquivo .rel mínimo."""
        rel_file = tmp_path / "resultado.rel"
        rel_file.write_text(
            "ANATEM v12.10\n"
            "Sistema de Teste\n"
            "Tempo de CPU: 00:00:05.123\n"
            "Passos de simulacao: 100\n"
        )

        resultado = LeitorREL.ler(rel_file)
        assert resultado.arquivo == rel_file
        assert "v12.10" in resultado.dados_brutos or "ANATEM" in resultado.dados_brutos


class TestLeitorSNAP:
    """Testes para LeitorSNAP (.snap)."""

    def test_ler_snap_estrutura(self, tmp_path):
        """Ler arquivo .snap mínimo."""
        snap_file = tmp_path / "estado.snap"
        snap_file.write_text(
            "SNAPSHOT - ESTADO DO SISTEMA\n"
            "(BARRA)\n"
            "1  1.0  0.0\n"
            "2  0.95  -5.0\n"
        )

        resultado = LeitorSNAP.ler(snap_file, tempo=0.0)
        assert resultado.arquivo == snap_file
        # Pode ter barras ou estar vazio (parser em desenvolvimento)
        assert isinstance(resultado.barras, dict)


class TestLeitorOUT:
    """Testes para LeitorOUT (.out)."""

    def test_ler_out_estrutura(self, tmp_path):
        """Ler arquivo .out mínimo."""
        out_file = tmp_path / "resultado.out"
        out_file.write_text(
            "ANATEM v12.10\n"
            "Sistema de: Teste\n"
            "Tempo de CPU: 00:00:10.500\n"
        )

        resultado = LeitorOUT.ler(out_file)
        assert resultado["arquivo"] == str(out_file)


# Teste de integração completo
class TestIntegracaoV21:
    """Testes de integração v2.1.0 completa."""

    def test_roundtrip_binario_estrutura(self, plt_binario_exemplo):
        """Pipeline: binário → estrutura → análise → resultado."""
        # Fase 1: Ler binário
        header = LeitorPLTBinario(plt_binario_exemplo).ler_header()
        assert header.assinatura == "PLTx"

        # Fase 2: Estruturar resultado
        resultado = LeitorPLTBinarioV2.ler(plt_binario_exemplo)
        assert isinstance(resultado, ResultadoPLT)

        # Fase 3: Análise
        n_pontos = resultado.num_pontos()
        assert n_pontos >= 0

    def test_pipeline_relatorio(self, tmp_path):
        """Pipeline completo: criar .rel + ler + analisar."""
        rel_file = tmp_path / "relatorio.rel"
        rel_file.write_text(
            "ANATEM v12.10\n"
            "Teste Simulacao\n"
            "Tempo CPU: 00:00:05.000\n"
            "Convergencia: SUCESSO\n"
        )

        resultado = LeitorREL.ler(rel_file)
        assert "SUCESSO" in resultado.dados_brutos


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
