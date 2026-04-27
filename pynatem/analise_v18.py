"""
analise_v18.py – Modos de Análise do ANATEM (v1.8).

v1.8.1: Análise de Contingência (N-1, §7.3)
v1.8.2: Multi-infeed (§36-37, EAMI/EAIF)
v1.8.3: Séries Temporais (TIME/DSTO)
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict
from pathlib import Path
from enum import Enum


# ============================================================================
# v1.8.1 — ANÁLISE DE CONTINGÊNCIA (§7.3)
# ============================================================================

@dataclass
class Contingencia:
    """Uma contingência individual para análise N-1 (§7.3.2).

    Estrutura:
      IDENT: Identificador (1-12 caracteres) — usado em nomes de arquivos
      TITULO: Título da contingência (14-92 caracteres)
      DEVT: Lista de eventos que definem a contingência
    """
    ident: str  # Identificador (1-12 chars)
    titulo: str  # Título (14-92 chars)
    eventos: List[str] = field(default_factory=list)  # Linhas DEVT

    def validar(self) -> tuple[bool, List[str]]:
        """Valida contingência conforme §7.3.2."""
        erros = []
        if not self.ident or len(self.ident) > 12:
            erros.append(f"IDENT deve ter 1-12 caracteres (tem {len(self.ident)})")
        if not self.titulo or len(self.titulo) > 79:
            erros.append(f"TITULO deve ter 1-79 caracteres (tem {len(self.titulo)})")
        if not self.eventos:
            erros.append("Contingência deve ter ao menos 1 evento DEVT")
        return len(erros) == 0, erros

    def serializar_contingencia(self) -> str:
        """Serializa para formato arquivo de contingências (§7.3.2)."""
        linhas = []
        # Linha A: IDENT e TITULO
        linha_ident = self.ident.ljust(12)
        linha_titulo = self.titulo[:79].ljust(79)
        linhas.append(f"{linha_ident}{linha_titulo}\n")

        # Linhas B: Eventos DEVT
        for evento in self.eventos:
            linhas.append(f"{evento}\n")

        # Linha C: FIMCTG
        linhas.append("FIMCTG\n")

        return "".join(linhas)


@dataclass
class AnalisadorContingencia:
    """Gerenciador de análise de contingências (§7.3).

    Coordena execução de casos N-1:
    - Caso base + lista de contingências → Múltiplos casos ANATEM
    - Opção de paralelização (§7.3.1 item 7)
    - Geração automática de arquivos .stb, .out, .plt
    """
    caso_base_path: Path  # Arquivo .stb base
    historico_path: Path  # Arquivo histórico ANAREDE
    caso_numero: int  # Número do caso no histórico
    contingencias: List[Contingencia] = field(default_factory=list)
    identificador: str = "analise_ctg"  # Identificador da análise
    processos_paralelos: int = 1  # 1=sequencial, N=paralelo

    def adicionar_contingencia(self, ctg: Contingencia) -> "AnalisadorContingencia":
        """Adiciona contingência à análise."""
        valido, _ = ctg.validar()
        if valido:
            self.contingencias.append(ctg)
        return self

    def gerar_arquivo_contingencias(self) -> str:
        """Gera conteúdo arquivo de contingências (§7.3.2).

        Formato:
          CONTINGENCIA
          [contingências com IDENT, TITULO, DEVT, FIMCTG]
          FIM
        """
        linhas = ["CONTINGENCIA\n"]
        for ctg in self.contingencias:
            linhas.append(ctg.serializar_contingencia())
        linhas.append("FIM\n")
        return "".join(linhas)

    def validar_configuracao(self) -> tuple[bool, List[str]]:
        """Valida se análise pode ser executada (§7.3.1)."""
        erros = []
        if not self.caso_base_path.exists():
            erros.append(f"Caso base não encontrado: {self.caso_base_path}")
        if not self.historico_path.exists():
            erros.append(f"Histórico não encontrado: {self.historico_path}")
        if self.caso_numero <= 0:
            erros.append(f"Número do caso inválido: {self.caso_numero}")
        if not self.contingencias:
            erros.append("Nenhuma contingência definida")
        if self.processos_paralelos < 1:
            erros.append(f"Processos paralelos deve ser >= 1 (tem {self.processos_paralelos})")
        for ctg in self.contingencias:
            valido, ctg_erros = ctg.validar()
            if not valido:
                erros.extend([f"Contingência {ctg.ident}: {e}" for e in ctg_erros])
        return len(erros) == 0, erros

    def resumo_analise(self) -> str:
        """Gera resumo da análise de contingência."""
        return f"""
