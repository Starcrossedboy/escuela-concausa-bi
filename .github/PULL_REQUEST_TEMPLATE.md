<!--
  TÍTULO DEL PR — se valida en CI, cópialo con este formato exacto:

      [Nombre Apellido] - Descripción concisa (ID) - [sync|CI|DoF|DevLog]

  Ejemplo:
      [Diana Alvarez] - Extractor de CEMABE con reintentos (US-113) - [sync|CI|DoF|DevLog]

  El nombre es el tuyo, el de tu rama `dev/nombre-apellido`. Los cuatro tokens del final
  son tu declaración de que sincronizaste, el CI está verde, cumples Definition of Filed
  y escribiste tu DevLog.
-->

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
- Fila actualizada en `vault/02_Requirements/Traceability_Matrix.md`: [ ] sí
- Lo que aún falta (si aplica):

## Sincronía y alcance

- [ ] Salgo de **mi rama fija** `dev/nombre-apellido` — la única que uso
- [ ] Hice `git merge origin/main` **antes de abrir este PR**
- [ ] Solo toqué archivos de mi alcance 🟢/🟡 (`vault/_Meta/ownership.yml`) — o, si el cambio
      es **transversal**, lo declaro arriba y pedí revisión a cada dueño afectado
- [ ] Si toqué una ruta crítica de otra persona, le pedí revisión <!-- opcional -->

## Definition of Filed

- [ ] Tiene **ID** según `vault/_Meta/Naming_Conventions.md`
- [ ] Vive en su **carpeta correcta**
- [ ] Tiene **frontmatter** con `owner` y `status`
- [ ] Enlaza `traces_up` y `traces_down`
- [ ] Listado en el **`_index.md`** de su carpeta
- [ ] Fila actualizada en la matriz de trazabilidad

## Calidad

- [ ] `python vault/_Meta/scripts/vault_lint.py .` da Vault limpio
- [ ] `pytest tests/ -q` en verde
- [ ] Commits en Conventional Commits con el ID

<!--
  Las casillas que terminan con un comentario HTML "opcional" (se ven abajo, en el archivo
  fuente) NO las exige el check de plantilla: son alternativas excluyentes y condicionales que
  no aplican a todo PR. Si agregas una casilla que un autor honesto pueda tener que dejar
  vacía, márcala igual. Ver .github/scripts/verificar_plantilla_pr.sh (BUG-014).
-->

## Uso de IA

- [ ] Usé IA — enlace al DevLog: `vault/_DevLog/____`
- [ ] **Revisé línea por línea** el código generado
- [ ] No pegué datos reales ni credenciales en prompts
- [ ] (Alternativa) No usé IA en este cambio <!-- opcional -->

## Seguridad

- [ ] No subo `.env`, credenciales ni llaves
- [ ] No subo datos reales pesados (>5 MB)
- [ ] Si toqué esquema, seguridad o CI/CD, pedí revisión del dueño del área <!-- opcional -->

---

## Aprobación — compuerta única (PM · DEC-003)

**Aprobación obligatoria · Proceso + trazabilidad** — @edgarcoroneln (PM)
- [ ] CI verde · plantilla completa · IDs · DevLog · Definition of Filed · matriz actualizada

**Revisión técnica de apoyo (no bloqueante)** — Tech Lead del área
- [ ] Solicité su revisión con *Reviewers* si el cambio toca su área (resuelve la historia · no rompe nada · convenciones OK · pruebas suficientes)

> Al mergear: **no borres la rama.** `dev/nombre-apellido` es permanente y se reutiliza
> para el siguiente cambio.
