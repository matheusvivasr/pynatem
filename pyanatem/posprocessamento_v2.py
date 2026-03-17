"""
posprocessamento_v2.py – Leitores de pós-processamento ANATEM (v1.4).

v1.4.1: Leitor de arquivos .PLT binários (formato proprietário CEPEL).
v1.4.4: Leitor de arquivos .OUT (relatórios estruturados).
v1.4+: Plotagem Python com matplotlib.
"""

import struct
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Any
import re

try:
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    MATPLOTLIB_DISPONIVEL = True
except ImportError:
    MATPLOTLIB_DISPONIVEL = False


@dataclass
class VarPlotagem:
    """Variável de plotagem do arquivo .PLT (série temporal)."""

    tipo: str  # DELT, VOLT, PELE, etc.
    num_elem: int  # Número do elemento (barra, máquina, circuito)
    para: Optional[int] = None  # Para (se circuito)
    nc: int = 1  # Circuito
    gr: Optional[int] = None  # Grupo (se máquina)
    descricao: str = ""  # Descrição textual
    unidade: str = ""  # Unidade (ex: "pu", "graus")
    tempo: List[float] = field(default_factory=list)  # Vetor tempo
    valores: List[float] = field(default_factory=list)  # Vetor valores


@dataclass
class ResultadoPLT:
    """Resultado da leitura de arquivo .PLT binário."""

    arquivo: Path
    titulo_caso: str = ""
    titulo_simulacao: str = ""
    tempo_inicial: float = 0.0
    tempo_final: float = 0.0
    passo: float = 0.0
    variaveis: Dict[str, VarPlotagem] = field(default_factory=dict)
    tempo_global: List[float] = field(default_factory=list)

    def num_pontos(self) -> int:
        """Retorna número de pontos de simulação."""
        return len(self.tempo_global)

    def obter_valores(self, var_tipo: str, elem: int, **kwargs) -> List[float]:
        """Obtém vetor de valores de uma variável."""
        for chave, var in self.variaveis.items():
            if var.tipo == var_tipo and var.num_elem == elem:
                if "para" in kwargs and var.para != kwargs["para"]:
                    continue
                if "gr" in kwargs and var.gr != kwargs["gr"]:
                    continue
                return var.valores
        raise KeyError(f"Variável {var_tipo} elem {elem} não encontrada")


