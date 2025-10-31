# Changelog

Todas as mudanças notáveis estão documentadas aqui.

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
