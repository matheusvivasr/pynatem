# Changelog

Todas as mudanças notáveis estão documentadas aqui.

## [1.3.2] — 2026-07-10 — Bancos Shunt: evento MDSH + plotagem

> Segundo patch da etapa **v1.3**. Escopo corrigido: **não existe código `DBSH`**
> — os bancos shunt são dados do ANAREDE (importados do fluxo de potência). No
> lado ANATEM o que existe são eventos e variáveis de plotagem.

### Added

- **Evento MDSH** (§12.1) em `BlocoDEVT.modificacao_shunt(barra, tini, valor)` —
  modificação de shunt equivalente (variação absoluta). Reconhecido pelo parser.
- **Plotagem de shunt** (§12.2) em `BlocoDPLT`: `reativo_shunt` (QSHT, shunt
  equivalente), `shunt_individualizado` (QBSH), `unidades_shunt` (NUBSH).
- 2 testes novos (plotagem shunt + roundtrip do evento MDSH). Total: 239 testes.

### Notas

- A meta original "Bancos Shunt (DBSH)" do roadmap partia de premissa falsa (não
  há tal código). Entregue o que é real: evento MDSH + plotagem. A definição do
  banco em si é feita no ANAREDE (ver LeitorSAV).

## [1.3.1] — 2026-07-10 — Cargas estáticas funcionais (DCAR)

> Primeiro patch da etapa **v1.3 (Cargas, Shunt, OLTC e Circuitos)**.

### Added

- **`BlocoDCAR`** (§46.14) — Cargas estáticas funcionais (modelo ZIP por
  tensão). Parâmetros `A/B` (parcela ativa ~ V / V²), `C/D` (reativa ~ V / V²)
  e `Vmn` (tensão abaixo da qual vira Z constante), estruturados e validados.
  Exposto em `CasoAnatem.dcar`; emitido no deck; parser preserva a linha.
- 2 testes novos (serialização, roundtrip com opções de cabeçalho). Total: 237.

### Notas

- Confiabilidade **Média**: os parâmetros do modelo de carga são estruturados,
  mas a *linguagem de seleção* (Cap. 42) que escolhe as barras alvo é tratada
  como string opaca e preservada bruta no roundtrip (parsing estruturado da
  seleção fica para o roadmap A43 / v1.9.2).

## [1.2.6] — 2026-07-10 — CAG + Controle Centralizado de Tensão — fecha a etapa v1.2 🎉

> Último patch da etapa **v1.2 (Máquina Síncrona Completa)**. Com ele, toda a
> cadeia de modelagem da máquina síncrona está disponível.

### Added

- **`BlocoDCAG`** (§46.13, §16.7) — associação de Controle Automático de Geração
  (CAG) ao seu modelo CDU. Régua `Nc Mc[U]`.
- **`BlocoDCCT`** (§46.15, §16.8) — associação de Controle Centralizado de
  Tensão (CCT) ao seu modelo CDU. Régua `Nc Mc[U]`.
- Ambos herdam de `_BlocoAssocCDU` (base para códigos de associação de controle
  de área a CDU). CAG e CCT só têm modelo por CDU (não há predefinidos).
- Expostos em `CasoAnatem.dcag`/`.dcct`; emitidos no deck após o DMAQ. Parser
  usa `_ler_assoc_cdu`. Roundtrip garantido.
- 2 testes novos (exemplo do manual + roundtrip de ambos). Total: 235 testes.

### Notas

- CAG (v1.2.6) e CCT (v1.2.7 no roadmap) foram entregues juntos — são códigos de
  associação idênticos e triviais. Isto **conclui a etapa v1.2**: o usuário já
  pode modelar uma máquina síncrona completa (curva de saturação + regulador de
  tensão + regulador de velocidade + PSS) e controles de área (CAG/CCT).

## [1.2.5] — 2026-07-10 — Curvas de saturação de máquina (DCST)

> Patch da etapa **v1.2 (Máquina Síncrona Completa)**. Completa a cadeia de
> modelagem da máquina: curva de saturação + os 3 tipos de regulador.
> (A versão 1.2.4 foi omitida — o item "modelos de máquina MD04–MD24" era N/A,
> pois o DMDG só tem 3 modelos, todos já implementados; ver ROADMAP.)

### Added

- **`BlocoDCST`** (§16.2) — Modelos de Curva de Saturação de máquina síncrona.
  Bloco plano com régua `Nc, Tipo, P1, P2, P3` (4 tipos: exponencial com
  descontinuidade, exponencial, linear, linear por partes). Cada curva é
  identificada por `Nc` e referenciada pelo campo `Cs` do DMDG/DRGT.