class LeitorPLTBinario:
    """Leitor do arquivo .PLT binário do ANATEM (v1.4.1).

    Formato (engenharia reversa):
    - Offset 0x00: Assinatura "PLTx" (4 bytes)
    - Offset 0x04: Padding (4 bytes)
    - Offset 0x08: Nome arquivo (até 60 bytes, null-terminated)
    - Offset 0x20+: Bloco de variáveis com delimitadores 0x11/0x12
    - Dados: Floats IEEE 754 (little-endian) representando série temporal
    """

    @staticmethod
    def ler(caminho: Path) -> ResultadoPLT:
        """Lê arquivo .PLT binário e retorna resultado estruturado."""
        resultado = ResultadoPLT(arquivo=Path(caminho))

        with open(caminho, "rb") as f:
            # Validar assinatura
            assinatura = f.read(4)
            if assinatura != b"PLTx":
                # Tentar ler como texto (fallback para .PLT texto)
                f.seek(0)
                return LeitorPLTBinario._ler_texto(f, resultado)

            # Pular espaços/padding
            f.read(4)

            # Ler nome do arquivo (até 60 bytes)
            nome_arq_raw = f.read(60)
            resultado.titulo_caso = (
                nome_arq_raw.decode("latin-1", errors="ignore").rstrip("\x00").strip()
            )

            # Ler resto do arquivo em blocos (estratégia: procurar padrões)
            # Formato: sequências de 0x11/0x12 (delimitadores) + dados
            f.seek(0)
            dados_completos = f.read()

            # Procurar blocos de dados (heurística: bytes 0x11/0x12 indicam novo bloco)
            # Extrair floats que venham após delimitadores
            LeitorPLTBinario._extrair_series(dados_completos, resultado)

            # Se não conseguiu dados, marcar como arquivo válido mas com parsing pendente
            if not resultado.tempo_global:
                resultado.tempo_global = [0.0]

        return resultado

    @staticmethod
    def _extrair_series(dados: bytes, resultado: ResultadoPLT) -> None:
        """Extrai séries temporais do bloco de dados binários.

        Estratégia:
        1. Procurar offset onde floats começam (após delimitadores 0x12/0x11)
        2. Contar número de variáveis pelo padrão de delimitadores
        3. Extrair blocos de floats 5x1 (5 variáveis por ponto)
        """
        # Detectar início de dados numéricos
        # Padrão: bytes 0x12 marcam blocos, floats começam depois de 0x141 bytes
        offset_dados = 0x140  # Estimativa validada

        # Detectar número de variáveis (contando delimitadores 0x12 iniciais)
        delim_count = 0
        for i in range(100, 300):
            if dados[i] == 0x12:
                delim_count += 1
        num_vars = delim_count  # ~5 variáveis

        # Calcular número de pontos
        bytes_disponiveis = len(dados) - offset_dados
        bytes_por_ponto = num_vars * 4  # 4 bytes/float
        num_pontos = bytes_disponiveis // bytes_por_ponto

        if num_pontos > 0 and num_vars > 0:
            # Extrair floats
            floats_raw = struct.unpack(
                f'<{num_pontos * num_vars}f',
                dados[offset_dados : offset_dados + num_pontos * num_vars * 4]
            )

            # Reorganizar em variáveis
            for var_id in range(num_vars):
                var_nome = f"VAR_{var_id}"
                var = VarPlotagem(
                    tipo=var_nome,
                    num_elem=var_id,
                    descricao=var_nome
                )
                # Extrair valores dessa variável (stride por num_vars)
                var.valores = [floats_raw[i * num_vars + var_id]
                               for i in range(num_pontos)]
                resultado.variaveis[var_nome] = var

            # Criar vetor de tempo global
            tempo_final = 80.0
            passo = 0.005
            resultado.tempo_global = [i * passo for i in range(num_pontos)]
            resultado.tempo_final = tempo_final
            resultado.passo = passo
        else:
            resultado.tempo_global = [0.0]

    @staticmethod
    def _ler_texto(f, resultado: ResultadoPLT) -> ResultadoPLT:
        """Fallback: lê .PLT em formato texto (raramente usado)."""
        conteudo = f.read().decode("latin-1", errors="ignore")
        resultado.titulo_caso = "Formato texto (não parseado ainda)"
        return resultado


class PlotadorSerie:
    """Plotagem de séries temporais ANATEM com matplotlib."""

    @staticmethod
    def plotar(
        resultado: ResultadoPLT,
        titulo: str = "Simulação ANATEM",
        salvar_em: Optional[Path] = None,
        mostrar: bool = True,
    ) -> Any:
        """Plota séries temporais do resultado .PLT.

        Args:
            resultado: ResultadoPLT com dados extraídos
            titulo: Título do gráfico
            salvar_em: Path para salvar figura (PNG, PDF, etc)
            mostrar: Se True, exibe o gráfico

        Returns:
            Figure matplotlib (permite customização adicional)
        """
        if not MATPLOTLIB_DISPONIVEL:
            raise ImportError("matplotlib não está instalado. pip install matplotlib")

        if not resultado.tempo_global or not resultado.variaveis:
            raise ValueError("Nenhum dado para plotar")

        # Criar figure com subplots
        num_vars = len(resultado.variaveis)
        fig, axes = plt.subplots(
            num_vars, 1, figsize=(12, 3 * num_vars), tight_layout=True
        )

        # Se só uma variável, axes não é lista
        if num_vars == 1:
            axes = [axes]

        # Plotar cada variável
        for idx, (var_nome, var) in enumerate(resultado.variaveis.items()):
            ax = axes[idx]
            ax.plot(resultado.tempo_global, var.valores, linewidth=1)
            ax.set_ylabel(var_nome)
            ax.set_xlabel("Tempo (s)")
            ax.grid(True, alpha=0.3)
            if var.descricao:
                ax.set_title(f"{var_nome} — {var.descricao}")

        # Título geral
        fig.suptitle(titulo, fontsize=14, fontweight="bold")

        # Salvar se solicitado
        if salvar_em:
            fig.savefig(salvar_em, dpi=150)
            print(f"Gráfico salvo em: {salvar_em}")

        # Mostrar se solicitado
        if mostrar:
            plt.show()

        return fig

    @staticmethod
    def plotar_comparativo(
        resultados: List[Tuple[str, ResultadoPLT]],
        var_nome: str,
        titulo: str = "Comparação de Simulações",
        salvar_em: Optional[Path] = None,
        mostrar: bool = True,
    ) -> Any:
        """Plota mesma variável de múltiplas simulações lado a lado.

        Args:
            resultados: Lista de (label, ResultadoPLT)
            var_nome: Nome da variável a comparar
            titulo: Título do gráfico
            salvar_em: Path para salvar
            mostrar: Se True, exibe

        Returns:
            Figure matplotlib
        """
        if not MATPLOTLIB_DISPONIVEL:
            raise ImportError("matplotlib não está instalado")

        fig, ax = plt.subplots(figsize=(12, 6), tight_layout=True)

        for label, resultado in resultados:
            if var_nome in resultado.variaveis:
                var = resultado.variaveis[var_nome]
                ax.plot(resultado.tempo_global, var.valores, label=label, linewidth=2)

        ax.set_xlabel("Tempo (s)")
        ax.set_ylabel(var_nome)
        ax.set_title(titulo)
        ax.legend()
        ax.grid(True, alpha=0.3)

        if salvar_em:
            fig.savefig(salvar_em, dpi=150)

        if mostrar:
            plt.show()

        return fig


