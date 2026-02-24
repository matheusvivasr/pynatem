"""
caso.py – Objeto principal do pyanatem.

CasoAnatem representa um arquivo STB completo como grafo de blocos
serializáveis. A serialização produz o texto exato esperado pelo ANATEM.

Ordem dos blocos no STB:
    ( comentário
    DOPC   – opções globais (opcional)
    DARQ   – arquivos associados
    DMDG   – modelos de geradores (opcional)
    DMAQ   – associação máquina↔modelo (opcional)
    SVC    – Compensadores Estáticos de Reativos (opcional)
    TCSC   – Compensadores Série Controlados a Tiristor (opcional)
    STATCOM – Compensadores Estáticos de Reativos VSC (opcional)
    HVDC   – Conversores CA-CC de elos LCC / DCNV (opcional)
    DELO   – Associação de elos CC / DELO (opcional)
    DEVT   – eventos
    DPLT   – variáveis de plotagem
    DSIM   – parâmetros de simulação
    EXSI   – executa
    FIM    – fim do deck
"""

from __future__ import annotations
from copy import deepcopy
from pathlib import Path
from typing import List, Optional, Union
from pathlib import Path as _Path

from .blocos import (
    BlocoDOPC,
    BlocoDARQ,
    BlocoDSIM,
    BlocoDEVT,
    BlocoDPLT,
    BlocoDMAQ,
    BlocoDMDG,
    BlocoDRGT,
    BlocoDRGV,
    BlocoDEST,
    BlocoDCST,
    BlocoDCAG,
    BlocoDCCT,
    BlocoDCAR,
    BlocoDGER,
    BlocoDMTC,
    BlocoDLTC,
    BlocoDFLA,
    BlocoDMOT,
    BlocoEXSI,
    BlocoSVC,
    BlocoTCSC,
    BlocoSTATCOM,
    BlocoHVDC,
    BlocoDELO,
    BlocoDDFM,
)


def _verificar_latin1(texto: str, origem: str) -> None:
    """Valida que ``texto`` é representável em latin-1 (padrão ANATEM).

    Levanta ``ValueError`` descritivo apontando o caractere ofensor e a
    linha do deck em que ele aparece, em vez de deixar o ``UnicodeEncodeError``
    obscuro chegar ao usuário.
    """
    try:
        texto.encode("latin-1")
    except UnicodeEncodeError as e:
        char = texto[e.start]
        n_linha = texto.count("\n", 0, e.start) + 1
        ini = texto.rfind("\n", 0, e.start) + 1
        fim = texto.find("\n", e.start)
        linha = texto[ini : fim if fim != -1 else len(texto)]
        raise ValueError(
            f"{origem}: o caractere {char!r} (U+{ord(char):04X}) não é "
            f"representável em latin-1, a codificação exigida pelo ANATEM. "
            f"Ele aparece na linha {n_linha} do deck: {linha.rstrip()!r}. "
            f"Substitua-o por um equivalente latin-1 no campo correspondente "
            f"(ex.: título, nomes de arquivo)."
        ) from e


