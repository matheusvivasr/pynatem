"""Configuração compartilhada para a suíte de testes.

Isola cada teste em um diretório temporário para que arquivos gerados
(`*.stb`, `*.plt`, `*.rela`, etc.) nunca poluam a raiz do repositório.
"""

import os

import pytest


@pytest.fixture(autouse=True)
def _isolar_diretorio(tmp_path, monkeypatch):
    """Executa cada teste dentro de um diretório temporário próprio.

    Testes que escrevem arquivos com nomes relativos (ex.: ``caso.exportar("x.stb")``)
    passam a gravar em ``tmp_path`` em vez do diretório de trabalho corrente,
    mantendo o repositório limpo.
    """
    monkeypatch.chdir(tmp_path)
    yield
    # tmp_path é removido automaticamente pelo pytest ao final do teste
    os.chdir  # no-op explícito para clareza
