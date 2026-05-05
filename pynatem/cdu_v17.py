"""
cdu_v17.py – Definições e Inicializações de CDU (v1.7).

v1.7.1: DEFVAL, DEFVDF, DEFPLT — Inicialização de Modelos CDU
  Especificação §29.4–29.7 do Manual ANATEM 12.10

DEFVAL (§29.4):
  Declaração de variável e valor inicial de CDU.
  Campos: DEFVAL (stip) (vdef) (d1) (o) (d2)
    stip: subtipo (em branco, VAR, CDU, VOLT, FREQ, ANGL, FLXA, TAP, etc)
    vdef: identificação alfanumérica da variável
    d1: valor/nome/ID conforme stip (em branco→valor numérico ou #PARAM)
    o: exclusão em relatório P2D2 NULL (opcional)
    d2: valor default se localização remota ausente

DEFVDF (§29.5):
  Definição de valor default para saída de bloco INPUT.
  Campos: DEFVDF (nome) (valor)
    nome: identificação alfanumérica do sinal de saída INPUT
    valor: numérico ou #PARAM (used when equipment absent)

DEFPLT (§29.6):
  Declaração de variável para plotagem automática.
  Campos: DEFPLT (var)
    var: identificação alfanumérica da variável a plotar

Inicialização (§29.7):
  Algoritmo em 12 passos para inicializar CDU no início da simulação.
  Passo 1: Tentar inicializar a partir de DEFVAL.
"""

from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class DEFVAL:
    """Declaração de Valor Inicial de Variável CDU (§29.4)."""

    vdef: str  # identificação alfanumérica da variável
    d1: str = ""  # valor/nome/ID conforme stip
    stip: str = ""  # subtipo (vazio=numérico, VAR, CDU, VOLT, FREQ, etc)
    o: bool = False  # exclusão P2D2 NULL
    d2: float = 0.0  # valor default se localização ausente

    def serializar(self) -> str:
        """Serializa em formato ANATEM §29.4."""
        linha = f"DEFVAL"
        if self.stip:
            linha += f" {self.stip:<6}"
        else:
            linha += f" {'':<6}"
        linha += f" {self.vdef:<15}"
        linha += f" {self.d1:<20}"
        if self.o:
            linha += f" O"
        if self.d2 != 0.0:
            linha += f" {self.d2:>15.10f}"
        return linha + "\n"


@dataclass
class DEFVDF:
    """Declaração de Valor Default para INPUT (§29.5)."""

    nome: str  # identificação da saída de bloco INPUT
    valor: float  # valor default (numérico ou #PARAM)

    def serializar(self) -> str:
        """Serializa em formato ANATEM §29.5."""
        return f"DEFVDF {self.nome:<15} {self.valor:>15.10f}\n"


@dataclass
class DEFPLT:
    """Declaração de Variável para Plotagem (§29.6)."""

    var: str  # identificação alfanumérica da variável

    def serializar(self) -> str:
        """Serializa em formato ANATEM §29.6."""
        return f"DEFPLT {self.var:<15}\n"


@dataclass
class InicializacaoCDU:
    """Agregador de definições DEFVAL/DEFVDF/DEFPLT para inicialização CDU (§29.7)."""

    defval_list: List[DEFVAL] = field(default_factory=list)
    defvdf_list: List[DEFVDF] = field(default_factory=list)
    defplt_list: List[DEFPLT] = field(default_factory=list)

    def adicionar_defval(self, vdef: str, d1: str = "", stip: str = "",
                        o: bool = False, d2: float = 0.0) -> "InicializacaoCDU":
        """Adiciona DEFVAL (§29.4)."""
        self.defval_list.append(DEFVAL(vdef=vdef, d1=d1, stip=stip, o=o, d2=d2))
        return self

    def adicionar_defvdf(self, nome: str, valor: float) -> "InicializacaoCDU":
        """Adiciona DEFVDF (§29.5)."""
        self.defvdf_list.append(DEFVDF(nome=nome, valor=valor))
        return self

    def adicionar_defplt(self, var: str) -> "InicializacaoCDU":
        """Adiciona DEFPLT (§29.6)."""
        self.defplt_list.append(DEFPLT(var=var))
        return self

    def serializar(self) -> str:
        """Serializa na ordem correta (DEFVAL → DEFVDF → DEFPLT)."""
        linhas = []
        for defval in self.defval_list:
            linhas.append(defval.serializar())
        for defvdf in self.defvdf_list:
            linhas.append(defvdf.serializar())
        for defplt in self.defplt_list:
            linhas.append(defplt.serializar())
        return "".join(linhas)


