"""
estabilidade_v19.py – Algoritmos de Pós-Falta e Estabilidade (v1.9).

v1.9.1: Critérios de Estabilidade Transitória (§7.4)
v1.9.2: Perda de Sincronismo (Loss of Synchronism)
v1.9.3: Recuperação de Frequência

Referência: Manual ANATEM 12.10 §5 (Pós-processamento)
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Tuple

# ============================================================================
# v1.9.1 — CRITÉRIOS DE ESTABILIDADE TRANSITÓRIA (§7.4)
# ============================================================================


class NivelAlerta(Enum):
    """Níveis de alerta para violações (§7.4.2)."""

    OK = 0  # Sem violação
    ALERTA_1 = 1  # Violação média (fundo amarelo, fonte vermelha)
    ALERTA_2 = 2  # Violação severa (fundo roxo, fonte preta)


@dataclass
class CriterioTensao:
    """Critério de tensão (§7.4, Tensão 1–5).

    5 critérios para monitoração de tensão pós-falta:
    1. Primeira oscilação
    2. Segunda oscilação
    3. Oscilações posteriores (t > Tverif)
    4. Variação final de tensão
    5. Tensão final vs. limite DGLT
    """

    tipo: int  # 1–5 (tipo de critério)
    vmin_percentual: Optional[float] = None  # Tensão mínima (% nominal)
    vmin_500kv: Optional[float] = None  # Tensão mínima específica para 500kV
    alerta_1: float = 85.0  # Limite alerta 1 (%)
    alerta_2: float = 80.0  # Limite alerta 2 (%)
    tverif: Optional[float] = None  # Tempo verificação (Tensão 3)
    amax: Optional[float] = None  # Amplitude máxima (Tensão 3)
    var_maxima: Optional[float] = None  # Variação máxima final (Tensão 4)

    def validar(self) -> tuple[bool, List[str]]:
        """Valida parâmetros do critério (§7.4)."""
        erros = []
        if self.tipo < 1 or self.tipo > 5:
            erros.append(
                f"Tipo de critério tensão inválido: {self.tipo} (deve ser 1-5)"
            )

        if self.tipo in [1, 2]:
            if self.vmin_percentual is None or self.vmin_percentual <= 0:
                erros.append(
                    f"Critério Tensão {self.tipo}: vmin_percentual deve ser > 0"
                )

        if self.tipo == 3:
            if self.tverif is None or self.tverif <= 0:
                erros.append("Critério Tensão 3: tverif deve ser > 0")
            if self.amax is None or self.amax < 0:
                erros.append("Critério Tensão 3: amax deve ser >= 0")

        if self.tipo == 4:
            if self.var_maxima is None or self.var_maxima < 0:
                erros.append("Critério Tensão 4: var_maxima deve ser >= 0")

        if self.alerta_1 <= self.alerta_2:
            erros.append(
                f"Alerta 1 ({self.alerta_1}) deve ser > Alerta 2 ({self.alerta_2})"
            )

        return len(erros) == 0, erros

    def descrever(self) -> str:
        """Descrição textual do critério."""
        descricoes = {
            1: "Primeira oscilação — Vmin percentual",
            2: "Segunda oscilação — Vmin percentual",
            3: "Oscilações posteriores — Amplitude máxima",
            4: "Variação final de tensão",
            5: "Tensão final vs. DGLT",
        }
        return descricoes.get(self.tipo, f"Tipo {self.tipo}")


@dataclass
class CriterioReativoGER:
    """Critério de Reativo em Gerador (§7.4, Reativo GER).

    Verifica se potências reativas terminais (QELE) atendem faixas
    especificadas em DBAR do Anarede.
    """

    habilitado: bool = True
    alerta_1: float = 85.0  # Limite alerta 1 (%)
    alerta_2: float = 80.0  # Limite alerta 2 (%)

    def validar(self) -> tuple[bool, List[str]]:
        """Valida parâmetros."""
        erros = []
        if self.alerta_1 <= self.alerta_2:
            erros.append(
                f"Alerta 1 ({self.alerta_1}) deve ser > Alerta 2 ({self.alerta_2})"
            )
        return len(erros) == 0, erros


@dataclass
class CriterioReativoCER:
    """Critério de Reativo em Compensador (§7.4, Reativo CER).

    Verifica se potências reativas terminais (BCES) atendem faixas
    especificadas em DCER do Anarede.
    """

    habilitado: bool = True
    # Sem parâmetros adicionais — usa limites de DCER

    def validar(self) -> tuple[bool, List[str]]:
        """Valida configuração."""
        return True, []


@dataclass
class CriterioCarregamento:
    """Critério de Carregamento de Circuito (§7.4).

    Verifica se correntes de circuito (ILIN) atendem limites de
    emergência de curta duração em DLIN.
    """

    habilitado: bool = True
    percentual_limite: float = 100.0  # % do limite de emergência (DLIN)
    alerta_1: float = 95.0  # Limite alerta 1 (%)
    alerta_2: float = 90.0  # Limite alerta 2 (%)

    def validar(self) -> tuple[bool, List[str]]:
        """Valida parâmetros."""
        erros = []
        if self.percentual_limite <= 0:
            erros.append(
                f"Percentual limite deve ser > 0 (tem {self.percentual_limite})"
            )
        if self.alerta_1 <= self.alerta_2:
            erros.append(
                f"Alerta 1 ({self.alerta_1}) deve ser > Alerta 2 ({self.alerta_2})"
            )
        return len(erros) == 0, erros


@dataclass
class CriterioReles:
    """Critério de Relés (§7.4).

    Monitora atuação de:
    - Relés de impedância
    - Sub/sobtensão
    - Sobrecorrente
    - Subfrequência
    """

    habilitado: bool = True
    monitorar_impedancia: bool = True
    monitorar_subtensao: bool = True
    monitorar_sobtensao: bool = True
    monitorar_sobrecorrente: bool = True
    monitorar_subfrequencia: bool = True

    def validar(self) -> tuple[bool, List[str]]:
        """Valida configuração."""
        at_menos_um = any(
            [
                self.monitorar_impedancia,
                self.monitorar_subtensao,
                self.monitorar_sobtensao,
                self.monitorar_sobrecorrente,
                self.monitorar_subfrequencia,
            ]
        )
        if not at_menos_um:
            return False, ["Deve monitorar ao menos um tipo de relé"]
        return True, []


@dataclass
class CriterioAngular:
    """Critério Angular (§7.4).

    Específico para análise de interligação Norte-Nordeste.
    Avalia diferença angular entre Tucuruí e Paulo Afonso.
    Requer CDU com saída TUCPAQ.
    """

    habilitado: bool = False  # Desabilitado por padrão (específico)
    # Condição: A1 <= A2
    # A1 = ΔAngle(primeira_oscilação) - 90°
    # A2 = ΔAngle(final) - 90°

    def validar(self) -> tuple[bool, List[str]]:
        """Valida configuração."""
        if self.habilitado:
            return True, []  # Sem parâmetros — usa TUCPAQ do CDU
        return True, []


@dataclass
class AnalisadorEstabilidade:
    """Analisador de Estabilidade Transitória (§7.4).

    Coordena múltiplos critérios de pós-falta para avaliar:
    - Tensão (5 critérios)
    - Reativo (GER + CER)
    - Carregamento de circuitos
    - Atuação de relés
    - Diferença angular (específico)
    """

    criterios_tensao: List[CriterioTensao] = field(default_factory=list)
    criterio_reativo_ger: Optional[CriterioReativoGER] = None
    criterio_reativo_cer: Optional[CriterioReativoCER] = None
    criterio_carregamento: Optional[CriterioCarregamento] = None
    criterio_reles: Optional[CriterioReles] = None
    criterio_angular: Optional[CriterioAngular] = None

    def adicionar_criterio_tensao(
        self, criterio: CriterioTensao
    ) -> "AnalisadorEstabilidade":
        """Adiciona critério de tensão (1-5)."""
        self.criterios_tensao.append(criterio)
        return self

    def definir_reativo_ger(
        self, criterio: CriterioReativoGER
    ) -> "AnalisadorEstabilidade":
        """Define critério reativo em gerador."""
        self.criterio_reativo_ger = criterio
        return self

    def definir_reativo_cer(
        self, criterio: CriterioReativoCER
    ) -> "AnalisadorEstabilidade":
        """Define critério reativo em compensador."""
        self.criterio_reativo_cer = criterio
        return self

    def definir_carregamento(
        self, criterio: CriterioCarregamento
    ) -> "AnalisadorEstabilidade":
        """Define critério de carregamento."""
        self.criterio_carregamento = criterio
        return self

    def definir_reles(self, criterio: CriterioReles) -> "AnalisadorEstabilidade":
        """Define critério de relés."""
        self.criterio_reles = criterio
        return self

    def definir_angular(self, criterio: CriterioAngular) -> "AnalisadorEstabilidade":
        """Define critério angular."""
        self.criterio_angular = criterio
        return self

    def validar(self) -> tuple[bool, List[str]]:
        """Valida toda configuração de critérios."""
        erros = []

        # Validar tensão
        for i, criterio in enumerate(self.criterios_tensao):
            valido, c_erros = criterio.validar()
            if not valido:
                erros.extend([f"CriterioTensao[{i}]: {e}" for e in c_erros])

        # Validar reativo
        if self.criterio_reativo_ger:
            valido, c_erros = self.criterio_reativo_ger.validar()
            if not valido:
                erros.extend([f"CriterioReativoGER: {e}" for e in c_erros])

        if self.criterio_reativo_cer:
            valido, c_erros = self.criterio_reativo_cer.validar()
            if not valido:
                erros.extend([f"CriterioReativoCER: {e}" for e in c_erros])

        # Validar carregamento
        if self.criterio_carregamento:
            valido, c_erros = self.criterio_carregamento.validar()
            if not valido:
                erros.extend([f"CriterioCarregamento: {e}" for e in c_erros])

        # Validar relés
        if self.criterio_reles:
            valido, c_erros = self.criterio_reles.validar()
            if not valido:
                erros.extend([f"CriterioReles: {e}" for e in c_erros])

        # Validar angular
        if self.criterio_angular:
            valido, c_erros = self.criterio_angular.validar()
            if not valido:
                erros.extend([f"CriterioAngular: {e}" for e in c_erros])

        return len(erros) == 0, erros

    def resumo_analise(self) -> str:
        """Resumo dos critérios configurados."""
        linhas = ["Análise de Estabilidade Transitória (§7.4):\n"]

        if self.criterios_tensao:
            linhas.append(f"  Critérios Tensão: {len(self.criterios_tensao)}")
            for criterio in self.criterios_tensao:
                linhas.append(f"    • Tipo {criterio.tipo}: {criterio.descrever()}")

        if self.criterio_reativo_ger and self.criterio_reativo_ger.habilitado:
            linhas.append("  Reativo GER: Habilitado")

        if self.criterio_reativo_cer and self.criterio_reativo_cer.habilitado:
            linhas.append("  Reativo CER: Habilitado")

        if self.criterio_carregamento and self.criterio_carregamento.habilitado:
            linhas.append("  Carregamento Circuito: Habilitado")

        if self.criterio_reles and self.criterio_reles.habilitado:
            linhas.append("  Relés: Habilitado")

        if self.criterio_angular and self.criterio_angular.habilitado:
            linhas.append("  Angular (Tucuruí-PAF): Habilitado")

        return "\n".join(linhas)


# ============================================================================
# v1.9.2 — PERDA DE SINCRONISMO (Loss of Synchronism)
# ============================================================================


@dataclass
class IndicadorSincronismo:
    """Indicador de Perda de Sincronismo (Loss of Synchronism).

    Monitora abertura angular de máquinas síncronas para detectar
    perda de síncrono (ângulo > 180° → instável).
    """

    ncdu: int  # Número identificador do CDU/máquina
    nome: str  # Identificação alfanumérica
    angulo_max_graus: float = 360.0  # Limite de ângulo máximo (default)
    opcao_peco: bool = True  # Transformar erro em aviso se > 1000°

    def validar(self) -> tuple[bool, List[str]]:
        """Valida indicador."""
        erros = []
        if self.ncdu <= 0:
            erros.append(f"NCDU deve ser > 0 (tem {self.ncdu})")
        if not self.nome:
            erros.append("Nome não pode estar vazio")
        if self.angulo_max_graus <= 0:
            erros.append(f"Ângulo máximo deve ser > 0 (tem {self.angulo_max_graus}°)")
        return len(erros) == 0, erros

    def avaliar_estabilidade(self, angulo_observado: float) -> Tuple[bool, str]:
        """Avalia estabilidade baseado em ângulo observado.

        Retorna: (estável, mensagem)
        """
        if angulo_observado > 180:
            return False, f"Perda de síncrono: ângulo {angulo_observado:.1f}° > 180°"
        elif angulo_observado > self.angulo_max_graus:
            if self.opcao_peco and angulo_observado > 1000:
                return (
                    True,
                    f"Aviso: ângulo {angulo_observado:.1f}° > limite (transformado em aviso)",
                )
            else:
                return (
                    False,
                    f"Ângulo {angulo_observado:.1f}° > limite {self.angulo_max_graus:.1f}°",
                )
        return True, f"Estável: ângulo {angulo_observado:.1f}° < limite"


@dataclass
class MonitorSincronismo:
    """Monitor de Sincronismo para múltiplas máquinas."""

    indicadores: List[IndicadorSincronismo] = field(default_factory=list)

    def adicionar_indicador(
        self, indicador: IndicadorSincronismo
    ) -> "MonitorSincronismo":
        """Adiciona máquina a monitorar."""
        self.indicadores.append(indicador)
        return self

    def avaliar_sistema(self, angulos: dict[int, float]) -> dict:
        """Avalia estabilidade do sistema.

        Args:
            angulos: Dict {ncdu: ângulo_em_graus}

        Retorna:
            {ncdu: (estável, mensagem)}
        """
        resultados: dict[int, Tuple[Optional[bool], str]] = {}
        for ind in self.indicadores:
            if ind.ncdu in angulos:
                estavel, msg = ind.avaliar_estabilidade(angulos[ind.ncdu])
                resultados[ind.ncdu] = (estavel, msg)
            else:
                resultados[ind.ncdu] = (None, "Ângulo não disponível")
        return resultados


# ============================================================================
# v1.9.3 — RECUPERAÇÃO DE FREQUÊNCIA
# ============================================================================


@dataclass
class AlgoritmoRecuperacaoFrequencia:
    """Algoritmo de recuperação de frequência pós-falta.

    Monitora frequência do sistema e detecta recuperação após distúrbio.
    """

    frecuencia_nominal: float = 60.0  # Hz (Brasil)
    df_max_admitida: float = 2.0  # Hz (máxima variação)
    tempo_recuperacao: float = 5.0  # segundos (tempo máximo recuperação)
    margem_estabilidade: float = 0.5  # Hz (margem de segurança)

    def validar(self) -> tuple[bool, List[str]]:
        """Valida parâmetros."""
        erros = []
        if self.frecuencia_nominal <= 0:
            erros.append(
                f"Frequência nominal deve ser > 0 (tem {self.frecuencia_nominal})"
            )
        if self.df_max_admitida <= 0:
            erros.append(f"ΔF máxima deve ser > 0 (tem {self.df_max_admitida})")
        if self.tempo_recuperacao <= 0:
            erros.append(
                f"Tempo recuperação deve ser > 0 (tem {self.tempo_recuperacao})"
            )
        if self.margem_estabilidade < 0:
            erros.append(
                f"Margem estabilidade não pode ser < 0 (tem {self.margem_estabilidade})"
            )
        return len(erros) == 0, erros

    def avaliar_recuperacao(
        self, f_minima: float, t_recuperacao: float
    ) -> Tuple[bool, str]:
        """Avalia se sistema se recupera adequadamente.

        Args:
            f_minima: Frequência mínima atingida (Hz)
            t_recuperacao: Tempo até retornar a nominal (segundos)

        Retorna:
            (recuperado, mensagem)
        """
        delta_f = abs(self.frecuencia_nominal - f_minima)

        if delta_f > self.df_max_admitida:
            return False, f"ΔF = {delta_f:.2f} Hz > limite {self.df_max_admitida} Hz"

        if t_recuperacao > self.tempo_recuperacao:
            return (
                False,
                f"Recuperação em {t_recuperacao:.1f}s > limite {self.tempo_recuperacao:.1f}s",
            )

        if delta_f > self.frecuencia_nominal - self.margem_estabilidade:
            return False, f"Frequência mínima {f_minima:.2f} Hz < limite de segurança"

        return (
            True,
            f"Recuperação adequada: ΔF={delta_f:.2f} Hz em {t_recuperacao:.1f}s",
        )


if __name__ == "__main__":
    # Exemplo v1.9.1: Critérios de Estabilidade
    print("=" * 70)
    print("v1.9.1: Análise de Estabilidade Transitória (§7.4)")
    print("=" * 70)

    analisador = AnalisadorEstabilidade()

    # Adicionar critérios de tensão
    analisador.adicionar_criterio_tensao(
        CriterioTensao(tipo=1, vmin_percentual=85.0, alerta_1=90, alerta_2=85)
    )
    analisador.adicionar_criterio_tensao(
        CriterioTensao(tipo=2, vmin_percentual=80.0, vmin_500kv=90.0)
    )

    # Reativo
    analisador.definir_reativo_ger(CriterioReativoGER())
    analisador.definir_carregamento(CriterioCarregamento(percentual_limite=90.0))
    analisador.definir_reles(CriterioReles())

    print(analisador.resumo_analise())

    # Validar
    valido, erros = analisador.validar()
    print(f"\nValidação: {'OK' if valido else 'ERRO'}")
    if not valido:
        for erro in erros:
            print(f"  - {erro}")

    # Exemplo v1.9.2: Perda de Sincronismo
    print("\n" + "=" * 70)
    print("v1.9.2: Perda de Sincronismo (Loss of Synchronism)")
    print("=" * 70)

    monitor = MonitorSincronismo()
    monitor.adicionar_indicador(
        IndicadorSincronismo(ncdu=1, nome="GEN_BRASILIA", angulo_max_graus=360.0)
    )
    monitor.adicionar_indicador(
        IndicadorSincronismo(ncdu=2, nome="GEN_SUL", angulo_max_graus=360.0)
    )

    # Simular ângulos observados
    angulos_observados = {
        1: 45.0,  # Estável
        2: 185.0,  # Instável (> 180°)
    }

    print("Avaliação de Sincronismo:")
    resultados = monitor.avaliar_sistema(angulos_observados)
    for ncdu, (estavel, msg) in resultados.items():
        status = "OK" if estavel else "FALHA"
        print(f"  [{status}] Máquina {ncdu}: {msg}")

    # Exemplo v1.9.3: Recuperação de Frequência
    print("\n" + "=" * 70)
    print("v1.9.3: Recuperação de Frequência")
    print("=" * 70)

    alg_freq = AlgoritmoRecuperacaoFrequencia(
        frecuencia_nominal=60.0,
        df_max_admitida=2.0,
        tempo_recuperacao=5.0,
        margem_estabilidade=0.5,
    )

    # Teste 1: Recuperação adequada
    estavel, msg = alg_freq.avaliar_recuperacao(f_minima=58.5, t_recuperacao=3.2)
    print(f"[{'OK' if estavel else 'FALHA'}] Teste 1: {msg}")

    # Teste 2: Queda de frequência excessiva
    estavel, msg = alg_freq.avaliar_recuperacao(f_minima=57.0, t_recuperacao=2.0)
    print(f"[{'OK' if estavel else 'FALHA'}] Teste 2: {msg}")

    # Teste 3: Recuperação lenta
    estavel, msg = alg_freq.avaliar_recuperacao(f_minima=59.0, t_recuperacao=6.5)
    print(f"[{'OK' if estavel else 'FALHA'}] Teste 3: {msg}")