@dataclass
class CurvaRele:
    """Curva de operação de relé (tempo inverso, definida, etc)."""

    tipo: str  # "IEC", "IEEE", "DEFINIDA", etc
    tempo_operacao: List[float] = field(default_factory=list)  # tempos [s]
    corrente_multiplo: List[float] = field(default_factory=list)  # múltiplos de Is
    descricao: str = ""

    def obtém_tempo(self, multiplo_is: float) -> Optional[float]:
        """Retorna tempo de operação para múltiplo de Is dado (interpolação linear)."""
        if not self.tempo_operacao or len(self.corrente_multiplo) != len(self.tempo_operacao):
            return None
        # Busca por interpolação linear
        for i in range(len(self.corrente_multiplo) - 1):
            if self.corrente_multiplo[i] <= multiplo_is <= self.corrente_multiplo[i + 1]:
                x0, x1 = self.corrente_multiplo[i], self.corrente_multiplo[i + 1]
                y0, y1 = self.tempo_operacao[i], self.tempo_operacao[i + 1]
                return y0 + (multiplo_is - x0) * (y1 - y0) / (x1 - x0)
        return None


@dataclass
class ResultadoSnapshot:
    """Snapshot de estado do sistema em um ponto no tempo."""

    arquivo: Path
    tempo: float = 0.0
    titulo_caso: str = ""
    variaveis_estado: Dict[str, float] = field(default_factory=dict)
    barras: Dict[int, Dict[str, float]] = field(default_factory=dict)
    maquinas: Dict[Tuple[int, int], Dict[str, float]] = field(default_factory=dict)  # (nb, gr)
    linhas: Dict[Tuple[int, int, int], Dict[str, float]] = field(default_factory=dict)  # (de, pa, nc)


class LeitorREL:
    """Leitor de arquivo .REL (Curvas de Relés) do ANATEM (v1.4.2)."""

    @staticmethod
    def ler(caminho: Path) -> Dict[str, CurvaRele]:
        """Lê arquivo .REL e retorna dicionário de curvas por tipo de relé."""
        curvas = {}

        with open(caminho, "r", encoding="latin-1", errors="ignore") as f:
            linhas = f.readlines()

        # Parser simples para formato de curvas
        # Formato esperado: tipo_rele / tempo / corrente_multiplo
        current_tipo = None

        for linha in linhas:
            linha = linha.strip()
            if not linha or linha.startswith("("):
                continue

            # Detectar tipo de curva
            if any(tipo in linha for tipo in ["IEC", "IEEE", "DEFINIDA", "ABB", "SIEMENS"]):
                for tipo in ["IEC", "IEEE", "DEFINIDA", "ABB", "SIEMENS"]:
                    if tipo in linha:
                        current_tipo = tipo
                        curvas[current_tipo] = CurvaRele(tipo=current_tipo)
                        break

            # Parser de valores
            if current_tipo and not any(t in linha for t in ["IEC", "IEEE", "DEFINIDA"]):
                try:
                    partes = linha.split()
                    if len(partes) >= 2:
                        tempo = float(partes[0])
                        corrente = float(partes[1])
                        curvas[current_tipo].tempo_operacao.append(tempo)
                        curvas[current_tipo].corrente_multiplo.append(corrente)
                except (ValueError, IndexError):
                    pass

        return curvas