@dataclass
class MensagemPersonalizada:
    """Mensagem personalizada para alertas em CDU (§33.1, código DMSG).

    Define mensagens que serão emitidas por blocos ALERTA durante simulação.
    Suporta expressões coringas que são substituídas em tempo de simulação.
    """
    lc: int  # número identificador da mensagem (usado por ALERTA P1/P2)
    texto: str  # mensagem com expressões coringas

    CORINGAS_VALIDAS = {
        "%vent%": "Nome da variável de entrada do bloco (6 chars)",
        "%nb%": "Número do bloco",
        "%nome_do_cdu%": "Nome do CDU (identificação alfanumérica)",
        "%ncdu%": "Número do CDU",
        "%trns%": "Transição observada ('0 -> 1' ou '1 -> 0')",
    }

    def validar(self) -> tuple[bool, List[str]]:
        """Valida se coringas utilizados são válidos."""
        erros = []
        import re
        coringas_encontrados = re.findall(r'%[^%]+%', self.texto)
        for coringa in coringas_encontrados:
            if coringa not in self.CORINGAS_VALIDAS:
                erros.append(f"Coringa inválido: {coringa}")
        return len(erros) == 0, erros

    def serializar(self) -> str:
        """Serializa em formato ANATEM DMSG."""
        return f"DMSG {self.lc:<10} {self.texto}\n"


@dataclass
class BlocoAlerta:
    """Bloco ALERTA para monitoração com mensagens personalizadas (§33.1.2).

    Emite mensagem quando entrada transita entre 0/1 ou 1/0.
    P1: Lc para transição 0->1 (em branco=desabilitado, 0=msg padrão, >0=DMSG)
    P2: Lc para transição 1->0 (mesma lógica)
    """
    nome: str  # identificação do bloco
    entrada: str  # sinal de entrada a monitorar
    p1: Optional[int] = None  # mensagem para 0->1
    p2: Optional[int] = None  # mensagem para 1->0

    def validar(self) -> tuple[bool, str]:
        """Valida se ao menos P1 ou P2 está preenchido."""
        if self.p1 is None and self.p2 is None:
            return False, "Ao menos P1 ou P2 deve estar preenchido"
        return True, ""

    def serializar_bloco_cdu(self) -> str:
        """Serializa bloco ALERTA em formato CDU."""
        linha = f"BLO {self.nome} ALERTA {self.entrada}"
        if self.p1 is not None:
            linha += f" {self.p1}"
        else:
            linha += " "
        if self.p2 is not None:
            linha += f" {self.p2}"
        else:
            linha += " "
        return linha + "\n"


@dataclass
class AlgoritmoOTM:
    """Algoritmo OTMx para detecção de malha inativa (§32.5, código DARQ/RELA).

    Define quais algoritmos de otimização usar:
    - OTM3: Forward/Backward a partir de ENTRAD
    - OTM4: Backward a partir de SAIDA
    - OTM5: Backward a partir de ganho nulo
    - OTMX: Combinação automática (recomendada)
    """
    tipo: str  # "OTM3", "OTM4", "OTM5" ou "OTMX" (recomendado)
    ativo: bool = True  # habilitar algoritmo
    gerar_relatorio: bool = False  # gerar relatório com blocos desligados

    ALGORITMOS_VALIDOS = {
        "OTM3": "Forward/Backward a partir de ENTRAD",
        "OTM4": "Backward a partir de SAIDA",
        "OTM5": "Backward a partir de ganho nulo",
        "OTMX": "Combinação automática (recomendada)",
    }

    def validar(self) -> tuple[bool, str]:
        """Valida se tipo é um algoritmo conhecido."""
        if self.tipo not in self.ALGORITMOS_VALIDOS:
            return False, f"Tipo OTM desconhecido: {self.tipo}"
        return True, ""

    def serializar_opcao(self) -> str:
        """Serializa para código DARQ/RELA."""
        status = "[ATIVO]" if self.ativo else "[INATIVO]"
        relatorio = " + RELATÓRIO" if self.gerar_relatorio else ""
        return f"{self.tipo} {status}{relatorio}\n"


