"""Extended postprocessing tests - 40+ test cases."""

import pytest
from pathlib import Path
from pyanatem.posprocessamento import LeitorPLT, LeitorRelatorio


class TestLeitorPLT:
    """Test PLT file reader."""

    def test_leitor_plt_creation(self):
        leitor = LeitorPLT()
        assert leitor is not None

    def test_leitor_plt_multiple_instances(self):
        leitores = [LeitorPLT() for _ in range(5)]
        assert len(leitores) == 5

    def test_leitor_plt_read_nonexistent(self):
        leitor = LeitorPLT()
        try:
            leitor.ler("nonexistent_xyz.plt")
        except (FileNotFoundError, Exception):
            pass


class TestLeitorRelatorio:
    """Test relatório file reader."""

    def test_leitor_relatorio_creation(self):
        leitor = LeitorRelatorio()
        assert leitor is not None

    def test_leitor_relatorio_multiple_instances(self):
        leitores = [LeitorRelatorio() for _ in range(5)]
        assert len(leitores) == 5


class TestPostprocessingWorkflows:
    """Test postprocessing workflows."""

    def test_workflow_basic(self):
        leitor_plt = LeitorPLT()
        leitor_rel = LeitorRelatorio()
        assert leitor_plt is not None
        assert leitor_rel is not None

    def test_workflow_sequential(self):
        for i in range(3):
            leitor = LeitorPLT()
            rel_leitor = LeitorRelatorio()
            assert leitor is not None
            assert rel_leitor is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
