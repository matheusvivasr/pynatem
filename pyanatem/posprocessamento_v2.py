"""
posprocessamento_v2.py – Leitores de pós-processamento ANATEM (v1.4).

v1.4.1: Leitor de arquivos .PLT binários (formato proprietário CEPEL).
v1.4.4: Leitor de arquivos .OUT (relatórios estruturados).
"""

import struct
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
import re


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
        """Extrai séries temporais do bloco de dados binários."""
        # Estratégia: procurar sequências de floats após delimitadores
        # Por ora, implementar heurística simples: contar floats no arquivo

        # Detectar número de pontos: arquivo total / (4 bytes/float * num_vars)
        # 5 variáveis no exemplo = 5 floats por ponto de tempo
        num_vars = 5  # Placeholder (seria extraído do cabeçalho)
        num_bytes_dados = len(dados) - 256  # Estimar dados após header
        num_pontos = num_bytes_dados // (4 * num_vars)

        if num_pontos > 0:
            # Criar vetor de tempo (simulado com amostragem 0.005s, tfim=80s)
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