- Exposto em `CasoAnatem.dcst`; emitido no deck **antes** do DMDG (que a
  referencia). Parser lê `DCST`. Roundtrip garantido.
- 3 testes novos (serialização, roundtrip, ordem no deck). Total: 233 testes.

### Notas

- CAG (Controle Automático de Geração) e Controle Centralizado de Tensão, que o
  roadmap agrupava neste patch, foram **separados** em v1.2.6 e v1.2.7 (são
  esquemas de controle maiores; patches focados).

## [1.2.3] — 2026-07-10 — Estabilizadores (PSS) predefinidos (DEST)

> Terceiro patch da etapa **v1.2 (Máquina Síncrona Completa)**.

### Added

- **`BlocoDEST`** (§16.5) — Modelos predefinidos de Estabilizador (PSS)
  aplicado em regulador de tensão. Cobre os **12 modelos** (MD01–MD12) via
  armazenamento genérico posicional, com roundtrip garantido.
  `adicionar_md01(...)` tem campos nomeados validados (K/T/T1/T2/T3/T4/Lmn/Lmx).
- Exposto em `CasoAnatem.dest`; emitido no deck entre DMDG e DMAQ (associação
  via campo Me). Parser lê `DEST MDxx`.
- 2 testes novos (MD01 nomeado + roundtrip com genérico). Total: 230 testes.

## [1.2.2] — 2026-07-10 — Reguladores de Velocidade/Turbina predefinidos (DRGV)

> Segundo patch da etapa **v1.2 (Máquina Síncrona Completa)**.

### Added

- **`BlocoDRGV`** (§16.4) — Modelos predefinidos de Regulador de Velocidade e
  Turbina. Cobre os **7 modelos** (MD01–MD07) via armazenamento genérico
  posicional, com roundtrip garantido. `adicionar_md01(...)` tem campos
  nomeados validados (R/Rp/At/Qnl/Tw/Tr/Tf/Tg/Lmn/Lmx/Dtb/D/Pbg/Pbt).
- Exposto em `CasoAnatem.drgv`; emitido no deck entre DMDG e DMAQ (associação
  via campo Mt). Parser lê `DRGV MDxx`.

### Changed

- Refatoração: `BlocoDRGT`/`BlocoDRGV` agora herdam de `_BlocoModeloMDxx`
  (base genérica para blocos de modelo predefinido por variante MDxx). Reduz
  duplicação e deixa DEST (v1.2.3) trivial. O parser usa `_ler_modelo_mdxx`.

### Added (cont.)

- 2 testes novos (MD01 nomeado + roundtrip com genérico). Total: 228 testes.

## [1.2.1] — 2026-07-10 — Reguladores de Tensão predefinidos (DRGT)

> Primeiro patch da etapa **v1.2 (Máquina Síncrona Completa)**. Começa a
> preencher o Inventário A (capacidades ausentes).

### Added

- **`BlocoDRGT`** (§16.3) — Modelos predefinidos de Regulador de Tensão e
  Excitatriz. Cobre os **24 modelos** (MD01–MD24) via armazenamento genérico
  posicional (No + parâmetros na ordem da régua), com roundtrip garantido.
  - `adicionar(modelo, no, *parametros)` — qualquer MDxx.
  - `adicionar_md01(...)` — construtor nomeado, validado campo a campo contra
    a régua do MD01 (Cs/Ka/Ke/Kf/Tm/Ta/Te/Tf/Lmn/Lmx/L/S).
- Exposto em `CasoAnatem.drgt`; emitido no deck entre DMDG e DMAQ (que o
  associa à máquina via campo Mv). Parser `ParserSTB` lê `DRGT MDxx`.
- 4 testes novos (MD01 nomeado, genérico multi-variante, roundtrip, ordem no
  deck). Total: 226 testes.

### Notas

- Abordagem "genérico paramétrico + MD01 nomeado" (decidida com o usuário):
  cobertura total dos 24 modelos com risco baixo; o MD01 tem API ergonômica.
  Demais modelos usam parâmetros posicionais (a régua de cada um está no §16.3).

## [1.1.5] — 2026-07-10 — DPLT 4-letra (OLTC/FACTS/HVDC/CDU) validado — fecha a etapa v1.1 🎉

> Quinto e último patch da etapa **v1.1 (Confiabilidade Máxima)**. Com ele o
> Inventário B fica zerado: todos os itens que estavam em Média/best-effort
> passaram a Alta.

### Fixed