@dataclass
class Sensor:
    """Sensor/Supervisor de um SEP por CDU (§34.2.1).

    Sensores importam grandezas elétricas da rede para monitoração.
    Implementados como blocos IMPORT com subtipo apropriado.
    """
    nome: str  # identificação alfanumérica do sensor
    tipo: str  # subtipo de IMPORT (STBUS, STCIRC, VOLT, FREQ, etc)
    equipamento: str  # localização remota: nb (barra), nclin (linha), etc
    p1: Optional[str] = None  # parâmetro P1 (opcional, mas recomendado)
    p2: float = 0.0  # parâmetro P2 (valor default se equipamento ausente)
    localizacao_base: bool = False  # usar BASE em DLOC para topologia variável

    def serializar_bloco_import(self) -> str:
        """Gera linha BLO IMPORT para o CDU (simplificado)."""
        linha = f"BLO {self.nome} IMPORT {self.tipo} {self.equipamento}"
        if self.p1:
            linha += f" P1={self.p1}"
        if self.p2 != 0.0:
            linha += f" P2={self.p2}"
        return linha + "\n"


@dataclass
class Atuador:
    """Atuador de um SEP por CDU (§34.2.2).

    Atuadores efetuam comandos sobre equipamentos do sistema.
    Implementados como blocos EXPORT.
    Suportam manual override (IMPORT de referência) ou sem override (ENTRAD).
    """
    nome: str  # identificação alfanumérica do atuador
    tipo: str  # tipo de ação (STGER, STBSH, RTRF, XTRF, etc)
    equipamento: str  # localização: nb, (nb,gr), (ni, nf, nclin), etc
    manual_override: bool = False  # True = usa IMPORT referência + comando pulsante
    p1: Optional[str] = None  # parâmetro P1 (obrigatório)
    referencia_bloco: str = ""  # nome do bloco IMPORT/ENTRAD de referência

    def serializar_bloco_export(self) -> str:
        """Gera linha BLO EXPORT para o CDU (simplificado)."""
        linha = f"BLO {self.nome} EXPORT {self.tipo} {self.equipamento}"
        if self.p1:
            linha += f" P1={self.p1}"
        if self.manual_override:
            linha += " OVERRIDE"
        return linha + "\n"


@dataclass
class MalhaHabilitadora:
    """Malha Habilitadora de um SEP (§34.2.3).

    Modela as CONDIÇÕES NECESSÁRIAS para ativação (lógica AND).
    Todas as condições precisam ser verdadeiras simultaneamente.
    """
    nome: str  # identificação: ex "MALHA_ENABLE"
    condicoes: List[str] = field(default_factory=list)  # sinais que habilitem

    def adicionar_condicao(self, sinal: str) -> "MalhaHabilitadora":
        """Adiciona condição habilitadora."""
        self.condicoes.append(sinal)
        return self

    def serializar_bloco_and(self) -> str:
        """Gera linha BLO AND que concatena condições."""
        if not self.condicoes:
            return ""
        # Simplificado: assume até 4 entradas
        entradas = " ".join(self.condicoes[:4])
        return f"BLO {self.nome} AND {entradas}\n"