class CasoAnatem:
    """Representa um caso completo do ANATEM (arquivo .stb).

    Uso básico::

        caso = CasoAnatem()
        caso.darq.sav  = "rede.sav"
        caso.darq.plt  = "saida.plt"
        caso.dsim.tfim = 10.0
        caso.curto_barra(barra=5, t_apl=1.0, t_rem=1.1)
        caso.dplt.tensao_barra(5)
        caso.dplt.angulo_maquina(5, unidade=1)
        caso.exportar("meu_caso.stb")
    """

    def __init__(self) -> None:
        self.dopc = BlocoDOPC()
        self.darq = BlocoDARQ()
        self.dcst = BlocoDCST()
        self.dmdg = BlocoDMDG()
        self.drgt = BlocoDRGT()
        self.drgv = BlocoDRGV()
        self.dest = BlocoDEST()
        self.dmaq = BlocoDMAQ()
        self.dcag = BlocoDCAG()
        self.dcct = BlocoDCCT()
        self.dcar = BlocoDCAR()
        self.dger = BlocoDGER()
        self.dmtc = BlocoDMTC()
        self.dltc = BlocoDLTC()
        self.dfla = BlocoDFLA()
        self.dmot = BlocoDMOT()
        self.svc = BlocoSVC()
        self.tcsc = BlocoTCSC()
        self.statcom = BlocoSTATCOM()
        self.hvdc = BlocoHVDC()
        self.delo = BlocoDELO()
        self.ddfm = BlocoDDFM()
        self.devt = BlocoDEVT()
        self.dplt = BlocoDPLT()
        self.dsim = BlocoDSIM()
        self._titulo: Optional[str] = None

        # BlocoDCDU é importado aqui para evitar importação circular no topo
        from .cdu import BlocoDCDU as _BlocoDCDU

        self.dcdu = _BlocoDCDU()

    @property
    def titulo(self) -> Optional[str]:
        return self._titulo

    @titulo.setter
    def titulo(self, v: str) -> None:
        self._titulo = v

    # ------------------------------------------------------------------
    # API de alto nível – eventos compostos
    # ------------------------------------------------------------------

    def curto_barra(
        self,
        barra: int,
        t_apl: float,
        t_rem: float,
        r_falta: float = 0.0,
        x_falta: float = 0.0,
    ) -> "CasoAnatem":
        """Aplica e remove curto-circuito em barra CA (APCB + RMCB)."""
        self.devt.curto_barra(
            barra=barra, tini=t_apl, tipo="APCB", r=r_falta, x=x_falta
        )
        self.devt.curto_barra(barra=barra, tini=t_rem, tipo="RMCB")
        return self

    def curto_circuito(
        self,
        de: int,
        para: int,
        circ: int,
        t_apl: float,
        t_rem: float,
        r_falta: float = 0.0,
        x_falta: float = 0.0,
    ) -> "CasoAnatem":
        """Aplica e remove curto-circuito em circuito CA (APCC + RMCC)."""
        self.devt.curto_circuito(
            de=de, para=para, circ=circ, tini=t_apl, tipo="APCC", r=r_falta, x=x_falta
        )
        self.devt.curto_circuito(de=de, para=para, circ=circ, tini=t_rem, tipo="RMCC")
        return self

    def adicionar_maquina(
        self,
        barra: int,
        grupo: int,
        p: Optional[int] = None,
        q: Optional[int] = None,
        und: Optional[int] = None,
        mg: Optional[int] = None,
        mt: Optional[int] = None,
        mt_cdu: bool = False,
        mv: Optional[int] = None,
        mv_cdu: bool = False,
        me: Optional[int] = None,
        me_cdu: bool = False,
        xvd: Optional[float] = None,
        nbc: Optional[int] = None,
    ) -> "CasoAnatem":
        """Associa uma máquina síncrona a modelos dinâmicos (DMAQ).

        Atalho para ``self.dmaq.adicionar_maquina()``.
        Veja :class:`~pyanatem.blocos.BlocoDMAQ` para descrição dos parâmetros.
        """
        self.dmaq.adicionar_maquina(
            barra=barra,
            grupo=grupo,
            p=p,
            q=q,
            und=und,
            mg=mg,
            mt=mt,
            mt_cdu=mt_cdu,
            mv=mv,
            mv_cdu=mv_cdu,
            me=me,
            me_cdu=me_cdu,
            xvd=xvd,
            nbc=nbc,
        )
        return self

    def abrir_linha(
        self, de: int, para: int, t_aber: float, circ: int = 1
    ) -> "CasoAnatem":
        """Abertura de circuito CA (ABLN)."""
        self.devt.abertura_linha(de=de, para=para, tini=t_aber, circ=circ)
        return self

    def abrir_linha_e_fechar(
        self, de: int, para: int, t_aber: float, t_fech: float, circ: int = 1
    ) -> "CasoAnatem":
        """Abre e religa circuito CA (ABLN + FCLN)."""
        self.devt.abertura_linha(de=de, para=para, tini=t_aber, circ=circ)
        self.devt.fechamento_linha(de=de, para=para, tini=t_fech, circ=circ)
        return self

    def alterar_dsim(self, **kwargs: object) -> "CasoAnatem":
        """Atualiza parâmetros de simulação (levanta AttributeError se inválido)."""
        for k, v in kwargs.items():
            if not hasattr(self.dsim, k):
                raise AttributeError(f"BlocoDSIM não tem atributo '{k}'")
            setattr(self.dsim, k, v)
        return self

    # ------------------------------------------------------------------
    # Serialização
    # ------------------------------------------------------------------

    def deck(self) -> str:
        """Gera o texto completo do arquivo STB."""
        partes: List[str] = []

        partes.append(
            f"( {self._titulo}\n" if self._titulo else "( Gerado por pyanatem\n"
        )

        if self._titulo:
            partes.append(f"TITU\n{self._titulo}\n999999\n")

        if self.dopc.tem_dados():
            partes.append(self.dopc.serializar())

        partes.append(self.darq.serializar())

        # Curvas de saturação (referenciadas pelo campo Cs do DMDG/DRGT)
        if self.dcst.tem_dados():
            partes.append(self.dcst.serializar())

        if self.dmdg.tem_dados():
            partes.append(self.dmdg.serializar())

        # Modelos predefinidos de controle (antes do DMAQ, que os associa)
        if self.drgt.tem_dados():
            partes.append(self.drgt.serializar())
        if self.drgv.tem_dados():
            partes.append(self.drgv.serializar())
        if self.dest.tem_dados():
            partes.append(self.dest.serializar())

        if self.dmaq.tem_dados():
            partes.append(self.dmaq.serializar())

        # Associação de controles de área (CAG/CCT) a modelos CDU
        if self.dcag.tem_dados():
            partes.append(self.dcag.serializar())
        if self.dcct.tem_dados():
            partes.append(self.dcct.serializar())

        # Cargas e geração funcionais (modelo ZIP por tensão)
        if self.dcar.tem_dados():
            partes.append(self.dcar.serializar())
        if self.dger.tem_dados():
            partes.append(self.dger.serializar())

        # Transformadores OLTC: modelo de controle (DMTC) + associação (DLTC)
        if self.dmtc.tem_dados():
            partes.append(self.dmtc.serializar())
        if self.dltc.tem_dados():
            partes.append(self.dltc.serializar())

        # Fluxo agregado de intercâmbio (áreas de circuitos)
        if self.dfla.tem_dados():
            partes.append(self.dfla.serializar())

        # Máquinas de indução convencional
        if self.dmot.tem_dados():
            partes.append(self.dmot.serializar())

        # Blocos FACTS/HVDC — emitidos entre DMAQ e DEVT quando populados
        if self.svc.tem_dados():
            partes.append(self.svc.serializar())
        if self.tcsc.tem_dados():
            partes.append(self.tcsc.serializar())
        if self.statcom.tem_dados():
            partes.append(self.statcom.serializar())
        if self.hvdc.tem_dados():
            partes.append(self.hvdc.serializar())
        if self.delo.tem_dados():
            partes.append(self.delo.serializar())

        # Geradores eólicos DFIG
        if self.ddfm.tem_dados():
            partes.append(self.ddfm.serializar())

        partes.append(self.devt.serializar())
        partes.append(self.dplt.serializar())
        partes.append(self.dsim.serializar())

        partes.append(BlocoEXSI().serializar())
        partes.append("FIM\n")

        return "\n".join(partes)

    def salvar_cdu(self, caminho: Union[str, Path]) -> Path:
        """Serializa o BlocoDCDU deste caso para um arquivo .cdu.

        O arquivo gerado é normalmente referenciado via ``caso.darq``
        usando ``caso.darq.adicionar_cdu(str(caminho))``.

        Args:
            caminho: caminho do arquivo .cdu a ser gravado.

        Returns:
            Caminho absoluto do arquivo gravado.
        """
        caminho = Path(caminho)
        caminho.parent.mkdir(parents=True, exist_ok=True)
        texto = self.dcdu.serializar()
        _verificar_latin1(texto, "salvar_cdu()")
        caminho.write_text(texto, encoding="latin-1")
        return caminho

    def exportar(self, caminho: Union[str, Path]) -> Path:
        """Salva o deck em disco (encoding latin-1, padrão ANATEM).

        Raises:
            ValueError: se algum campo de texto (título, nomes de arquivo…)
                contiver caractere não representável em latin-1; a mensagem
                identifica o caractere e a linha do deck.
        """
        caminho = Path(caminho)
        caminho.parent.mkdir(parents=True, exist_ok=True)
        texto = self.deck()
        _verificar_latin1(texto, "exportar()")
        caminho.write_text(texto, encoding="latin-1")
        return caminho

    @classmethod
    def ler(cls, caminho: Union[str, Path]) -> "CasoAnatem":
        """Lê um arquivo STB existente e retorna um CasoAnatem populado."""
        from .parser.stb import ParserSTB

        return ParserSTB.ler(caminho)

    def copiar(self) -> "CasoAnatem":
        """Retorna cópia profunda independente deste caso."""
        return deepcopy(self)

    # ------------------------------------------------------------------
    # Validação
    # ------------------------------------------------------------------

    def validar(self) -> List[str]:
        """Verifica consistência mínima do caso.

        Checagens:
            1. Arquivo SAV definido.
            2. tfim > tini.
            3. delt > 0.
            4. delt não excessivamente grande em termos absolutos (> 0.02s).
            5. Número mínimo de passos de integração (heurística: < 50 passos
               totais indica resolução temporal provavelmente grosseira
               demais para a dinâmica eletromecânica).
            6. Todo APCB tem RMCB correspondente na mesma barra.
            7. Eventos possivelmente sobrepostos: dois eventos diferentes
               no mesmo instante para o mesmo alvo (barra/circuito).
            8. Nenhum evento ocorre depois de tfim (não seria executado).

        Returns:
            Lista de avisos/erros. Lista vazia significa caso válido.
        """
        erros: List[str] = []

        if not self.darq.sav:
            erros.append("DARQ: arquivo SAV (caso de rede) não definido.")

        if self.dsim.tfim <= self.dsim.tini:
            erros.append(
                f"DSIM: tfim ({self.dsim.tfim}) deve ser maior que tini ({self.dsim.tini})."
            )

        if self.dsim.delt <= 0:
            erros.append(f"DSIM: delt ({self.dsim.delt}) deve ser positivo.")
        else:
            if self.dsim.delt > 0.02:
                erros.append(
                    f"DSIM: delt ({self.dsim.delt}s) maior que 0.02s pode causar "
                    "instabilidade numérica."
                )

            duracao = self.dsim.tfim - self.dsim.tini
            if duracao > 0:
                n_passos = duracao / self.dsim.delt
                if n_passos < 50:
                    erros.append(
                        f"DSIM: apenas {n_passos:.0f} passos de integração no período "
                        f"simulado ({duracao}s / {self.dsim.delt}s) — resolução temporal "
                        "pode ser grosseira demais para capturar a dinâmica eletromecânica."
                    )

        # 6. APCB sem RMCB correspondente
        apcb = set()
        for ev in self.devt._eventos:
            if ev.codigo == "APCB":
                apcb.add(ev.nb1)
            elif ev.codigo == "RMCB":
                apcb.discard(ev.nb1)
        for b in apcb:
            erros.append(f"DEVT: curto APCB na barra {b} sem RMCB correspondente.")

        # 7. eventos possivelmente sobrepostos (mesmo alvo, mesmo instante, ação diferente)
        vistos: dict = {}
        for ev in self.devt._eventos:
            chave = (ev.nb1, ev.nb2, ev.nc, round(ev.tini, 6))
            if chave in vistos and vistos[chave] != ev.codigo:
                erros.append(
                    f"DEVT: eventos '{vistos[chave]}' e '{ev.codigo}' no mesmo instante "
                    f"t={ev.tini}s para o mesmo alvo (nó {ev.nb1}) — verifique a ordem "
                    "de execução esperada."
                )
            vistos[chave] = ev.codigo

        # 8. evento depois de tfim
        if self.devt._eventos:
            ultimo_tini = max(ev.tini for ev in self.devt._eventos)
            if ultimo_tini > self.dsim.tfim:
                erros.append(
                    f"DEVT: evento em t={ultimo_tini}s ocorre depois de "
                    f"tfim={self.dsim.tfim}s e não será executado pela simulação."
                )

        # 9. validação cruzada DMAQ ↔ DMDG
        # Coleta os números de modelo predefinidos declarados no DMDG
        modelos_dmdg = {
            m.no for m in self.dmdg._md01 + self.dmdg._md02 + self.dmdg._md03
        }

        for assoc in self.dmaq.associacoes:
            # mg — modelo de gerador (sempre predefinido no DMDG, nunca CDU)
            if assoc.mg is not None and assoc.mg not in modelos_dmdg:
                erros.append(
                    f"DMAQ: barra {assoc.barra} grupo {assoc.grupo} referencia modelo de "
                    f"gerador mg={assoc.mg} que não está definido no DMDG."
                )
            # mt — modelo de turbina/regulador de velocidade (predefinido quando mt_cdu=False)
            if (
                assoc.mt is not None
                and not assoc.mt_cdu
                and assoc.mt not in modelos_dmdg
            ):
                erros.append(
                    f"DMAQ: barra {assoc.barra} grupo {assoc.grupo} referencia modelo de "
                    f"turbina mt={assoc.mt} (predefinido) que não está definido no DMDG."
                )
            # mv — modelo de regulador de tensão (predefinido quando mv_cdu=False)
            if (
                assoc.mv is not None
                and not assoc.mv_cdu
                and assoc.mv not in modelos_dmdg
            ):
                erros.append(
                    f"DMAQ: barra {assoc.barra} grupo {assoc.grupo} referencia modelo de "
                    f"regulador mv={assoc.mv} (predefinido) que não está definido no DMDG."
                )
            # me — modelo de estabilizador (predefinido quando me_cdu=False)
            if (
                assoc.me is not None
                and not assoc.me_cdu
                and assoc.me not in modelos_dmdg
            ):
                erros.append(
                    f"DMAQ: barra {assoc.barra} grupo {assoc.grupo} referencia modelo de "
                    f"estabilizador me={assoc.me} (predefinido) que não está definido no DMDG."
                )

        return erros

    def validar_contra_sav(self, path_sav: Union[str, _Path]) -> List[str]:
        """Cruza barras/circuitos do STB com os presentes no SAV do ANAREDE.

        Args:
            path_sav: caminho do arquivo .sav.

        Returns:
            Lista de inconsistências. Vazia = tudo OK.
        """
        from .anarede import validar_contra_sav

        return validar_contra_sav(self, path_sav)

    def __repr__(self) -> str:
        n_ev = len(self.devt._eventos) + len(self.devt._linhas_brutas)
        n_plt = len(self.dplt.linhas)
        return (
            f"CasoAnatem(sav={self.darq.sav!r}, tfim={self.dsim.tfim}, "
            f"delt={self.dsim.delt}, eventos={n_ev}, variaveis={n_plt})"
        )