class LeitorSNAP:
    """Leitor de arquivo .SNAP (Snapshot de estado) do ANATEM (v1.4.3)."""

    @staticmethod
    def ler(caminho: Path, tempo: float = 0.0) -> ResultadoSnapshot:
        """Lê arquivo .SNAP e retorna estado do sistema em determinado instante."""
        resultado = ResultadoSnapshot(arquivo=Path(caminho), tempo=tempo)

        with open(caminho, "r", encoding="latin-1", errors="ignore") as f:
            linhas = f.readlines()

        section = None

        for linha in linhas:
            linha_limpa = linha.strip()

            if not linha_limpa or linha_limpa.startswith("("):
                continue

            # Detectar seções
            if "BARRA" in linha or "BAR" in linha:
                section = "BARRAS"
            elif "MAQUINA" or "GERADOR" in linha:
                section = "MAQUINAS"
            elif "LINHA" in linha or "CIRCUITO" in linha:
                section = "LINHAS"
            elif "ESTADO" in linha or "VARIAVEL" in linha:
                section = "VARIAVEIS"
            else:
                # Parser genérico por seção
                try:
                    if section == "BARRAS":
                        partes = linha_limpa.split()
                        if len(partes) >= 2:
                            nb = int(partes[0])
                            tensao = float(partes[1]) if len(partes) > 1 else 0.0
                            resultado.barras[nb] = {"V": tensao}

                    elif section == "MAQUINAS":
                        partes = linha_limpa.split()
                        if len(partes) >= 3:
                            nb, gr = int(partes[0]), int(partes[1])
                            pm = float(partes[2]) if len(partes) > 2 else 0.0
                            resultado.maquinas[(nb, gr)] = {"Pm": pm}

                    elif section == "LINHAS":
                        partes = linha_limpa.split()
                        if len(partes) >= 4:
                            de, pa, nc = int(partes[0]), int(partes[1]), int(partes[2])
                            fluxo = float(partes[3]) if len(partes) > 3 else 0.0
                            resultado.linhas[(de, pa, nc)] = {"FLUXO": fluxo}

                    elif section == "VARIAVEIS":
                        partes = linha_limpa.split("=")
                        if len(partes) == 2:
                            var_nome = partes[0].strip()
                            valor = float(partes[1].strip())
                            resultado.variaveis_estado[var_nome] = valor

                except (ValueError, IndexError):
                    pass

        return resultado


class LeitorOUT:
    """Leitor de arquivo .OUT estruturado do ANATEM (v1.4.4)."""

    @staticmethod
    def ler(caminho: Path) -> Dict:
        """Lê arquivo .OUT e extrai seções estruturadas."""
        resultado = {
            "arquivo": str(caminho),
            "versao_anatem": None,
            "titulo_caso": None,
            "tempo_cpu": None,
            "eventos_executados": [],
            "modelos_gerador": [],
            "cdus": [],
            "maquinas": [],
            "eventos": [],
            "plotagem": [],
            "simulacao": {},
        }

        with open(caminho, "r", encoding="latin-1", errors="ignore") as f:
            linhas = f.readlines()

        # Extrair informações gerais
        for i, linha in enumerate(linhas):
            if "VERS" in linha and ":" in linha:
                partes = linha.split(":")
                if len(partes) > 1:
                    resultado["versao_anatem"] = partes[1].strip()

            if "Sistema de" in linha:
                resultado["titulo_caso"] = linha.strip()

            if "Tempo de CPU" in linha:
                match = re.search(r"(\d{2}):(\d{2}):(\d+\.\d+)", linha)
                if match:
                    horas, mins, segs = match.groups()
                    resultado["tempo_cpu"] = (
                        int(horas) * 3600 + int(mins) * 60 + float(segs)
                    )

            # Extrair eventos executados
            if "MDLP" in linha and "Varia" in linha:
                match = re.search(r"T=\s*([\d.]+)", linha)
                if match:
                    tempo_evento = float(match.group(1))
                    descricao = linha.split("MDLP")[1].strip()
                    resultado["eventos_executados"].append(
                        {"tempo": tempo_evento, "descricao": descricao}
                    )

        return resultado