@dataclass
class MalhaInibidora:
    """Malha Inibidora de um SEP (§34.2.3).

    Modela as EXCEÇÕES para não-atuação (lógica NOR).
    Basta uma condição ser falsa para inibir a proteção.
    """
    nome: str  # identificação: ex "MALHA_INIBIR"
    condicoes: List[str] = field(default_factory=list)  # sinais que inibam

    def adicionar_condicao_inibicao(self, sinal: str) -> "MalhaInibidora":
        """Adiciona condição de inibição."""
        self.condicoes.append(sinal)
        return self

    def serializar_bloco_nor(self) -> str:
        """Gera linha BLO NOR que concatena inibições."""
        if not self.condicoes:
            return ""
        # Simplificado: assume até 4 entradas
        entradas = " ".join(self.condicoes[:4])
        return f"BLO {self.nome} NOR {entradas}\n"


@dataclass
class MalhaAtuadora:
    """Malha Atuadora de um SEP (§34.2.4).

    Núcleo da lógica de atuação: avalia mudanças a provocar no sistema
    em função de variáveis monitoradas. Maior parte dos blocos concentra-se aqui.
    """
    blocos: List[str] = field(default_factory=list)  # linhas de blocos CDU

    def adicionar_bloco(self, linha_bloco: str) -> "MalhaAtuadora":
        """Adiciona bloco lógico à malha atuadora."""
        self.blocos.append(linha_bloco)
        return self

    def serializar_blocos(self) -> str:
        """Serializa todos os blocos da malha atuadora."""
        return "".join(b if b.endswith("\n") else b + "\n" for b in self.blocos)


@dataclass
class ReleouSEP:
    """Agregador de Relé ou Sistema Especial de Proteção (§34.1–34.4).

    Encapsula sensores, atuadores, malhas habilitadora/inibidora e malha atuadora.
    Gera CDU com estrutura bem-definida para proteção.
    """
    nome: str  # identificação do relé/SEP
    sensores: List[Sensor] = field(default_factory=list)
    atuadores: List[Atuador] = field(default_factory=list)
    malha_habilitadora: Optional[MalhaHabilitadora] = None
    malha_inibidora: Optional[MalhaInibidora] = None
    malha_atuadora: Optional[MalhaAtuadora] = None

    def adicionar_sensor(self, sensor: Sensor) -> "ReleouSEP":
        """Adiciona sensor de monitoração."""
        self.sensores.append(sensor)
        return self

    def adicionar_atuador(self, atuador: Atuador) -> "ReleouSEP":
        """Adiciona atuador de comando."""
        self.atuadores.append(atuador)
        return self

    def definir_malha_habilitadora(self, malha: MalhaHabilitadora) -> "ReleouSEP":
        """Define malha habilitadora."""
        self.malha_habilitadora = malha
        return self

    def definir_malha_inibidora(self, malha: MalhaInibidora) -> "ReleouSEP":
        """Define malha inibidora."""
        self.malha_inibidora = malha
        return self

    def definir_malha_atuadora(self, malha: MalhaAtuadora) -> "ReleouSEP":
        """Define malha atuadora (núcleo lógico)."""
        self.malha_atuadora = malha
        return self

    def serializar_cdu(self) -> str:
        """Serializa relé/SEP como corpo CDU estruturado."""
        linhas = [f"# Relé/SEP: {self.nome}\n", "# Estrutura: Sensores -> Malhas -> Atuadores\n\n"]

        # Seção de Sensores (IMPORT)
        if self.sensores:
            linhas.append("# SENSORES (Importação de grandezas elétricas)\n")
            for sensor in self.sensores:
                linhas.append(sensor.serializar_bloco_import())
            linhas.append("\n")

        # Seção de Malha Habilitadora (AND)
        if self.malha_habilitadora:
            linhas.append("# MALHA HABILITADORA (Condições necessárias para atuação)\n")
            linhas.append(self.malha_habilitadora.serializar_bloco_and())
            linhas.append("\n")

        # Seção de Malha Inibidora (NOR)
        if self.malha_inibidora:
            linhas.append("# MALHA INIBIDORA (Exceções que impedem atuação)\n")
            linhas.append(self.malha_inibidora.serializar_bloco_nor())
            linhas.append("\n")

        # Seção de Malha Atuadora (Núcleo lógico)
        if self.malha_atuadora:
            linhas.append("# MALHA ATUADORA (Lógica de decisão e comando)\n")
            linhas.append(self.malha_atuadora.serializar_blocos())
            linhas.append("\n")

        # Seção de Atuadores (EXPORT)
        if self.atuadores:
            linhas.append("# ATUADORES (Comandos para equipamentos da rede)\n")
            linhas.append("# Recomendação: adicionar DELAY antes do EXPORT para estabilidade\n")
            for atuador in self.atuadores:
                linhas.append(atuador.serializar_bloco_export())

        return "".join(linhas)


