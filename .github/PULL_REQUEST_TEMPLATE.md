## ¿Qué cambia y por qué?


## IDs relacionados

- Historia: `US-___`
- Requisito: `REQ-___`
- Otros (DS / ML / ADR / TEST / BUG / SEC):

## ¿Cómo lo probaste?

```
# pega aquí los comandos y su salida
```

## Avance entregado

- Historia `US-___`: [ ] cerrada por completo · [ ] avance parcial
- Fila actualizada en `02_Requirements/Traceability_Matrix.md`: [ ] sí
- Lo que aún falta (si aplica):

## Definition of Filed

- [ ] Tiene **ID** según `_Meta/Naming_Conventions.md`
- [ ] Vive en su **carpeta correcta**
- [ ] Tiene **frontmatter** con `owner` y `status`
- [ ] Enlaza `traces_up` y `traces_down`
- [ ] Listado en el **`_index.md`** de su carpeta
- [ ] Fila actualizada en la matriz de trazabilidad

## Calidad

- [ ] `python _Meta/scripts/vault_lint.py .` da Vault limpio
- [ ] `pytest tests/ -q` en verde
- [ ] Commits en Conventional Commits con el ID

## Uso de IA

- [ ] Usé IA — enlace al DevLog: `_DevLog/____`
- [ ] **Revisé línea por línea** el código generado
- [ ] No pegué datos reales ni credenciales en prompts
- [ ] (Alternativa) No usé IA en este cambio

## Seguridad

- [ ] No subo `.env`, credenciales ni llaves
- [ ] No subo datos reales pesados (>5 MB)
- [ ] Si toqué esquema, seguridad o CI/CD, pedí revisión del dueño del área

---

## Aprobación — compuerta única (PM · DEC-003)

**Aprobación obligatoria · Proceso + trazabilidad** — @edgarcoroneln (PM)
- [ ] CI verde · plantilla completa · IDs · DevLog · Definition of Filed · matriz actualizada

**Revisión técnica de apoyo (no bloqueante)** — Tech Lead del área
- [ ] Solicité su revisión con *Reviewers* si el cambio toca su área (resuelve la historia · no rompe nada · convenciones OK · pruebas suficientes)