- Mnemônicos das variáveis de plotagem DPLT de 4 letras estavam **inventados**.
  Substituídos pelos códigos e réguas reais do manual:
  - **OLTC** (§13.3.1): `TAPO` → **`TAP`** (régua De/Para/Nc).
  - **CER/SVC** (§25.4): `QSVC/VSVC/BSVC` → **`QCES/VCES/BCES/ICES`** (régua
    barra + grupo; antes só 1 identificador).
  - **CSC/TCSC** (§26.4): `XTCS/PTCS` → **`XCSC/BCSC/ICSC`** (não existe variável
    de potência; `potencia_tcsc` foi substituído por `susceptancia_tcsc`/
    `corrente_tcsc`).
  - **VSI/STATCOM** (§27.5): `QSTA/VSTA` → **`QVSI/PVSI/IMVSI/ETMVSI`**.
  - **HVDC conversor** (§24.6.1): `VCCD/ICCD/PCCD` → **`VCNV/CCNV/PCNV`** (+`QCNV`,
    `VBDC`); `ALFA`/`GAMA` já estavam corretos.
  - **CDU** (§29.10): `SCDU` → **`CDU`** (saída) e novo **`CDUE`** (estado).

### Changed

- Confiabilidade DPLT 4-letra: **Média → Alta**. Com isso, **Inventário B zerado**
  e a etapa v1.1 (Confiabilidade Máxima) está **concluída**.

### Added

- Métodos novos em `BlocoDPLT`: `corrente_svc`, `susceptancia_tcsc`,
  `corrente_tcsc`, `ativo_statcom`, `corrente_statcom`, `tensao_interna_statcom`,
  `reativo_cc`, `tensao_barra_cc`, `estado_cdu`.
- 1 teste novo de roundtrip das linhas DPLT 4-letra; os testes existentes foram
  atualizados para os mnemônicos reais. Total: 222 testes.

## [1.1.4] — 2026-07-10 — Curvas de tempo inverso (bloco CURVA) validadas

> Quarto patch da etapa **v1.1 (Confiabilidade Máxima)**. Fecha o item
> best-effort do `stip` de RELINV.

### Fixed

- Curvas de tempo inverso: o tipo de bloco correto é **`CURVA`** (§29.3.13), não
  `RELINV` (que não consta no manual 12.10). O parser agora reconhece o tipo
  `CURVA` e **todos os subtipos** de `stip`: **IEC, IEC2, IEEE, IEEE2**. Antes só
  `IEC`/`IEEE` eram aceitos — `IEC2`/`IEEE2` eram confundidos com a variável de
  entrada, deslocando todos os campos seguintes.
- `RELINV` mantido como **alias legado** do tipo (retrocompatível).

### Changed

- Confiabilidade das curvas de tempo inverso: **best-effort → Alta** (validado
  contra as Listagens 29.97–29.100 do manual). A "regra da ignorância" que
  bloqueava o `stip` foi removida (a referência §29.3.13 está disponível).

### Added

- 2 testes novos: roundtrip do bloco CURVA nos 4 subtipos + alias RELINV.
  Total: 221 testes.

## [1.1.3] — 2026-07-10 — LeitorSAV robusto (colunas fixas + DGBT)

> Terceiro patch da etapa **v1.1 (Confiabilidade Máxima)**.

### Changed

- `LeitorSAV` reescrito para **colunas fixas** do layout ANAREDE (antes fazia
  split de espaços, que quebrava com nomes de barra contendo espaços e errava
  a posição do circuito no DLIN). Mantém *fallback* por espaços para tolerância.
- Tensão-base (kV) das barras agora é **resolvida via bloco DGBT** (grupo → kV),
  em vez da heurística anterior que buscava um kV "plausível" no DBAR (onde só
  há a tensão em pu). `BarraSAV` ganhou os campos `tipo` e `grupo_base`.
- Reconhece mais blocos ANAREDE (DGBT, DSHL, DBSH, DARE, DTPF, DANC) como
  cabeçalhos, evitando falsos "não interpretada".
- Confiabilidade LeitorSAV elevada de **Média → Alta** no README.

### Added

- 3 testes novos: DBAR/DGBT em colunas fixas (nome com espaço + tensão-base),
  DLIN em colunas fixas, e blocos extras ignorados sem erro. Total: 219 testes.

## [1.1.2] — 2026-07-10 — HVDC (DCNV/DELO) validados contra o manual

> Segundo patch da etapa **v1.1 (Confiabilidade Máxima)**.

### Changed

- **BREAKING** — `BlocoHVDC` (DCNV, §46.21) re-modelado de "conversor de elo"
  best-effort (`nb_ret/nb_inv/pcc/vcc/icc/alfa_*`) para o código real de
  **dados de conversor CA-CC + associação a controles**:
  `adicionar(no, mc, gkb=None, amn=None, amx=None, gmn=None, mc_usuario=False,
  s1..s4=None, s1..s4_usuario=False)`. Serialização em colunas fixas.
