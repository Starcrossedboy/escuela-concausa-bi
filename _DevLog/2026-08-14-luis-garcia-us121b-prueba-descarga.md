---
id: DEVLOG-2026-08-14-LUIS-US121B
title: "DevLog — US-121b Prueba de descarga real DS-04 y DS-05"
author: "Luis Enrique García Vázquez"
session_date: "2026-08-14"
ai_tool: "Claude Code (Sonnet 5)"
traces_up: ["US-121b", "REQ-001"]
affected_ids: ["US-121b", "REQ-001", "DS-04", "DS-05"]
tags: [devlog, ai-assisted, sprint-1, data-sources, sesnsp, sinaica]
---

# DevLog — US-121b: Prueba de descarga real DS-04 (SESNSP) y DS-05 (SINAICA)

## Contexto

**Objetivo:** cerrar `US-121b` (vencía domingo 9-ago, se retomó el 14-ago ya en S2): localizar las
URLs/endpoints reales de mis dos fuentes, descargar/consultar de verdad, contar registros,
verificar esquema y llave, y llenar la sección 9 de las fichas `DS-04` y `DS-05` en el vault.

**Fecha:** viernes 14 de agosto de 2026
**Tool:** Claude Code (Sonnet 5)

---

## Qué se pidió a la IA

Contexto inicial (revisar mi plan de sprint y decirme qué historia empezar), y después:

> "Sí, por favor. Comencemos ahora mismo con la tarea US-121b. Busca las URL/endpoints de SESNSP y
> SINAICA, realiza la prueba de descarga y completa los pasos que indicaste."

---

## Qué hizo la IA (y qué se revisó)

### DS-04 · SESNSP

- Buscó en la web el portal oficial (`gob.mx/sesnsp/.../datos-abiertos-de-incidencia-delictiva`) y
  encontró un enlace de descarga (`Municipal-Delitos-2015-2025_jun2026.zip`, publicado vía
  SharePoint/OneDrive de `cni_sspc_gob_mx`).
- **Revisión manual:** antes de dar el enlace por bueno, se verificó con `curl -I` (headers, sin
  descargar el archivo) que la URL resuelve y expone el nombre real del archivo. Se probó también
  con `&download=1` para intentar evitar la UI de OneDrive.
- **Resultado:** en ambos casos la redirección termina en `login.microsoftonline.com` pidiendo
  autenticación. **No es un enlace de descarga pública anónima**, a pesar de estar catalogado como
  "datos abiertos". Se decidió **no fabricar** conteos de registros ni esquema — eso violaría la
  regla del repo de nunca inventar datos de fuentes no verificadas. Se documentó el bloqueo tal
  cual y se dejó una nota explícita para escalar a la Tech Lead (Diana Alvarez) antes de intentar
  `US-122b` sobre esta fuente.
- También se intentó `datos.gob.mx` (API CKAN) y `secretariadoejecutivo.gob.mx` como alternativas
  públicas — ambos bloquean con reto anti-bot (Akamai/challenge JS), sin acceso vía `curl` desde
  este entorno.

### DS-05 · SINAICA

- La IA no encontró una API REST/JSON oficial documentada por INECC. En su lugar, revisó el
  código fuente del paquete open-source `rsinaica` (R, por Diego Valle-Jones,
  github.com/diegovalle/rsinaica) para identificar los endpoints internos reales que usa el sitio
  `sinaica.inecc.gob.mx`.
- **Prueba de descarga real ejecutada (no simulada):**
  - `POST /lib/libd/cnxn.php` (`metodo=getUltimosEnvios`) → 200 estaciones con envío reciente.
  - `POST /lib/j/php/getData.php` → catálogo completo, 384 estaciones históricas (nombre, código,
    red, lat/lon, municipioId, fecha de inicio de datos).
  - `POST /lib/libd/cnxn.php` (`estId=33&metodo=getParamsPorEstAjax`) → lista de parámetros
    disponibles para la estación de prueba (SO2, NO2, O3, PM10, PM2.5, etc.).
  - `POST /pags/datGrafs.php` (`estacionId=33&param=PM2.5&fechaIni=2026-08-01&rango=4...`) → **287
    registros horarios reales** de PM2.5 de la estación 33 ("Centro", Aguascalientes) del
    2026-08-01 en adelante, con datos vigentes de hoy (2026-08-14).
