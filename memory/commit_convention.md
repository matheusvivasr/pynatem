---
name: commit_convention
description: Convenção de commit messages para pynatem — formato vM.m.p quando houver versão
metadata:
  type: feedback
---

# Convenção de Commits — pynatem

## Regra: Quando há versão no escopo, comece com vM.m.p

### Exemplos Corretos

```
v2.1.0 feat: início do ciclo de pós-processamento consolidado
v2.1.1 feat: parser de header plt binário
v2.1.2 fix: LeitorREL extração de versão
v2.2.1 feat(cdu): inicialização DEFVAL/DEFVDF/DEFPLT
v2.3.2 feat(análise): análise de CDU isolada
```

### Exemplos Incorretos (Não Fazer)

```
feat(v2.1): ... ❌ versão não deve estar em parênteses
feat: v2.1.0 ... ❌ versão no meio, não no início
```

### Por Quê

- **Clareza:** Fácil ver qual versão cada commit pertence pelo `git log`
- **Release notes:** Ferramentas de release conseguem parsear vM.m.p no início
- **Organização:** Agrupa commits por versão naturalmente

### Quando NÃO usar vM.m.p

- Commits sem versão associada (docs, CI, memory, etc.):
  ```
  docs: atualizar README
  ci: adicionar teste de conformidade
  memory: checkpoint de sessão
  ```

- Commits antes de v2.1.0 (já foram feitos assim):
  ```
  feat(v2.0.3): DCER e DFNT
  ```

## Aplicar a Partir de v2.1.3

Quando retomar trabalho em v2.1.3, use:
```
v2.1.3 feat: snapshots + DAVS — segundo patch
v2.2.1 feat(cdu): inicialização de modelos
... e assim por diante
```