Análise de Contingência (§7.3):
  Caso Base: {self.caso_base_path.name}
  Histórico: {self.historico_path.name}
  Número do Caso: {self.caso_numero}
  Identificador: {self.identificador}

  Contingências: {len(self.contingencias)}
  Paralelização: {self.processos_paralelos} processo(s)

  Subdiretório: {self.identificador}/
  Arquivos: {self.identificador}_*.stb (dados)
            {self.identificador}_*.out (resultados)
            {self.identificador}_*.plt (plotagem)
"""


# ============================================================================
# v1.8.2 — MULTI-INFEED (§36-37, EAMI/EAIF)
# ============================================================================

class TipoAnaliseMultiInfeed(Enum):
    """Tipos de análise multi-infeed disponíveis (§36-37)."""
    EAMI = "EAMI"  # Cálculo automático MIIF (elos HVDC LCC)
    EAIF = "EAIF"  # Interação fontes shunt controladas
    MANUAL = "MANUAL"  # Especificação manual via DMIF


@dataclass
class DefinicaoBarraMultiInfeed:
    """Definição de barra para análise MIIF (§36.5, código DMIF).

    DMIF permite selecionar barras CA para cálculo automático de índices.
    """
    nb: int  # Número da barra

    def serializar_dmif(self) -> str:
        """Serializa em formato DMIF."""
        return f"DMIF\n( Nb )\n{self.nb}\n"


@dataclass
class AnalisadorMultiInfeed:
    """Análise Multi-infeed com cálculo automático (§36-37).

    Tipos:
    - EAMI: Cálculo automático de MIIF para elos HVDC LCC
    - EAIF: Análise interação fontes shunt (DFNT)

    Saída: Índices em OUT ou CSV (MIIF)
    """
    tipo: TipoAnaliseMultiInfeed
    barras: List[int] = field(default_factory=list)  # DMIF barras
    peco_enabled: bool = True  # Opção PECO (§7.3 item 8)
    exportar_csv: bool = False  # Exportar resultados em CSV

    def adicionar_barra(self, nb: int) -> "AnalisadorMultiInfeed":
        """Adiciona barra para análise manual (DMIF)."""
        if nb not in self.barras:
            self.barras.append(nb)
        return self

    def gerar_blocos_dmif(self) -> str:
        """Gera bloco DMIF para análise manual (§36.5)."""
        if not self.barras or self.tipo == TipoAnaliseMultiInfeed.EAMI:
            return ""  # EAMI automático, não precisa DMIF

        linhas = ["DMIF\n", "( Nb )\n"]
        for nb in sorted(self.barras):
            linhas.append(f"{nb}\n")
        linhas.append("999999\n")
        return "".join(linhas)

    def gerar_bloco_analise(self) -> str:
        """Gera bloco de execução EAMI ou EAIF (§36.4)."""
        if self.tipo == TipoAnaliseMultiInfeed.EAMI:
            return "EAMI\n(\nFIM\n"
        elif self.tipo == TipoAnaliseMultiInfeed.EAIF:
            return "EAIF\n(\nFIM\n"
        return ""

    def resumo_analise(self) -> str:
        """Gera resumo da análise multi-infeed."""
        tipo_nome = {
            TipoAnaliseMultiInfeed.EAMI: "Cálculo Automático MIIF (elos HVDC LCC)",
            TipoAnaliseMultiInfeed.EAIF: "Interação Fontes Shunt (DFNT)",
            TipoAnaliseMultiInfeed.MANUAL: "Definição Manual (DMIF)",
        }
        return f"""
Análise Multi-infeed (§36-37):
  Tipo: {tipo_nome[self.tipo]}
  Barras: {len(self.barras)} {'(automático HVDC)' if self.tipo == TipoAnaliseMultiInfeed.EAMI else ''}
  Opção PECO: {'Habilitada' if self.peco_enabled else 'Desabilitada'}
  Exportar CSV: {'Sim (MIIF)' if self.exportar_csv else 'Não'}

  Índices Calculados:
    • SCR (Short-Circuit Ratio)
    • MIIF (Multi-Infeed Interaction Factor)
    • Robustez sistema CA
    • Grau interação entre fontes