- Confiabilidade DCNV elevada de **Média → Alta** no README.

### Added

- **`BlocoDELO`** (DELO, §46.27) — associação de elos CC aos modelos de polo
  (`ne, mp, mm=None, mp_usuario, mm_usuario`); exposto em `CasoAnatem.delo` e
  emitido no deck após o HVDC.
- Parser lê DCNV (colunas fixas) e DELO (formato livre); antes pulados.
- 4 testes novos (roundtrip DCNV com/sem sinais, exemplo manual DELO Lst. 46.25,
  roundtrip DELO bipolar/monopolar). Total: 216 testes.

## [1.1.1] — 2026-07-10 — FACTS validados contra o manual

> Primeiro patch da etapa **v1.1 (Confiabilidade Máxima)**. Alinha o número de
> versão do pacote ao esquema v1 já anunciado no README (o código estava em
> `0.14.2`; o esquema `0.x` foi encerrado).

### Changed

- **BREAKING** — Blocos FACTS re-modelados para bater com o manual ANATEM §46
  (antes eram best-effort com campos inventados):
  - `BlocoSVC` (DCER, §46.18) agora é código de **associação**:
    `adicionar(nb, gr, mc, me=None, mc_usuario=False, me_usuario=True)`.
    Removidos `no/nb/bmin/bmax/vref/modelo`.
  - `BlocoTCSC` (DCSC, §46.22) idem:
    `adicionar(de, pa, mc, nc=1, me=None, mc_usuario=False, me_usuario=True)`.
    Removidos `no/de/para/circ/xcmin/xcmax/modelo`.
  - `BlocoSTATCOM` (DVSI, §46.64) agora modela os **15 campos** reais do
    conversor VSI: `adicionar(nv, de, np, cnvk, vb, xv, vst, st, ne, pa=None,
    nx=1, m="P", rv=None, vpt=None, tap=1.0)`. Removidos
    `no/nb/tipo_vsi/qmin/qmax/vref/modelo`.
- Confiabilidade DCER/DCSC/DVSI elevada de **Média → Alta** na tabela do README.

### Added

- Parser (`ParserSTB`) agora lê os blocos DCER/DCSC (formato livre) e DVSI
  (colunas fixas) — antes eram pulados silenciosamente. Roundtrip garantido.
- 6 testes novos: validação contra Listagens 46.16/46.20/46.61 do manual e
  roundtrip por bloco (DCER, DCSC, DVSI shunt e série). Total: 212 testes.

## [0.14.2] — 2026-07-09 ⭐

### Added

- Encoding latin-1 garantido em entrada/saída
- Desambiguação automática de tipos CDU (IMPORT/EXPORT/INPUT/OUTPUT/SERIET)
- Validação cruzada DMAQ ↔ DMDG finalizada
- 163+ testes covering roundtrip, encoding, blocos, parser, CDU
- Type hints completos em todas as classes públicas
- Documentação consolidada com tabela de confiabilidade

### Changed

- Parser CDU agora reconhece estruturas aninhadas corretamente
- Validação de caracteres latin-1 mais rigorosa

### Fixed

- Suporte correto a caracteres especiais em nomes de arquivos
- Parser CDU reconhece COMPAR/LOGIC/SERIET em posições variáveis

## [0.13.3] — 2026-05-15

### Added

- Validação FACTS/HVDC/CDU contra manual ANATEM 12.10
- 140+ testes

## [0.12.3] — 2026-04-01

### Added

- Robustez do parser CDU melhorada
- Suporte a IMPORT/EXPORT com limites

## [0.11.3] — 2026-03-10

### Added

- Type hints completos
- Documentação inline

## [0.10.3] — 2026-02-15

### Added

- Documentação pública inicial

## [0.9.2] — 2026-01-20

### Changed

- Refatoração estrutural

## [0.8.4] — 2025-12-30

### Added

- Cobertura CDU expandida (46+ testes)

## [0.7.3] — 2025-11-15

### Added

- Validações cruzadas (DMAQ ↔ DMDG)

## [0.6.4] — 2025-10-10

### Added

- Integração FACTS/HVDC/CDU

## [0.5.3] — 2025-09-01

### Added

- Serialização posicional DMAQ

## [0.4.7] — 2025-08-01

### Added

- Blocos básicos
- Parser inicial
- Ensaios automatizados

---

**Formato:** [Semantic Versioning](https://semver.org/)
**Use v0.14.2** para novos projetos.
