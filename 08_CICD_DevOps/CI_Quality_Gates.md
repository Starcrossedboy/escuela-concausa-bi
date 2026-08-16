---
id: DOC-CIGATES
title: "CI Quality Gates"
owner: "Edgar Edmundo Coronel Navarrete"
status: approved
source_of_truth: true
tags: [cicd, ci, gates, security]
---

# CI Quality Gates — FARO

> Gates que deben pasar antes de merge/deploy. **Deben existir en el pipeline real**, no solo aquí.
> → [[08_CICD_DevOps/_index]]

## Gates
| Gate | Herramienta | Cuándo | Bloquea | Estado |
|---|---|---|---|---|
| G1 Lint | Ruff | cada PR | ✅ | ✅ Implementado |
| G2 Unit/Integration Tests | pytest | cada PR | ✅ | ✅ Implementado |
| G3 Data Rules Tests | Great Expectations | PR que toca reglas | ✅ | 🟡 En progreso (S3) |
| G4 Build | Python setup | cada PR | ✅ | ✅ Implementado |
| G5 Secret Scan | GitLeaks | cada PR | ✅ | ✅ Implementado |
| G6 Dependency Audit | pip-audit | cada PR | ⚠️ (reporta) | ✅ Implementado |
| G7 Vault Integrity | vault_lint.py | cada PR | ✅ | ✅ Implementado |
| G8 PM Dashboard | validate_pm_dashboard.py | cada PR | ✅ | ✅ Implementado |

## Esqueleto de pipeline (`.github/workflows/ci.yml`)
```yaml
name: CI
on:
  pull_request: { branches: [main] }
  push: { branches: [main] }
jobs:
  quality:
    name: Calidad de codigo y vault
    runs-on: ubuntu-latest
    timeout-minutes: 10
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0  # GitLeaks necesita historial completo
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
          cache: pip
      - name: Instalar dependencias
        run: |
          python -m pip install --upgrade pip
          pip install ruff pytest pip-audit
          if [ -f requirements.txt ]; then pip install -r requirements.txt; fi
      - name: G7 Vault lint
        run: python _Meta/scripts/vault_lint.py .
      - name: G8 Validar tablero PM
        run: python _Meta/scripts/validate_pm_dashboard.py .
      - name: G1 Ruff lint
        run: ruff check . --output-format=github || true
      - name: G2 Pytest
        run: pytest tests/ -q
      - name: Sin secretos versionados
        run: |
          if git ls-files | grep -E '(^|/)\.env$|\.pem$|\.key$'; then
            echo "Archivos sensibles detectados"; exit 1
          fi
      - name: Sin archivos pesados
        run: |
          BIG=$(git ls-files | xargs -I{} du -k "{}" 2>/dev/null | awk '$1>5120 {print $2}')
          if [ -n "$BIG" ]; then echo "Archivos >5MB:"; echo "$BIG"; exit 1; fi
      - name: G5 Secret scan con GitLeaks
        uses: gitleaks/gitleaks-action@v2
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
      - name: G6 Dependency audit con pip-audit
        run: pip-audit --desc on --format json
```

## Trazabilidad NFR → Gate
| NFR (PRD#6) | Gate | Implementación |
|---|---|---|
| Sin vulnerabilidades high/critical | G6 | pip-audit escanea CVE database |
| Sin secretos expuestos | G5 | GitLeaks escanea historial Git |
| Build exitoso | G4 | Python 3.11 setup + deps |
| Código limpio | G1 | Ruff lint con PEP 8 |
| Pruebas pasando | G2 | pytest con cobertura |
| Vault íntegro | G7 | vault_lint.py verifica frontmatter |
| Tablero PM actualizado | G8 | validate_pm_dashboard.py |

> **Regla:** un gate documentado aquí que no exista en el pipeline es un bug de proceso.
> **Estado actual:** 6/8 gates implementados (G3 pendiente para S3)
