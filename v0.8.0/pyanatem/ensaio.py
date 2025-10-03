"""
ensaio.py – Automação de ensaios eletromecânicos com o ANATEM.

Fluxo típico:
    1. Carrega template STB existente.
    2. Cria N variações (cenários) modificando eventos, plotagem e DSIM.
    3. Exporta cada variação como .stb.
    4. Executa o ANATEM para cada arquivo (sequencial ou paralelo).
"""

from __future__ import annotations
import copy
import glob
import subprocess
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from typing import Callable, Dict, Iterable, List, Optional, Union

from .caso import CasoAnatem


def _executar_um(args):
    """Worker para execução paralela (ProcessPoolExecutor)."""
    exe, stb, timeout, capturar = args
    cmd = [exe, str(stb)]
    return subprocess.run(
        cmd, capture_output=capturar, text=True, timeout=timeout,
        cwd=str(Path(stb).parent),
    )


class EnsaioAnatem:
    """Gerencia um conjunto de casos derivados de um template STB."""

    def __init__(self, template: Optional[CasoAnatem] = None, anatem_exe: Optional[str] = None):
        self._template = template or CasoAnatem()
        self.anatem_exe: Optional[str] = anatem_exe
        self._casos: Dict[str, CasoAnatem] = {}

    @classmethod
    def de_template(cls, caminho: Union[str, Path], anatem_exe: Optional[str] = None) -> "EnsaioAnatem":
        """Cria EnsaioAnatem a partir de um STB existente."""
        template = CasoAnatem.ler(caminho)
        return cls(template=template, anatem_exe=anatem_exe)

    @classmethod
    def novo(cls, anatem_exe: Optional[str] = None) -> "EnsaioAnatem":
        """Cria EnsaioAnatem com template em branco."""
        return cls(template=CasoAnatem(), anatem_exe=anatem_exe)

    @property
    def template(self) -> CasoAnatem:
        return self._template

    def configurar_template(self, **kwargs) -> "EnsaioAnatem":
        """Atalho para alterar_dsim no template."""
        self._template.alterar_dsim(**kwargs)
        return self

    def novo_caso(self, nome: str) -> CasoAnatem:
        """Cria um novo caso copiando o template."""
        caso = copy.deepcopy(self._template)
        self._casos[nome] = caso
        return caso

    def casos(self) -> Dict[str, CasoAnatem]:
        return dict(self._casos)

    def exportar_todos(self, diretorio: Union[str, Path] = ".") -> List[Path]:
        """Exporta todos os casos criados via novo_caso()."""
        diretorio = Path(diretorio)
        diretorio.mkdir(parents=True, exist_ok=True)
        paths = []
        for nome, caso in self._casos.items():
            p = diretorio / f"{nome}.stb"
            caso.exportar(p)
            paths.append(p)
        return paths

    def gerar_variacoes(self, modificador: Callable[[CasoAnatem, int], None], n: int,
                         diretorio: Union[str, Path] = ".", prefixo: str = "caso") -> List[Path]:
        """Gera N variações aplicando uma função modificadora."""
        diretorio = Path(diretorio)
        diretorio.mkdir(parents=True, exist_ok=True)
        paths = []
        for i in range(n):
            caso = copy.deepcopy(self._template)
            modificador(caso, i)
            nome = f"{prefixo}_{i:04d}"
            self._casos[nome] = caso
            p = diretorio / f"{nome}.stb"
            caso.exportar(p)
            paths.append(p)
        return paths

    def executar(self, caminho_stb: Union[str, Path], anatem_exe: Optional[str] = None,
                 timeout: Optional[int] = None, capturar_saida: bool = True) -> subprocess.CompletedProcess:
        """Executa o ANATEM para um único arquivo STB."""
        exe = anatem_exe or self.anatem_exe
        if not exe:
            raise RuntimeError(
                "Executável do ANATEM não configurado. "
                "Defina EnsaioAnatem.anatem_exe ou passe anatem_exe= como argumento."
            )
        caminho_stb = Path(caminho_stb)
        cmd = [exe, str(caminho_stb)]
        return subprocess.run(
            cmd, capture_output=capturar_saida, text=True, timeout=timeout,
            cwd=str(caminho_stb.parent),
        )

    def executar_lote(self, arquivos: Union[str, Iterable[Union[str, Path]]],
                       anatem_exe: Optional[str] = None, timeout: Optional[int] = None,
                       parar_em_erro: bool = False) -> List[subprocess.CompletedProcess]:
        """Executa o ANATEM para múltiplos STBs sequencialmente."""
        lista = self._resolver_arquivos(arquivos)
        resultados = []
        for stb in lista:
            r = self.executar(stb, anatem_exe=anatem_exe, timeout=timeout)
            resultados.append(r)
            if parar_em_erro and r.returncode != 0:
                raise RuntimeError(
                    f"ANATEM falhou em {stb} (returncode={r.returncode})\nstderr:\n{r.stderr}"
                )
        return resultados

    def executar_paralelo(self, arquivos: Union[str, Iterable[Union[str, Path]]],
                           anatem_exe: Optional[str] = None, timeout: Optional[int] = None,
                           max_workers: Optional[int] = None) -> List[subprocess.CompletedProcess]:
        """Executa o ANATEM para múltiplos STBs em paralelo (ordem preservada)."""
        exe = anatem_exe or self.anatem_exe
        if not exe:
            raise RuntimeError("Executável do ANATEM não configurado.")

        lista = self._resolver_arquivos(arquivos)
        args = [(exe, str(stb), timeout, True) for stb in lista]

        resultados_map: Dict[int, subprocess.CompletedProcess] = {}
        with ProcessPoolExecutor(max_workers=max_workers) as pool:
            futuros = {pool.submit(_executar_um, a): idx for idx, a in enumerate(args)}
            for fut in as_completed(futuros):
                idx = futuros[fut]
                try:
                    resultados_map[idx] = fut.result()
                except Exception as e:
                    resultados_map[idx] = subprocess.CompletedProcess(
                        args=args[idx][0:2], returncode=-1, stdout="", stderr=str(e),
                    )
        return [resultados_map[i] for i in range(len(lista))]

    @staticmethod
    def _resolver_arquivos(arquivos: Union[str, Iterable]) -> List[Path]:
        if isinstance(arquivos, str):
            return [Path(p) for p in sorted(glob.glob(arquivos))]
        return [Path(p) for p in arquivos]

    # ------------------------------------------------------------------
    # Etapa 4.6 – Análise de contingências automatizada
    # ------------------------------------------------------------------

    @classmethod
    def de_contingencias(
        cls,
        caso_base: CasoAnatem,
        lista_contingencias: List[dict],
        anatem_exe: Optional[str] = None,
    ) -> "EnsaioAnatem":
        """Gera automaticamente um caso por contingência a partir de um caso-base.

        Cada contingência é um dict com as chaves:
            - ``nome``  (str): identificador único, usado no nome do arquivo
            - ``tipo``  (str): ``"curto_barra"``, ``"abertura_linha"`` ou ``"step"``
            - Parâmetros dependentes do tipo (ver exemplos abaixo)

        Para ``tipo="curto_barra"``:
            ``barra`` (int), ``t_apl`` (float), ``t_rem`` (float),
            ``r_falta`` (float, default 0), ``x_falta`` (float, default 0)

        Para ``tipo="abertura_linha"``:
            ``de`` (int), ``para`` (int), ``t_aber`` (float),
            ``t_fech`` (float, opcional), ``circ`` (int, default 1)

        Para ``tipo="step"``:
            ``barra`` (int), ``unidade`` (int), ``t_ini`` (float), ``delta`` (float)

        Args:
            caso_base:          template base para todas as contingências.
            lista_contingencias: lista de dicts descrevendo as contingências.
            anatem_exe:         caminho do executável ANATEM.

        Returns:
            EnsaioAnatem com todos os casos criados.
        """
        ensaio = cls(template=caso_base, anatem_exe=anatem_exe)
        for cont in lista_contingencias:
            nome = cont.get("nome", f"cont_{len(ensaio._casos):04d}")
            caso = ensaio.novo_caso(nome)
            tipo = cont.get("tipo", "")

            if tipo == "curto_barra":
                caso.curto_barra(
                    barra=cont["barra"],
                    t_apl=cont["t_apl"],
                    t_rem=cont["t_rem"],
                    r_falta=cont.get("r_falta", 0.0),
                    x_falta=cont.get("x_falta", 0.0),
                )
            elif tipo == "abertura_linha":
                if "t_fech" in cont:
                    caso.abrir_linha_e_fechar(
                        de=cont["de"], para=cont["para"],
                        t_aber=cont["t_aber"], t_fech=cont["t_fech"],
                        circ=cont.get("circ", 1),
                    )
                else:
                    caso.abrir_linha(
                        de=cont["de"], para=cont["para"],
                        t_aber=cont["t_aber"], circ=cont.get("circ", 1),
                    )
            elif tipo == "step":
                caso.devt.step_referencia(
                    barra=cont["barra"], unidade=cont.get("unidade", 1),
                    tini=cont["t_ini"], delta=cont["delta"],
                )
            # tipo desconhecido: caso gerado sem eventos adicionais

        return ensaio

    def executar_contingencias(
        self,
        paths: List[Path],
        criterios: Optional[dict] = None,
        anatem_exe: Optional[str] = None,
        timeout: Optional[int] = None,
    ) -> List[dict]:
        """Executa lote de contingências e verifica critérios básicos.

        O caminho do arquivo de relatório é determinado da seguinte forma:

        1. Se ``self._template.darq.rela`` estiver definido, o relatório é
           procurado no mesmo diretório do arquivo .stb, com o nome declarado
           em ``darq.rela``.
        2. Caso contrário, o caminho é derivado substituindo a extensão do
           arquivo .stb por ``.rela`` (comportamento legado).

        Args:
            paths:      lista de arquivos .stb a executar.
            criterios:  dict de critérios (``"convergencia": True`` exige convergência).
            anatem_exe: executável ANATEM (sobrepõe o configurado no ensaio).
            timeout:    timeout por caso em segundos.

        Returns:
            Lista de dicts com: ``arquivo``, ``convergiu``, ``erros``, ``avisos``,
            ``passou`` (bool — atende todos os critérios).
        """
        from .posprocessamento import LeitorRelatorio
        criterios = criterios or {}
        resultados = []

        for path in paths:
            path = Path(path)
            # Determina caminho do relatório: darq.rela tem precedência
            rela_declarado = getattr(self._template.darq, "rela", None)
            if rela_declarado:
                rela_path = path.parent / Path(rela_declarado).name
            else:
                rela_path = path.with_suffix(".rela")

            # Executa o ANATEM
            try:
                proc = self.executar(path, anatem_exe=anatem_exe, timeout=timeout)
                returncode = proc.returncode
            except Exception as e:
                resultados.append({
                    "arquivo": str(path),
                    "convergiu": False,
                    "erros": [str(e)],
                    "avisos": [],
                    "passou": False,
                    "returncode": -1,
                })
                continue

            # Lê o relatório se existir
            convergiu = None
            erros: List[str] = []
            avisos: List[str] = []
            if rela_path.exists():
                rel = LeitorRelatorio.ler(rela_path)
                convergiu = rel.convergiu
                erros = rel.erros
                avisos = rel.avisos
            else:
                convergiu = returncode == 0

            # Verifica critérios
            passou = True
            if criterios.get("convergencia", False) and convergiu is not True:
                passou = False

            resultados.append({
                "arquivo": str(path),
                "convergiu": convergiu,
                "erros": erros,
                "avisos": avisos,
                "passou": passou,
                "returncode": returncode,
            })

        return resultados

    def relatorio_consolidado(self, resultados: List[dict]) -> str:
        """Gera tabela de resultados de contingências como string formatada."""
        linhas = ["Contingência".ljust(40) + "Convergiu  Passou  Erros"]
        linhas.append("-" * 70)
        for r in resultados:
            nome = Path(r["arquivo"]).stem[:38]
            conv = "Sim" if r.get("convergiu") else ("Não" if r.get("convergiu") is False else "?")
            passou = "Sim" if r.get("passou") else "Não"
            nerros = len(r.get("erros", []))
            linhas.append(f"{nome:<40}{conv:<11}{passou:<8}{nerros}")
        linhas.append("-" * 70)
        n_ok = sum(1 for r in resultados if r.get("passou"))
        linhas.append(f"Total: {len(resultados)} contingências — {n_ok} passaram.")
        return "\n".join(linhas)

    def __repr__(self) -> str:
        return (
            f"EnsaioAnatem(template={self._template!r}, "
            f"casos={len(self._casos)}, exe={self.anatem_exe!r})"
        )
