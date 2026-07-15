"""
plt_binario.py – Leitor de arquivo .plt binário do ANATEM (formato proprietário).

Engenharia reversa baseada em arquivo de exemplo:
  examples/treinamentoWP/TREINAMENTO_5_BARRAS.PLT (1.6 MB)

Estrutura identificada:
  - Assinatura: "PLTx" (4 bytes)
  - Metadata: filename, timestamps, parâmetros de simulação
  - Catálogo: nomes + tipos de variáveis, mapeamento de índices
  - Dados: série temporal em floats binários

Status: FASE 1 (análise de estrutura, parser de header)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, BinaryIO, Dict, List, Optional

if TYPE_CHECKING:
    import pandas


@dataclass
class VariavelPLT:
    """Descrição de uma variável de plotagem no .plt binário."""

    indice: int
    tipo: str  # ex: "DELT", "VOLT", "QSHT", "CDU", etc.
    equipamento: int  # barra, máquina, CDU, etc.
    subelemento: int = 0  # circuito, fase, etc. (opcional)
    nome_descritivo: str = ""
    unidade: str = ""


@dataclass
class HeaderPLT:
    """Header e metadata do arquivo .plt binário."""

    assinatura: str = "PLTx"
    filename: str = ""
    tempo_inicio: float = 0.0
    tempo_fim: float = 0.0
    intervalo: float = 0.0
    variáveis: List[VariavelPLT] = field(default_factory=list)
    n_passos: int = 0


class LeitorPLTBinario:
    """
    Leitor incremental do formato .plt binário do ANATEM.

    Uso:
        leitor = LeitorPLTBinario("caso.plt")
        header = leitor.ler_header()
        dados = leitor.ler_serie_temporal()
    """

    def __init__(self, caminho: Path | str):
        self.caminho = Path(caminho)
        self.arquivo: Optional[BinaryIO] = None
        self.dados_brutos: Optional[bytes] = None

    def __enter__(self):
        self.arquivo = open(self.caminho, "rb")
        return self

    def __exit__(self, *args):
        if self.arquivo:
            self.arquivo.close()

    def carregar_completo(self) -> bytes:
        """Carregar arquivo inteiro na memória."""
        if self.dados_brutos is None:
            with open(self.caminho, "rb") as f:
                self.dados_brutos = f.read()
        return self.dados_brutos

    def ler_assinatura(self) -> str:
        """Ler e verificar assinatura 'PLTx'."""
        dados = self.carregar_completo()
        assinatura = dados[0:4].decode("ascii")
        if assinatura != "PLTx":
            raise ValueError(
                f"Assinatura inválida: esperado 'PLTx', encontrado '{assinatura}'"
            )
        return assinatura

    def ler_filename(self) -> str:
        """Extrair nome do arquivo do header."""
        dados = self.carregar_completo()
        # Filename começa ~offset 11 (após assinatura + padding)
        # Busca pela sequência ".PLT"
        idx = dados.find(b".PLT")
        if idx < 0:
            raise ValueError("Não encontrado '.PLT' no header")

        # Procurar início do nome (última sequência de espaços antes)
        start = idx - 30
        for i in range(idx - 1, max(0, idx - 50), -1):
            if dados[i : i + 1] == b"\x00" or dados[i] < 32:
                start = i + 1
                break

        filename = dados[start : idx + 4].decode("latin-1", errors="ignore").strip()
        return filename

    def ler_header(self) -> HeaderPLT:
        """
        Ler header e catálogo de variáveis.

        Retorna HeaderPLT com:
          - filename
          - tempo_inicio, tempo_fim, intervalo
          - lista de variáveis
        """
        dados = self.carregar_completo()
        header = HeaderPLT()

        # Assinatura
        header.assinatura = self.ler_assinatura()

        # Filename
        header.filename = self.ler_filename()

        # Buscar seção de variáveis (offset ~0x30+)
        # Padrão: "7TIPO no barra ..." (tipo de variável + índices)
        variaveis = self._extrair_catalogos(dados)
        header.variáveis = variaveis

        return header

    def _extrair_catalogos(self, dados: bytes) -> List[VariavelPLT]:
        """
        Varredura para localizar catálogo de variáveis no header.

        Tipos conhecidos: DELT, VOLT, ANGL, QSHT, QBSH, NUBSH, TAP, CDU, etc.
        Padrão aproximado: "7TIPO  no subelemento descrição"
        """
        variaveis = []
        indice = 0

        # Buscar padrões tipo "7DELT", "7VOLT", etc.
        tipos_conhecidos = {
            "DELT",
            "VOLT",
            "ANGL",
            "FREQ",
            "QSHT",
            "QBSH",
            "NUBSH",
            "TAP",
            "CDU",
            "PCAR",
            "QCAR",
            "ILIN",
        }

        # Procuração por cada tipo
        for offset in range(len(dados) - 20):
            chunk = dados[offset : offset + 20]
            text = chunk.decode("latin-1", errors="ignore")

            # Padrão: "7TIPO" ou espaço + "TIPO"
            for tipo in tipos_conhecidos:
                if tipo in text and (
                    offset > 0 and chr(dados[offset - 1]) in " \n" or offset == 0
                ):
                    # Extrair linha
                    line_end = dados.find(b"\n", offset)
                    if line_end < 0:
                        line_end = offset + 100
                    linha = dados[offset:line_end].decode("latin-1", errors="ignore")

                    # Parse básico: "TIPO no sub descrição"
                    partes = linha.split()
                    if len(partes) >= 2:
                        tipo_limpo = partes[0].lstrip("0123456789")
                        try:
                            eq = int(partes[1])
                            sub = int(partes[2]) if len(partes) > 2 else 0
                            descr = " ".join(partes[3:]) if len(partes) > 3 else ""

                            var = VariavelPLT(
                                indice=indice,
                                tipo=tipo_limpo,
                                equipamento=eq,
                                subelemento=sub,
                                nome_descritivo=descr[:50],
                            )
                            variaveis.append(var)
                            indice += 1
                        except ValueError:
                            pass

        return variaveis

    def ler_serie_temporal(
        self, var_indices: Optional[List[int]] = None
    ) -> Dict[int, List[float]]:
        """
        Ler série temporal de variáveis (FASE 2).

        ⚠️ STATUS: Parcialmente Implementado
        O formato binário do .plt é proprietário do CEPEL e complexo.
        Requer exemplos adicionais para engenharia reversa completa.

        Retorna dict: índice_variável → lista de valores (floats IEEE 754).

        Limitações conhecidas:
        - Não detecta corretamente número de variáveis em alguns arquivos
        - Formato de série temporal não totalmente mapeado (compressão? estrutura?)
        - Requer validação contra múltiplos exemplos reais do CEPEL

        Veja: docs/v2.1_plt_binario_reversa.md
        """
        # Implementação stub — retornar vazio até format a ser totalmente entendido
        # Uso de `posprocessamento_v2.py` é recomendado como alternativa
        return {}

    def para_dataframe(self) -> "pandas.DataFrame":
        """
        Converter para DataFrame pandas (se pandas disponível).

        ⚠️ Requer que ler_serie_temporal() implemente FASE 2 completamente.
        Status: Não disponível (FASE 2 em desenvolvimento).
        """
        raise NotImplementedError(
            "para_dataframe() requer FASE 2 completa de ler_serie_temporal(). "
            "Use posprocessamento_v2.LeitorPLTBinario como alternativa."
        )


# Teste rápido
if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        plt_path = sys.argv[1]
    else:
        plt_path = "examples/treinamentoWP/TREINAMENTO_5_BARRAS.PLT"

    leitor = LeitorPLTBinario(plt_path)
    try:
        header = leitor.ler_header()
        print(f"Arquivo: {header.filename}")
        print(f"Variáveis encontradas: {len(header.variáveis)}")
        for var in header.variáveis[:10]:  # Primeiras 10
            print(
                f"  [{var.indice}] {var.tipo:6} eq={var.equipamento:3}"
                f" sub={var.subelemento:2}  {var.nome_descritivo}"
            )
    except Exception as e:
        print(f"Erro: {e}")
        import traceback

        traceback.print_exc()