@dataclass
class ParametroTopologia:
    """Parâmetro em uma topologia de CDU (§30.1.1)."""
    nome: str  # identificação do parâmetro
    valor_padrao: float  # valor padrão na topologia
    obrigatorio: bool = False  # True = usuario DEVE redefinir em ACDU

    def __str__(self) -> str:
        """Formato legível com indicador obrigatório."""
        ob_str = " [OBRIGATÓRIO]" if self.obrigatorio else " [opcional]"
        return f"{self.nome} = {self.valor_padrao}{ob_str}"


@dataclass
class TopologiaCDU:
    """Definição de Topologia de CDU (§30.1, código DTDU).

    Uma topologia é um modelo genérico de controle que pode ser reutilizado
    em múltiplos equipamentos. Os parâmetros podem ser obrigatórios
    (usuário deve redefinir) ou opcionais (herdam valor da topologia).
    """
    ntop: int  # número identificador da topologia
    nome: str  # identificação alfanumérica
    parametros: dict[str, ParametroTopologia] = field(default_factory=dict)
    blocos: List[str] = field(default_factory=list)  # corpo CDU (linhas em ANATEM)
    inicializacao: Optional[InicializacaoCDU] = None

    def adicionar_parametro(self, nome: str, valor_padrao: float,
                            obrigatorio: bool = False) -> "TopologiaCDU":
        """Adiciona parâmetro à topologia (§30.1.1)."""
        self.parametros[nome] = ParametroTopologia(
            nome=nome, valor_padrao=valor_padrao, obrigatorio=obrigatorio
        )
        return self

    def adicionar_bloco(self, linha_anatem: str) -> "TopologiaCDU":
        """Adiciona linha do corpo CDU (blocos, MAE, etc)."""
        self.blocos.append(linha_anatem)
        return self

    def definir_inicializacao(self, init: InicializacaoCDU) -> "TopologiaCDU":
        """Associa inicialização (DEFVAL/DEFVDF/DEFPLT)."""
        self.inicializacao = init
        return self

    def validar_parametros_obrigatorios(self, params_redefinidos: dict[str, float]
                                       ) -> tuple[bool, List[str]]:
        """Verifica se todos os parâmetros obrigatórios foram redefinidos.

        Retorna: (válido, lista de parâmetros faltantes)
        """
        faltantes = []
        for nome, param in self.parametros.items():
            if param.obrigatorio and nome not in params_redefinidos:
                faltantes.append(nome)
        return len(faltantes) == 0, faltantes

    def serializar_dtdu(self) -> str:
        """Serializa como DTDU (definição de topologia)."""
        linhas = [f"DTDU {self.ntop:<10} {self.nome:<30}\n"]

        # Parâmetros (DEFPAR)
        for nome, param in self.parametros.items():
            ob_flag = " O" if param.obrigatorio else ""
            linhas.append(
                f"DEFPAR {nome:<15} {param.valor_padrao:>15.10f}{ob_flag}\n"
            )

        # Corpo da topologia (blocos CDU)
        for bloco in self.blocos:
            if not bloco.endswith("\n"):
                bloco += "\n"
            linhas.append(bloco)

        # Inicialização (DEFVAL/DEFVDF/DEFPLT)
        if self.inicializacao:
            linhas.append(self.inicializacao.serializar())

        linhas.append("FIMCDU\n")
        return "".join(linhas)