"""


# ============================================================================
# v1.8.3 — SÉRIES TEMPORAIS (§46.72 TIME, §46.60 DSTO)
# ============================================================================

@dataclass
class Timestamp:
    """Timestamp do caso (§46.72, código TIME).

    Formatos suportados:
      - EPOCH: Inteiro Unix (segundos desde 1/1/1970)
      - YYYY/MM/DD HH:MM:SS UTC±HH:MM
      - YYYY/MM/DD HH:MM UTC±HH:MM
      - YYYY/MM/DD (12:00 UTC local)
      - YYYY/MM (Dia 1, 12:00 UTC local)
    """
    ano: int
    mes: int
    dia: int = 1
    hora: int = 12
    minuto: int = 0
    segundo: int = 0
    utc_offset: str = "UTC ±00:00"

    @staticmethod
    def from_epoch(epoch: int) -> "Timestamp":
        """Cria timestamp a partir EPOCH (segundos Unix)."""
        from datetime import datetime
        dt = datetime.utcfromtimestamp(epoch)
        return Timestamp(
            ano=dt.year,
            mes=dt.month,
            dia=dt.day,
            hora=dt.hour,
            minuto=dt.minute,
            segundo=dt.second,
        )

    def validar(self) -> tuple[bool, List[str]]:
        """Valida timestamp."""
        erros = []
        if self.ano < 1970 or self.ano > 2100:
            erros.append(f"Ano inválido: {self.ano} (deve ser 1970-2100)")
        if self.mes < 1 or self.mes > 12:
            erros.append(f"Mês inválido: {self.mes} (deve ser 1-12)")
        if self.dia < 1 or self.dia > 31:
            erros.append(f"Dia inválido: {self.dia} (deve ser 1-31)")
        if self.hora < 0 or self.hora > 23:
            erros.append(f"Hora inválida: {self.hora} (deve ser 0-23)")
        if self.minuto < 0 or self.minuto > 59:
            erros.append(f"Minuto inválido: {self.minuto} (deve ser 0-59)")
        if self.segundo < 0 or self.segundo > 59:
            erros.append(f"Segundo inválido: {self.segundo} (deve ser 0-59)")
        return len(erros) == 0, erros

    def serializar_time(self) -> str:
        """Serializa em formato TIME (§46.72)."""
        return f"TIME\n{self.ano:04d}/{self.mes:02d}/{self.dia:02d} {self.hora:02d}:{self.minuto:02d}:{self.segundo:02d} {self.utc_offset}\n"


@dataclass
class CenarioEstocastico:
    """Definição de cenário estocástico (§46.60, código DSTO).

    Atualmente suporta séries hidrológicas (HIDRO).
    Integração com arquivo USIHID.csv.
    """
    tipo: str = "HIDRO"  # Tipo de estocasticidade
    serie: int = 1  # Número identificador série (coluna SERIE)
    patamar: int = 1  # Identificador patamar (coluna PATAMAR)

    def validar(self) -> tuple[bool, List[str]]:
        """Valida cenário."""
        erros = []
        if self.tipo not in ["HIDRO"]:
            erros.append(f"Tipo estocástico inválido: {self.tipo} (esperado: HIDRO)")
        if self.serie < 1:
            erros.append(f"Série deve ser >= 1 (tem {self.serie})")
        if self.patamar < 1:
            erros.append(f"Patamar deve ser >= 1 (tem {self.patamar})")
        return len(erros) == 0, erros

    def serializar_dsto(self) -> str:
        """Serializa em formato DSTO (§46.60)."""
        return f"DSTO\n({self.tipo})\n{self.serie}\n{self.patamar}\n"


@dataclass
class AnaliseSerieTemporal:
    """Análise com séries temporais (§46.72 TIME, §46.60 DSTO).

    Integra:
    - Timestamp (TIME): Quando ocorre a análise
    - Cenário Estocástico (DSTO): Qual série/patamar hidrológico
    - Bloco SERIET: Leitura de séries externas
    """
    timestamp: Optional[Timestamp] = None
    cenario: Optional[CenarioEstocastico] = None
    arquivo_usihid: Optional[Path] = None  # Arquivo de séries hidrológicas

    def definir_timestamp(self, ts: Timestamp) -> "AnaliseSerieTemporal":
        """Define timestamp da análise."""
        self.timestamp = ts
        return self

    def definir_cenario(self, cen: CenarioEstocastico) -> "AnaliseSerieTemporal":
        """Define cenário estocástico."""
        self.cenario = cen
        return self

    def validar(self) -> tuple[bool, List[str]]:
        """Valida configuração série temporal."""
        erros = []
        if self.timestamp:
            valido, ts_erros = self.timestamp.validar()
            if not valido:
                erros.extend(ts_erros)
        if self.cenario:
            valido, cen_erros = self.cenario.validar()
            if not valido:
                erros.extend(cen_erros)
        if self.arquivo_usihid and not self.arquivo_usihid.exists():
            erros.append(f"Arquivo USIHID não encontrado: {self.arquivo_usihid}")
        return len(erros) == 0, erros

    def gerar_blocos(self) -> str:
        """Gera blocos TIME + DSTO + referência USIHID."""
        linhas = []
        if self.timestamp:
            linhas.append(self.timestamp.serializar_time())
        if self.cenario:
            linhas.append(self.cenario.serializar_dsto())
        if self.arquivo_usihid:
            # DARQ com arquivo USIHID
            linhas.append(f"DARQ\nHIS\n{self.arquivo_usihid}\n")
        return "".join(linhas)

    def resumo_analise(self) -> str:
        """Gera resumo da análise série temporal."""
        return f"""
