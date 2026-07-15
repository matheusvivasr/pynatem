"""
pynatem – Biblioteca Python para geração, manipulação, parsing e execução
automatizada de arquivos ANATEM (.stb, .dat, .cdu, .blt).
"""

from importlib.metadata import PackageNotFoundError, version

from .anarede import LeitorSAV, ResultadoSAV
from .blocos import (
    BlocoDARQ,
    BlocoDCAG,
    BlocoDCAR,
    BlocoDCCT,
    BlocoDCLI,
    BlocoDCST,
    BlocoDDFM,
    BlocoDELO,
    BlocoDEST,
    BlocoDEVT,
    BlocoDFLA,
    BlocoDFNT,
    BlocoDGER,
    BlocoDGSE,
    BlocoDLTC,
    BlocoDMAQ,
    BlocoDMCV,
    BlocoDMDG,
    BlocoDMEL,
    BlocoDMOT,
    BlocoDMTC,
    BlocoDOPC,
    BlocoDPLT,
    BlocoDRGT,
    BlocoDRGV,
    BlocoDSIM,
    BlocoHVDC,
    BlocoSTATCOM,
    BlocoSVC,
    BlocoTCSC,
)
from .caso import CasoAnatem
from .cdu import (
    BlocoCDU,
    BlocoDCDU,
    ControladorCDU,
    ParametroCDU,
    ValorDefaultCDU,
    ValorInicialCDU,
)
from .ensaio import EnsaioAnatem
from .posprocessamento import (
    LeitorPLT,
    LeitorRelatorio,
    ResultadoExecucao,
    ResultadoPLT,
)

__all__ = [
    "CasoAnatem",
    "EnsaioAnatem",
    "BlocoDARQ",
    "BlocoDOPC",
    "BlocoDSIM",
    "BlocoDEVT",
    "BlocoDPLT",
    "BlocoDMAQ",
    "BlocoDMDG",
    "BlocoDRGT",
    "BlocoDRGV",
    "BlocoDEST",
    "BlocoDCST",
    "BlocoDCAG",
    "BlocoDCCT",
    "BlocoDCAR",
    "BlocoDGER",
    "BlocoDMTC",
    "BlocoDLTC",
    "BlocoDFLA",
    "BlocoDMOT",
    "BlocoDGSE",
    "BlocoDFNT",
    "BlocoDMEL",
    "BlocoDMCV",
    "BlocoDCLI",
    "BlocoSVC",
    "BlocoTCSC",
    "BlocoSTATCOM",
    "BlocoHVDC",
    "BlocoDELO",
    "BlocoDDFM",
    "LeitorPLT",
    "ResultadoPLT",
    "LeitorRelatorio",
    "ResultadoExecucao",
    "BlocoCDU",
    "ParametroCDU",
    "ValorInicialCDU",
    "ValorDefaultCDU",
    "ControladorCDU",
    "BlocoDCDU",
    "LeitorSAV",
    "ResultadoSAV",
]

try:
    # Fonte única da versão: o campo `version` do pyproject.toml, lido do
    # metadata do pacote instalado. Evita o drift entre as duas declarações.
    __version__ = version("pynatem")
except PackageNotFoundError:
    # Execução direta do repositório, sem instalação (ex.: `python -c` na raiz).
    __version__ = "0.0.0.dev0"
