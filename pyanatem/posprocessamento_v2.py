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
    """Leitor do arquivo .PLT binário do ANATEM (v1.4.1)."""

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

            # Pular espaços
            f.read(4)

            # Ler nome do arquivo (até 60 bytes)
            nome_arq_raw = f.read(60)
            resultado.titulo_caso = nome_arq_raw.decode("latin-1", errors="ignore").rstrip("\x00")

            # Ler estrutura de header (ainda em engenharia reversa)
            # Por enquanto, ler raw bytes até encontrar início de dados numéricos
            header_resto = f.read(100)

            # Rewind e estratégia: ler blocos sequenciais
            # Formato ainda sob investigação; por ora, marcar como arquivo lido
            resultado.tempo_global = [0.0]  # Placeholder

        return resultado

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
