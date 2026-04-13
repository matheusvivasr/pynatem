"""
dsa_v110.py – Controle Dinâmico Adaptativo (v1.10).

v1.10.1: Avaliação de Segurança Dinâmica (DSA, §47.101 RSEG)
v1.10.2: Recomendações Preventivas (Ações de Controle)
v1.10.3: Integração com Snapshots (Multi-caso)

Referência: Manual ANATEM 12.10 §47.101 (RSEG), §7.4 (Critérios)
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Tuple
from enum import Enum
from pathlib import Path


# ============================================================================
# v1.10.1 — AVALIAÇÃO DE SEGURANÇA DINÂMICA (DSA, §47.101 RSEG)
# ============================================================================

class TipoElementoSeguranca(Enum):
    """Tipos de elementos monitorados em DSA (§47.101)."""
    CIRCUITO = "CIRCUITO"  # Carregamento (% emergência)
    BARRA = "BARRA"  # Tensão (% nominal)
    GERACAO = "GERACAO"  # Geração reativa (faixa em DBAR)


class StatusSeguranca(Enum):
    """Status de segurança do elemento."""
    SEGURO = "SEGURO"  # Dentro dos limites
    ALERTA = "ALERTA"  # Próximo do limite
    VIOLACAO = "VIOLACAO"  # Excedeu limite de emergência
    CRITICO = "CRITICO"  # Severidade alta


@dataclass
class ElementoSeguranca:
    """Elemento monitorado na Avaliação DSA (§47.101).

    Representa um circuito, barra ou barra de geração que será
    monitorado contra limites de emergência do Anarede.
    """
    tipo: TipoElementoSeguranca
    identificacao: str  # Nome do elemento
    limite_emergencia: float  # Limite de emergência (DLIN/DBAR)
    limite_alerta: float = None  # Limite de alerta (opcional, 90% emergência)
    valor_operacional: float = 0.0  # Valor em regime permanente

    def __post_init__(self):
        if self.limite_alerta is None:
            self.limite_alerta = self.limite_emergencia * 0.90

    def validar(self) -> tuple[bool, List[str]]:
        """Valida elemento de segurança."""
        erros = []
        if not self.identificacao:
            erros.append("Identificação não pode estar vazia")
        if self.limite_emergencia <= 0:
            erros.append(f"Limite emergência deve ser > 0 (tem {self.limite_emergencia})")
        if self.limite_alerta < 0 or self.limite_alerta > self.limite_emergencia:
            erros.append(f"Limite alerta deve estar entre 0 e {self.limite_emergencia}")
        return len(erros) == 0, erros


@dataclass
class AvaliadorDSA:
    """Avaliador de Segurança Dinâmica (Dynamic Security Assessment).

    Monitora critérios de segurança (tensão, carregamento, reativo)
    contra limites de emergência definidos no Anarede.
    Referência: §47.101 (RSEG)
    """
    elementos: List[ElementoSeguranca] = field(default_factory=list)
    nome_caso: str = "Caso_DSA"
    tempo_simulacao: float = 0.0  # Instante de avaliação (segundos)

    def adicionar_elemento(self, elemento: ElementoSeguranca) -> "AvaliadorDSA":
        """Adiciona elemento a monitorar."""
        self.elementos.append(elemento)
        return self

    def avaliar_seguranca(self, valor_observado: float, elemento_id: int) \
            -> Tuple[StatusSeguranca, str, float]:
        """Avalia segurança de um elemento em relação aos limites.

        Args:
            valor_observado: Valor medido durante simulação
            elemento_id: Índice do elemento

        Retorna:
            (status, mensagem, margem_seguranca)
        """
        if elemento_id < 0 or elemento_id >= len(self.elementos):
            return StatusSeguranca.CRITICO, "Elemento não encontrado", 0.0

        elem = self.elementos[elemento_id]
        margem = elem.limite_emergencia - valor_observado

        if valor_observado > elem.limite_emergencia:
            return StatusSeguranca.VIOLACAO, \
                f"{elem.identificacao}: {valor_observado:.2f} > limite {elem.limite_emergencia:.2f}", \
                margem

        elif valor_observado > elem.limite_alerta:
            return StatusSeguranca.ALERTA, \
                f"{elem.identificacao}: {valor_observado:.2f} > alerta {elem.limite_alerta:.2f}", \
                margem

        else:
            return StatusSeguranca.SEGURO, \
                f"{elem.identificacao}: {valor_observado:.2f} < limite {elem.limite_emergencia:.2f}", \
                margem

    def avaliar_sistema_completo(self, valores: List[float]) -> Dict[int, Tuple]:
        """Avalia segurança de todos os elementos.

        Args:
            valores: Lista de valores observados [V1, V2, ..., Vn]

        Retorna:
            Dict {elemento_id: (status, mensagem, margem)}
        """
        resultados = {}
        for i, valor in enumerate(valores):
            if i < len(self.elementos):
                resultados[i] = self.avaliar_seguranca(valor, i)
        return resultados

    def gerar_relatorio_rseg(self) -> str:
        """Gera relatório de Avaliação de Segurança Dinâmica (RSEG).

        Formato: Listagem de elementos com status e margens.
        """
        linhas = [
            "=" * 80,
            f"RELATÓRIO DE AVALIAÇÃO DE SEGURANÇA DINÂMICA (DSA)",
            f"Caso: {self.nome_caso}",
            f"Tempo de simulação: {self.tempo_simulacao:.2f}s",
            "=" * 80,
            "",
            "Elementos Monitorados:",
            "-" * 80,
        ]

        for i, elem in enumerate(self.elementos):
            tipo_str = elem.tipo.value
            linhas.append(
                f"[{i}] {tipo_str:<10} {elem.identificacao:<30} "
                f"Limite: {elem.limite_emergencia:>10.2f} "
                f"Alerta: {elem.limite_alerta:>10.2f}"
            )

        return "\n".join(linhas)


# ============================================================================
# v1.10.2 — RECOMENDAÇÕES PREVENTIVAS (Ações de Controle)
# ============================================================================

class TipoAcaoPreventiva(Enum):
    """Tipos de ações preventivas recomendadas."""
    REDUCAO_CARGA = "REDUCAO_CARGA"  # Reduzir carga em barra
    AUMENTO_GERACAO = "AUMENTO_GERACAO"  # Aumentar geração
    DESLIGAMENTO_CIRCUITO = "DESLIGAMENTO_CIRCUITO"  # Desligar contingência
    REJEICAO_FREQUENCIA = "REJEICAO_FREQUENCIA"  # ERAC: relé subfrequência
    CONTROLE_TENSAO = "CONTROLE_TENSAO"  # Aumentar suporte tensão
    ATUACAO_HVDC = "ATUACAO_HVDC"  # Controle HVDC


@dataclass
class AcaoPreventiva:
    """Ação preventiva recomendada pelo algoritmo DSA.

    Recomendação de controle para manter segurança dinâmica.
    """
    tipo: TipoAcaoPreventiva
    descricao: str  # Descrição detalhada da ação
    elemento_afetado: str  # Qual elemento esta ação afeta
    magnitude: float = 0.0  # Magnitude da ação (% carga, MW, etc)
    tempo_recomendado: float = 0.0  # Tempo ideal da ação (s)
    criticidade: int = 1  # 1=recomendação, 2=desejável, 3=crítica

    def descrever_criacao(self) -> str:
        """Descrição legível da ação."""
        criticalidade_str = ["Recomendação", "Desejável", "Crítica"][self.criticidade - 1]
        return (
            f"{self.tipo.value}: {self.descricao}\n"
            f"  Afeta: {self.elemento_afetado}\n"
            f"  Magnitude: {self.magnitude:.1f}\n"
            f"  Tempo recomendado: {self.tempo_recomendado:.2f}s\n"
            f"  Criticidade: {criticalidade_str}"
        )


@dataclass
class RecomendadorDSA:
    """Recomendador de Ações Preventivas baseado em DSA.

    Analisa violações e gera recomendações de controle para
    manter segurança dinâmica do sistema.
    """
    acoes: List[AcaoPreventiva] = field(default_factory=list)
    margem_seguranca_minima: float = 10.0  # % de margem desejada

    def adicionar_acao(self, acao: AcaoPreventiva) -> "RecomendadorDSA":
        """Adiciona ação preventiva ao conjunto."""
        self.acoes.append(acao)
        return self

    def recomendar_acoes(self, violacoes: Dict[int, Tuple]) -> List[AcaoPreventiva]:
        """Recomenda ações baseado em violações de segurança.

        Args:
            violacoes: Dict {elemento_id: (status, mensagem, margem)}

        Retorna:
            Lista de ações preventivas recomendadas
        """
        recomendacoes = []

        # Analisar violações
        for elem_id, (status, msg, margem) in violacoes.items():
            if status == StatusSeguranca.VIOLACAO:
                # Violação: recomendar ação crítica
                acao_critica = AcaoPreventiva(
                    tipo=TipoAcaoPreventiva.REDUCAO_CARGA,
                    descricao=f"Violação detectada: {msg}",
                    elemento_afetado=f"Elemento {elem_id}",
                    magnitude=abs(margem) * 1.2,  # 20% acima da margem
                    criticidade=3,  # Crítica
                )
                recomendacoes.append(acao_critica)

            elif status == StatusSeguranca.ALERTA:
                # Alerta: recomendar ação desejável
                acao_desejavel = AcaoPreventiva(
                    tipo=TipoAcaoPreventiva.AUMENTO_GERACAO,
                    descricao=f"Alerta de segurança: {msg}",
                    elemento_afetado=f"Elemento {elem_id}",
                    magnitude=abs(margem) * 0.5,  # Metade da margem
                    criticidade=2,  # Desejável
                )
                recomendacoes.append(acao_desejavel)

        return recomendacoes

    def gerar_relatorio_recomendacoes(self, recomendacoes: List[AcaoPreventiva]) -> str:
        """Gera relatório de recomendações."""
        if not recomendacoes:
            return "Nenhuma ação preventiva recomendada — Sistema seguro."

        linhas = [
            "=" * 80,
            "RECOMENDAÇÕES DE AÇÕES PREVENTIVAS (DSA)",
            "=" * 80,
            "",
        ]

        por_criticidade = {}
        for acao in recomendacoes:
            if acao.criticidade not in por_criticidade:
                por_criticidade[acao.criticidade] = []
            por_criticidade[acao.criticidade].append(acao)

        # Ordenar por criticidade (descendente)
        for crit in sorted(por_criticidade.keys(), reverse=True):
            crit_nome = ["Recomendação", "Desejável", "Crítica"][crit - 1]
            linhas.append(f"\n{crit_nome}s ({len(por_criticidade[crit])}):")
            linhas.append("-" * 80)

            for i, acao in enumerate(por_criticidade[crit], 1):
                linhas.append(f"[{i}] {acao.descrever_criacao()}")

        return "\n".join(linhas)


# ============================================================================
# v1.10.3 — INTEGRAÇÃO COM SNAPSHOTS (Multi-caso)
# ============================================================================

@dataclass
class CasoMultiplesDSA:
    """Caso para análise DSA em múltiplos cenários (com snapshots).

    Permite executar vários casos de estabilidade reutilizando a
    inicialização via snapshot.
    """
    nome_caso_base: str
    arquivo_snapshot: Optional[Path] = None
    casos_contingencia: List[str] = field(default_factory=list)
    avaliacoes: Dict[str, AvaliadorDSA] = field(default_factory=dict)

    def adicionar_contingencia(self, nome: str) -> "CasoMultiplesDSA":
        """Adiciona caso de contingência a analisar."""
        self.casos_contingencia.append(nome)
        self.avaliacoes[nome] = AvaliadorDSA(nome_caso=nome)
        return self

    def gerar_snapshot(self) -> str:
        """Comando para gravação de snapshot (§46.71 SNAP GRAV)."""
        return "SNAP GRAV\n"

    def restaurar_snapshot(self) -> str:
        """Comando para restauração de snapshot (§46.71 SNAP REST)."""
        return "SNAP REST\n"

    def gerar_sequencia_casos(self) -> str:
        """Gera sequência de comandos para análise multi-caso.

        Estrutura:
        1. Gravar snapshot (caso base inicializado)
        2. Para cada contingência:
           - Restaurar snapshot
           - Executar simulação (EXSI)
           - Gerar relatório DSA (RSEG)
        """
        linhas = [
            "( ============================================================================",
            "( ANÁLISE DSA MULTI-CASO COM SNAPSHOTS",
            "( ============================================================================",
            "",
            "( Gravar snapshot do caso base inicializado",
            self.gerar_snapshot(),
            "",
        ]

        for i, ctg in enumerate(self.casos_contingencia, 1):
            linhas.extend([
                f"( --- Caso {i}/{len(self.casos_contingencia)}: {ctg} ---",
                "( Restaurar snapshot do caso base",
                self.restaurar_snapshot(),
                "",
                "( Executar simulação",
                "EXSI",
                "(",
                "",
                "( Gerar relatório DSA",
                "RELA RSEG",
                "(",
                "",
            ])

        linhas.append("999999")
        return "\n".join(linhas)


if __name__ == "__main__":
    # Exemplo v1.10.1: Avaliação DSA
    print("=" * 70)
    print("v1.10.1: Avaliação de Segurança Dinâmica (DSA, §47.101)")
    print("=" * 70)

    # Criar avaliador
    dsa = AvaliadorDSA(nome_caso="Contingencia_LT_500kV", tempo_simulacao=2.5)

    # Adicionar elementos a monitorar
    dsa.adicionar_elemento(
        ElementoSeguranca(
            tipo=TipoElementoSeguranca.CIRCUITO,
            identificacao="LT_230kV_Rio-Brasilia",
            limite_emergencia=95.0,
        )
    )

    dsa.adicionar_elemento(
        ElementoSeguranca(
            tipo=TipoElementoSeguranca.BARRA,
            identificacao="Barra_Brasilia_500kV",
            limite_emergencia=110.0,
            limite_alerta=100.0,
        )
    )

    dsa.adicionar_elemento(
        ElementoSeguranca(
            tipo=TipoElementoSeguranca.GERACAO,
            identificacao="Gen_Itaipu_Norte",
            limite_emergencia=300.0,
        )
    )

    print(dsa.gerar_relatorio_rseg())

    # Simular valores de simulação
    print("\n" + "-" * 70)
    print("Valores Observados na Simulação:")
    valores_observados = [85.0, 105.0, 280.0]  # Dentro dos limites

    resultados = dsa.avaliar_sistema_completo(valores_observados)
    for elem_id, (status, msg, margem) in resultados.items():
        print(f"  [{status.value}] {msg} (margem: {margem:.1f})")

    # Exemplo v1.10.2: Recomendações
    print("\n" + "=" * 70)
    print("v1.10.2: Recomendações Preventivas")
    print("=" * 70)

    recomendador = RecomendadorDSA(margem_seguranca_minima=10.0)

    # Simular violação
    print("\nSimulação: Valores críticos detectados")
    valores_criticos = [98.0, 115.0, 310.0]  # Com violações

    # Avaliar novamente com valores críticos
    dsa2 = AvaliadorDSA(nome_caso="Contingencia_Crítica")
    for elem in dsa.elementos:
        dsa2.adicionar_elemento(elem)

    resultados_criticos = dsa2.avaliar_sistema_completo(valores_criticos)

    # Gerar recomendações
    recomendacoes = recomendador.recomendar_acoes(resultados_criticos)
    print(recomendador.gerar_relatorio_recomendacoes(recomendacoes))

    # Exemplo v1.10.3: Multi-caso com Snapshots
    print("\n" + "=" * 70)
    print("v1.10.3: Análise Multi-caso com Snapshots")
    print("=" * 70)

    multicaso = CasoMultiplesDSA(
        nome_caso_base="Caso_Base_Anatem",
        arquivo_snapshot=Path("snapshot_base.sav"),
    )

    multicaso.adicionar_contingencia("CTG_DES_LT_500kV_1")
    multicaso.adicionar_contingencia("CTG_DES_LT_500kV_2")
    multicaso.adicionar_contingencia("CTG_PERDA_GER_GRANDE")

    print("\nSequência de Casos DSA:")
    print(multicaso.gerar_sequencia_casos())