@dataclass
class AssociacaoCDU:
    """Associação de CDU a Topologia (§30.2, código ACDU).

    Cria uma instância concreta de uma topologia, redefinindo
    parâmetros conforme necessário.
    """
    ncdu: int  # número identificador do CDU
    ntop: int  # número da topologia (referência DTDU)
    nome: str  # identificação alfanumérica
    parametros_redefinidos: dict[str, float] = field(default_factory=dict)
    topologia: Optional[TopologiaCDU] = None

    def adicionar_parametro(self, nome: str, valor: float) -> "AssociacaoCDU":
        """Redefine parâmetro da topologia (§30.2.2)."""
        self.parametros_redefinidos[nome] = valor
        return self

    def validar(self) -> tuple[bool, List[str]]:
        """Valida se topologia pode ser usada."""
        if not self.topologia:
            return False, ["Topologia não associada"]
        return self.topologia.validar_parametros_obrigatorios(
            self.parametros_redefinidos
        )

    def serializar_acdu(self) -> str:
        """Serializa como ACDU (associação de CDU)."""
        linhas = [f"ACDU {self.ncdu:<10} {self.ntop:<10} {self.nome:<30}\n"]

        # Redefinição de parâmetros (§30.2.2)
        for nome, valor in self.parametros_redefinidos.items():
            linhas.append(f"DEFPAR {nome:<15} {valor:>15.10f}\n")

        linhas.append("FIMCDU\n")
        return "".join(linhas)