Análise com Séries Temporais (§46.72, §46.60):
  Timestamp: {f'{self.timestamp.ano:04d}/{self.timestamp.mes:02d}/{self.timestamp.dia:02d} {self.timestamp.hora:02d}:{self.timestamp.minuto:02d}' if self.timestamp else 'Não definido'}
  Cenário: {f'{self.cenario.tipo} série={self.cenario.serie} patamar={self.cenario.patamar}' if self.cenario else 'Não definido'}
  Arquivo USIHID: {self.arquivo_usihid.name if self.arquivo_usihid else 'Não definido'}

  Integração Bloco SERIET:
    - Leitura automática de séries via TIME/DSTO
    - Suporte a USIHID.csv (série hidrológica)
"""


if __name__ == "__main__":
    # Exemplo v1.8.1: Contingência
    print("=" * 70)
    print("v1.8.1: Análise de Contingência (N-1, §7.3)")
    print("=" * 70)

    analisador_ctg = AnalisadorContingencia(
        caso_base_path=Path("caso_base.stb"),
        historico_path=Path("hist_2026.his"),
        caso_numero=1,
        identificador="ctg_2026_07",
        processos_paralelos=4,
    )

    # Adicionar contingências
    ctg1 = Contingencia(
        ident="DES_LIN_001",
        titulo="Desligamento de LT 230kV Rio-Brasilia",
        eventos=[
            "0.1  3  1  2  1  0.0  0.0  0.0",  # Exemplo evento DEVT simplificado
        ],
    )

    ctg2 = Contingencia(
        ident="DES_LIN_002",
        titulo="Desligamento de LT 230kV Brasilia-Sul",
        eventos=[
            "0.1  3  1  3  1  0.0  0.0  0.0",
        ],
    )

    analisador_ctg.adicionar_contingencia(ctg1)
    analisador_ctg.adicionar_contingencia(ctg2)

    print(analisador_ctg.resumo_analise())
    print("\nArquivo de Contingências Gerado:")
    print(analisador_ctg.gerar_arquivo_contingencias())

    # Exemplo v1.8.2: Multi-infeed
    print("\n" + "=" * 70)
    print("v1.8.2: Análise Multi-infeed (§36-37)")
    print("=" * 70)

    analisador_mi = AnalisadorMultiInfeed(
        tipo=TipoAnaliseMultiInfeed.EAMI,
        peco_enabled=True,
        exportar_csv=True,
    )

    print(analisador_mi.resumo_analise())
    print("Bloco de Execução:")
    print(analisador_mi.gerar_bloco_analise())

    # Exemplo v1.8.3: Séries Temporais
    print("\n" + "=" * 70)
    print("v1.8.3: Análise com Séries Temporais (§46.72, §46.60)")
    print("=" * 70)

    ts = Timestamp(ano=2026, mes=7, dia=10, hora=14, minuto=30)
    cenario = CenarioEstocastico(tipo="HIDRO", serie=1984, patamar=1)

    analise_st = AnaliseSerieTemporal(
        timestamp=ts,
        cenario=cenario,
        arquivo_usihid=Path("usihid.csv"),
    )

    print(analise_st.resumo_analise())
    print("\nBlocos Gerados:")
    print(analise_st.gerar_blocos())