- **Revisión manual:** se verificó a mano el JSON crudo (`grep`/inspección directa del body de
  respuesta) para confirmar el esquema real (`id`, `fecha`, `hora`, `valor`, `bandO`, `val`), que
  **no coincide exactamente** con el esquema "esperado" que ya estaba en la ficha del vault
  (`parametro`, `fecha_hora` no existen como tales) — se corrigió la ficha para reflejar el
  esquema real, no el supuesto.
- Se detectó y documentó que la respuesta de `datGrafs.php` no es JSON puro sino HTML+JS con un
  arreglo `var dat = [...]` embebido — implica que el extractor de `US-122b` necesita una
  extracción por regex antes de poder parsear, no un `response.json()` directo.
- Se detectó que `municipioId` del catálogo de estaciones llegó como `"1"` (no como clave INEGI de
  5 dígitos) — riesgo nuevo documentado para la homologación de llave en `US-122b`.

---

## Decisiones tomadas (no delegadas a la IA)

1. **No marcar `US-121b` como Done.** DS-05 quedó completo, pero DS-04 quedó bloqueado. Siguiendo
   la regla del plan de sprint ("si tu historia queda a medias... anota qué falta y por qué"), se
   dejó en 🟡 En curso / 70% en la tabla de seguimiento, no en ✅.
2. **Escalar el bloqueo de DS-04 a la Tech Lead** en vez de intentar workarounds no autorizados
   (ej. scraping con sesión autenticada, credenciales compartidas) — está fuera de mi alcance
   decidir eso solo.
3. Corregir el esquema documentado de DS-05 al esquema real observado, no dejar el "esperado"
   original sin actualizar.

---

## Archivos modificados

- `14_Data_Sources/DS-04_SESNSP_Incidencia_Delictiva.md` — sección 2 (acceso, URL real + hallazgo
  de bloqueo), sección 9 (prueba parcial/bloqueada), sección 10 (riesgo nuevo).
- `14_Data_Sources/DS-05_SINAICA_Calidad_Aire.md` — sección 2 (endpoints reales), sección 5
  (esquema real corregido), sección 9 (prueba completada con evidencia), sección 10 (riesgos
  nuevos).
- `12_Roadmap_Sprints/Sprints/1-luis-enrique-garcia-vazquez.md` — tabla de seguimiento, fila
  `US-121b`.
- `02_Requirements/Traceability_Matrix.md` — fila `REQ-001`, columna DevLog (enlace a esta
  entrada).
- `_DevLog/2026-08-14-luis-garcia-us121b-prueba-descarga.md` (este archivo).
- `_DevLog/_index.md` — nueva fila.

---

## Seguridad / calidad

- [x] Sin secretos hardcodeados (todas las llamadas de prueba fueron anónimas, sin credenciales)
- [x] No se descargaron ni versionaron datos reales pesados — solo se ejecutaron pruebas puntuales
      contra las APIs/URLs para verificar accesibilidad y esquema
- [x] DevLog enlaza a los IDs afectados (`US-121b`, `REQ-001`, `DS-04`, `DS-05`)

## Bloqueantes

- **DS-04 (SESNSP):** el enlace de descarga oficial exige login de Microsoft/SharePoint. Necesito
  que Diana (Tech Lead) confirme cómo proceder antes de iniciar `US-122b` para esta fuente:
  ¿existe un mirror público sin autenticación?, ¿se autoriza usar una cuenta institucional para
  automatizar la descarga?, ¿se pide acceso formal a SESNSP?

## Próximos pasos

- Levantar el bloqueo de DS-04 con la Tech Lead antes del standup.
- Con DS-05 ya verificado, puedo adelantar el diseño del extractor de `US-122b` para esa fuente
  (incluyendo el parseo por regex de `datGrafs.php` y el manejo de `municipioId`).