if __name__ == "__main__":
    # Exemplo v1.7.1: AVR simples com inicialização
    print("=" * 70)
    print("v1.7.1: Inicialização de Modelos CDU")
    print("=" * 70)
    init = InicializacaoCDU()

    # DEFVAL: valores iniciais de variáveis de estado
    # Tipo 1: valor numérico direto
    init.adicionar_defval("X1", d1="0.0", stip="")  # X1 = 0.0
    init.adicionar_defval("X2", d1="1.0", stip="")  # X2 = 1.0

    # Tipo 2: importar tensão da barra terminal (d1 vazio = barra do equipamento)
    init.adicionar_defval("VTERMO", d1="", stip="VOLT", d2=1.0)  # default 1.0 pu

    # DEFVDF: valores default para INPUT (quando equipamento ausente)
    init.adicionar_defvdf("QINPi", 0.0)  # Reativo default = 0
    init.adicionar_defvdf("STINPi", 1.0)  # Status default = 1

    # DEFPLT: variáveis para plotagem automática
    init.adicionar_defplt("X1")  # Plotar estado X1
    init.adicionar_defplt("VSAIDA")  # Plotar saída

    print("\nv1.7.1 Output:")
    print(init.serializar())

    # Exemplo v1.7.2: Topologia de AVR genérico
    print("\n" + "=" * 70)
    print("v1.7.2: Topologia de CDU (DTDU + ACDU)")
    print("=" * 70)

    # Definir topologia (DTDU)
    top_avr = TopologiaCDU(ntop=1, nome="AVR_GENERICO")

    # Parâmetros obrigatórios (específicos de cada equipamento)
    top_avr.adicionar_parametro("KA", 100.0, obrigatorio=True)  # Ganho do AVR
    top_avr.adicionar_parametro("TA", 0.1, obrigatorio=True)   # Constante de tempo

    # Parâmetros opcionais (típicos, podem não mudar)
    top_avr.adicionar_parametro("VMAX", 2.0, obrigatorio=False)  # Limite máximo
    top_avr.adicionar_parametro("VMIN", -2.0, obrigatorio=False)  # Limite mínimo

    # Blocos de CDU (simplificado)
    top_avr.adicionar_bloco("BLO 1 ATRASO1 KA TA  Vref V 0 0 0 0 0 0 0 0")
    top_avr.adicionar_bloco("BLO 2 SAÍDA   1 Vregul 0 0 0 0 0 0 0 0 0 0")

    # Inicialização
    init_avr = InicializacaoCDU()
    init_avr.adicionar_defval("Vregul", d1="0.0", stip="")
    init_avr.adicionar_defval("Vref", d1="1.0", stip="VOLT", d2=1.0)
    top_avr.definir_inicializacao(init_avr)

    print("\nTopologia DTDU (1 = AVR_GENERICO):")
    print(top_avr.serializar_dtdu())

    # Usar a topologia (ACDU) — 2 instâncias diferentes
    print("\n" + "-" * 70)
    print("Associação ACDU #1 — Gerador 1 (máquina síncrona em barra 1)")
    print("-" * 70)

    acdu1 = AssociacaoCDU(ncdu=1, ntop=1, nome="AVR_GEN1")
    acdu1.topologia = top_avr
    acdu1.adicionar_parametro("KA", 150.0)   # Mais rápido para gen grande
    acdu1.adicionar_parametro("TA", 0.08)
    acdu1.adicionar_parametro("VMAX", 2.5)   # Limite maior

    valido, faltantes = acdu1.validar()
    if valido:
        print(acdu1.serializar_acdu())
    else:
        print(f"ERRO: Parâmetros obrigatórios faltantes: {faltantes}")

    print("-" * 70)
    print("Associação ACDU #2 — Gerador 2 (máquina menor, parâmetros conservadores)")
    print("-" * 70)

    acdu2 = AssociacaoCDU(ncdu=2, ntop=1, nome="AVR_GEN2")
    acdu2.topologia = top_avr
    acdu2.adicionar_parametro("KA", 80.0)    # Mais lento para gen pequeno
    acdu2.adicionar_parametro("TA", 0.15)
    # VMAX e VMIN usam defaults da topologia

    valido, faltantes = acdu2.validar()
    if valido:
        print(acdu2.serializar_acdu())
    else:
        print(f"ERRO: Parâmetros obrigatórios faltantes: {faltantes}")

    # Demonstrar erro: ACDU sem redefinir parâmetro obrigatório
    print("\n" + "-" * 70)
    print("Associação ACDU #3 — FALTA parâmetro obrigatório (erro esperado)")
    print("-" * 70)

    acdu3 = AssociacaoCDU(ncdu=3, ntop=1, nome="AVR_GEN3")
    acdu3.topologia = top_avr
    acdu3.adicionar_parametro("KA", 90.0)
    # Faltou TA obrigatório!

    valido, faltantes = acdu3.validar()
    if not valido:
        print(f"[ERRO DETECTADO] Parâmetros obrigatórios faltantes: {faltantes}")
    else:
        print(acdu3.serializar_acdu())

    # Exemplo v1.7.3: Relé de Subtensão (UV) customizado por CDU
    print("\n" + "=" * 70)
    print("v1.7.3: Relé/SEP por CDU (Estrutura de Proteção)")
    print("=" * 70)

    # Criar estrutura de relé de subtensão
    rele_uv = ReleouSEP(nome="Rele_Subtensao_Barra_1")

    # SENSORES: monitorar tensão de barra
    rele_uv.adicionar_sensor(
        Sensor(
            nome="sensor_V",
            tipo="VOLT",
            equipamento="1",  # barra 1
            p1="V",
            p2=1.0  # default 1 pu se barra ausente
        )
    )

    # MALHA HABILITADORA: relé ativo se barra 1 está ligada
    enable = MalhaHabilitadora("status_enable")
    enable.adicionar_condicao("STBUS_1")  # estado da barra 1
    rele_uv.definir_malha_habilitadora(enable)

    # MALHA INIBIDORA: não atuar se sistema está em colapso
    inibir = MalhaInibidora("status_inibir")
    inibir.adicionar_condicao_inibicao("FREQ_CRITICA")  # frequência crítica
    inibir.adicionar_condicao_inibicao("DESLIGAMENTO_IMINENTE")  # flag de segurança
    rele_uv.definir_malha_inibidora(inibir)

    # MALHA ATUADORA: lógica de comparação com limites
    malha = MalhaAtuadora()
    malha.adicionar_bloco("BLO comp COMPAR sensor_V 0.7 0 0 0")  # V < 0.7 pu
    malha.adicionar_bloco("BLO temp DISMAX comp 0.5 0 0 0")  # temporização 0.5s
    malha.adicionar_bloco("BLO logica AND status_enable temp")  # habilita e temporização
    malha.adicionar_bloco("BLO comando NOR status_inibir logica")  # não inibido
    rele_uv.definir_malha_atuadora(malha)

    # ATUADORES: desconectar carga quando subtensão detectada
    rele_uv.adicionar_atuador(
        Atuador(
            nome="cmd_carga",
            tipo="STLDP",  # Percentual de carga ativa
            equipamento="1",  # barra 1
            manual_override=False,
            p1="REDUCAO",
        )
    )

    print("\nRelé/SEP Estruturado (v1.7.3):")
    print(rele_uv.serializar_cdu())

    # Exemplo v1.7.4: Mensagens Personalizadas + Otimizações
    print("\n" + "=" * 70)
    print("v1.7.4: Mensagens Personalizadas + OTMx (Malha Inativa)")
    print("=" * 70)

    # Definir mensagens personalizadas (DMSG)
    print("\n--- MENSAGENS PERSONALIZADAS ---")
    msg1 = MensagemPersonalizada(
        lc=1001,
        texto="ALERTA: Subtensao detectada em %nome_do_cdu% (CDU %ncdu%)"
    )
    valido, erros = msg1.validar()
    if valido:
        print(f"Mensagem 1001 OK:\n{msg1.serializar()}")
    else:
        print(f"Erro na msg 1001: {erros}")

    msg2 = MensagemPersonalizada(
        lc=1002,
        texto="ALERTA: Transicao %trns% em %vent% (bloco %nb%)"
    )
    valido, erros = msg2.validar()
    if valido:
        print(f"Mensagem 1002 OK:\n{msg2.serializar()}")
    else:
        print(f"Erro na msg 1002: {erros}")

    # Erro intencional: coringa inválido
    print("\nTestando coringa inválido:")
    msg_erro = MensagemPersonalizada(
        lc=1003,
        texto="Sinal %invalido% causou problema"
    )
    valido, erros = msg_erro.validar()
    if not valido:
        print(f"  Erro esperado detectado: {erros}")

    # Blocos ALERTA
    print("\n--- BLOCOS ALERTA ---")
    alerta1 = BlocoAlerta(
        nome="Alerta_Subtensao",
        entrada="condicao_tensao_baixa",
        p1=1001,  # usa DMSG 1001 para transição 0->1
        p2=0      # usa mensagem padrão para transição 1->0
    )
    valido, msg_erro = alerta1.validar()
    if valido:
        print(f"Bloco ALERTA criado:\n{alerta1.serializar_bloco_cdu()}")
    else:
        print(f"Erro: {msg_erro}")

    # Algoritmos OTMx
    print("--- ALGORITMOS OTMx (Detecção Malha Inativa) ---")
    otmx = AlgoritmoOTM(tipo="OTMX", ativo=True, gerar_relatorio=True)
    valido, msg = otmx.validar()
    if valido:
        print(f"Algoritmo {otmx.tipo} configurado:\n{otmx.serializar_opcao()}")
        print("Benefícios:")
        print("  • Desliga blocos certamente inativos (ramos com lógicas desabilitadas)")
        print("  • Melhora performance: ~10-15% mais rápido em sistemas completos")
        print("  • Reduz uso de memória: detecta 5K-20K blocos inativos")
        print("  • Recomendado para uso cotidiano (v11.5+)")

    # Combinação completa: Relé com alertas + otimização
    print("\n" + "-" * 70)
    print("Exemplo Completo: Relé com Alertas e Otimização")
    print("-" * 70)
    print("\nSegunda-feira (Caso Reduzido):")
    print(f"  • Blocos: 49.704")
    print(f"  • Sem OTM: 6min 36s")
    print(f"  • Com OTMX: 6min 30s (1.5% mais rápido)")
    print(f"  • Blocos desligados: 5.066 (10%)")
    print("\nCaso Completo (SIN com Eólica + Solar):")
    print(f"  • Blocos: 128.512")
    print(f"  • Sem OTM: 17min 36s")
    print(f"  • Com OTMX: 15min 34s (13% mais rápido)")
    print(f"  • Blocos desligados: 19.812 (15%)")
