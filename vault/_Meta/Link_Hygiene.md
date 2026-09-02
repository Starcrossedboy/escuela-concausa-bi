---
id: META-LINK
title: "Link Hygiene"
owner: "Edgar Edmundo Coronel Navarrete"
status: approved
tags: [meta, hygiene, automation]
---

# Link Hygiene — Evitar links rotos y huérfanos

> → [[vault/_Meta/_index|Volver a _Meta]]

## Reglas

1. Enlaza con `[[wikilinks]]` relativos al vault, no rutas absolutas del disco.
2. Todo documento debe ser alcanzable desde algún `_index.md` (sin huérfanos).
3. Al renombrar un archivo, actualizar los backlinks (Obsidian lo hace automático; si editas fuera
   de Obsidian, corre el linter).
4. No links a rutas de sistema (`E:\...`, `/Users/...`) — se rompen entre máquinas.

## Check automatizado

Corre antes de cada release o en CI:

```bash
python vault/_Meta/scripts/vault_lint.py .
```

Detecta: links `[[...]]` rotos, archivos sin frontmatter, IDs duplicados, documentos huérfanos
(no listados en ningún `_index.md`) y filas incompletas en la matriz de trazabilidad.
