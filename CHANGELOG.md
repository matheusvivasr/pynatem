# Changelog

Todas as mudanças notáveis estão documentadas aqui.

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
