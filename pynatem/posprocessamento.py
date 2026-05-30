"""
posprocessamento.py – Leitura de arquivos de saída do ANATEM (.plt, .rela, .log).

IMPORTANTE sobre o formato .plt:
    O ANATEM pode gravar plotagem em formato binário proprietário OU em
    formato texto, dependendo da configuração de saída. Este módulo
    implementa leitura do formato TEXTO (cabeçalho com nomes de variável
    seguido de colunas numéricas delimitadas por espaço, primeira coluna
    = tempo). NÃO decodifica o formato binário proprietário — se o seu
    .plt não for lido corretamente, verifique a opção de formato de saída
    no manual (Parte X) ou gere a saída em modo texto/ASCII.

    Este é um leitor best-effort: a estrutura exata de colunas do .plt não
    pôde ser confirmada verbatim contra o manual nesta sessão (limitação de
    acesso ao PDF por página específica). Valide contra um arquivo .plt
    real antes de uso em produção.

Para .rela e .log (sempre texto), a leitura é direta por varredura de
palavras-chave conhecidas (CONVERGIU, DIVERG, ERRO, AVISO).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Dict, List, Optional, Union

if TYPE_CHECKING:
    import pandas as pd


# ---------------------------------------------------------------------------
# Leitura de .plt
# ---------------------------------------------------------------------------


@dataclass
class ResultadoPLT:
    """Dados de plotagem lidos de um arquivo .plt em formato texto.

    Atributos:
        variaveis: nomes das colunas (conforme cabeçalho do arquivo).
        tempo:     lista de instantes de tempo [s].
        dados:     dict variável → lista de valores (mesmo tamanho de `tempo`).
    """

    variaveis: List[str] = field(default_factory=list)
    tempo: List[float] = field(default_factory=list)
    dados: Dict[str, List[float]] = field(default_factory=dict)

    def para_dict(self) -> Dict[str, List[float]]:
        """Retorna um dict {'tempo': [...], variavel: [...], ...}."""
        out = {"tempo": self.tempo}
        out.update(self.dados)
        return out

    def para_dataframe(self) -> "pd.DataFrame":
        """Converte para pandas.DataFrame.

        Raises:
            ImportError: se pandas não estiver instalado.
        """
        try:
            import pandas as pd
        except ImportError as e:
            raise ImportError(
                "pandas não está instalado. Use `pip install pandas` "
                "ou `.para_dict()` para obter os dados sem pandas."
            ) from e
        return pd.DataFrame(self.para_dict())

    def valores(self, variavel: str) -> List[float]:
        """Retorna a série temporal de uma variável específica.

        Raises:
            KeyError: se a variável não existir nos dados lidos.
        """
        if variavel not in self.dados:
            disponiveis = ", ".join(self.dados.keys())
            raise KeyError(
                f"Variável '{variavel}' não encontrada. Disponíveis: {disponiveis}"
            )
        return self.dados[variavel]


def _parece_binario(texto: str, limiar: float = 0.05) -> bool:
    """Heurística: fração de caracteres de controle nos primeiros 2000 chars.

    Usado para detectar arquivos .plt binários (que o LeitorPLT não suporta),
    já que a decodificação latin-1 nunca falha por si só (mapeia todo byte
    0-255 para um caractere válido).
    """
    amostra = texto[:2000]
    if not amostra:
        return False
    controle = sum(1 for c in amostra if ord(c) < 32 and c not in "\n\r\t")
    return (controle / len(amostra)) > limiar


class LeitorPLT:
    """Leitor de arquivos .plt do ANATEM em formato TEXTO.

    Espera um cabeçalho com nomes de coluna seguido por linhas numéricas
    delimitadas por espaço/tab, primeira coluna = tempo.

    NÃO suporta o formato binário proprietário do ANATEM.
    """

    @staticmethod
    def ler(caminho: Union[str, Path]) -> ResultadoPLT:
        """Lê um arquivo .plt texto e retorna um ResultadoPLT.

        Args:
            caminho: caminho do arquivo .plt.

        Returns:
            ResultadoPLT com variáveis, tempo e dados.

        Raises:
            ValueError: se o arquivo parecer binário (heurística de
                caracteres de controle).
        """
        caminho = Path(caminho)
        texto = caminho.read_text(encoding="latin-1", errors="replace")

        if _parece_binario(texto):
            raise ValueError(
                f"'{caminho}' parece estar em formato binário proprietário do "
                "ANATEM, não suportado por este leitor. Gere a saída em modo "
                "texto/ASCII ou use uma ferramenta específica do CEPEL."
            )

        linhas = [l for l in texto.splitlines() if l.strip()]
        if not linhas:
            return ResultadoPLT()

        cabecalho = linhas[0].split()
        nomes_vars = cabecalho[1:] if len(cabecalho) > 1 else []

        tempo: List[float] = []
        dados: Dict[str, List[float]] = {v: [] for v in nomes_vars}

        for linha in linhas[1:]:
            partes = linha.split()
            if not partes:
                continue
            try:
                t = float(partes[0])
            except ValueError:
                continue  # linha não numérica (ex: separador de bloco), ignora
            tempo.append(t)
            for i, nome in enumerate(nomes_vars):
                try:
                    val = float(partes[i + 1]) if i + 1 < len(partes) else float("nan")
                except ValueError:
                    val = float("nan")
                dados[nome].append(val)

        return ResultadoPLT(variaveis=nomes_vars, tempo=tempo, dados=dados)


# ---------------------------------------------------------------------------
# Leitura de .rela / .log
# ---------------------------------------------------------------------------


@dataclass
class ResultadoExecucao:
    """Resumo extraído de um arquivo .rela ou .log do ANATEM.

    Atributos:
        convergiu:     True/False/None (None = indeterminado pela varredura).
        erros:         linhas contendo indicação de erro/divergência.
        avisos:        linhas contendo indicação de aviso.
        linhas_brutas: todo o conteúdo do arquivo, linha a linha.
    """

    convergiu: Optional[bool] = None
    erros: List[str] = field(default_factory=list)
    avisos: List[str] = field(default_factory=list)
    linhas_brutas: List[str] = field(default_factory=list)


class LeitorRelatorio:
    """Leitor de arquivos de relatório (.rela) e log (.log) do ANATEM.

    Varre o texto por palavras-chave conhecidas para inferir sucesso/falha.
    Não substitui a leitura manual do relatório completo em casos de dúvida.
    """

    _PALAVRAS_ERRO = ["ERRO", "DIVERG", "FALHA", "NAO CONVERGIU", "NÃO CONVERGIU"]
    _PALAVRAS_AVISO = ["AVISO", "ATENCAO", "ATENÇÃO"]
    _PALAVRAS_SUCESSO = [
        "CONVERGIU",
        "FIM NORMAL",
        "EXECUCAO CONCLUIDA",
        "EXECUÇÃO CONCLUÍDA",
    ]

    @staticmethod
    def ler(caminho: Union[str, Path]) -> ResultadoExecucao:
        """Lê e resume um arquivo .rela/.log.

        Args:
            caminho: caminho do arquivo.

        Returns:
            ResultadoExecucao com status de convergência, erros e avisos.
        """
        caminho = Path(caminho)
        texto = caminho.read_text(encoding="latin-1", errors="replace")
        linhas = texto.splitlines()

        erros: List[str] = []
        avisos: List[str] = []
        teve_sucesso = False
        teve_erro = False

        for linha in linhas:
            up = linha.upper()
            if any(p in up for p in LeitorRelatorio._PALAVRAS_ERRO):
                erros.append(linha.strip())
                teve_erro = True
            elif any(p in up for p in LeitorRelatorio._PALAVRAS_AVISO):
                avisos.append(linha.strip())
            if any(p in up for p in LeitorRelatorio._PALAVRAS_SUCESSO):
                teve_sucesso = True

        if teve_erro:
            convergiu = False
        elif teve_sucesso:
            convergiu = True
        else:
            convergiu = None

        return ResultadoExecucao(
            convergiu=convergiu, erros=erros, avisos=avisos, linhas_brutas=linhas
        )
