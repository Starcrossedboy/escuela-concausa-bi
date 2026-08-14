---
id: DS-04
title: "DS-04 · SESNSP Incidencia Delictiva"
owner: "Luis Enrique García Vázquez"
status: draft
traces_up: ["01_Product/PRD", "12_Roadmap_Sprints/PLAN_MAESTRO"]
tags: [data-source, bronze, driver-d2, ingesta-continua]
---

# DS-04 · SESNSP Incidencia Delictiva Municipal

> → [[14_Data_Sources/_index]] · Prueba de descarga real **🔴 BLOQUEADA** (Semana 1) — ver sección 9
> **Ingesta continua #1** (mensual).

## 1. Identificación
- **Nombre oficial:** Incidencia Delictiva del Fuero Común (nivel municipal).
- **Institución responsable:** SESNSP (Secretariado Ejecutivo del Sistema Nacional de Seguridad
  Pública).
- **Qué aporta al proyecto:** delitos y víctimas **por municipio**; base del entorno de inseguridad de
  la escuela.

## 2. Acceso
- **Portal oficial (landing):**
  `https://www.gob.mx/sesnsp/acciones-y-programas/datos-abiertos-de-incidencia-delictiva`
- **URL de descarga confirmada (metodología 2015-2025, corte jun 2026):** archivo
  `Municipal-Delitos-2015-2025_jun2026.zip`, publicado como enlace de OneDrive/SharePoint:
  `https://sspcgob-my.sharepoint.com/:u:/g/personal/cni_sspc_gob_mx/IQAnMGiScnoTTr4J2J9mUZthAat6lEdo7-1MCUpQU4n4EwQ?e=1NpS13`
  (verificado el 14-ago-2026: la URL resuelve y redirige al nombre de archivo real, confirmando
  que el enlace es vigente).
- **⚠️ Hallazgo crítico:** este enlace **no es descarga pública anónima**. Al seguir la redirección
  (con o sin `&download=1`) siempre termina en `login.microsoftonline.com` pidiendo autenticación
  de una cuenta Microsoft/institucional. Esto es atípico para un portal de "datos abiertos" y
  **bloquea la prueba de descarga automatizada** con `curl`/`requests` sin credenciales.
- **Formato:** ZIP (contenido interno no verificado — bloqueado por el login).
- **Tamaño aproximado:** PENDIENTE-CONFIRMAR (bloqueado por el login).

## 3. Frecuencia real de actualización
- **Mensual** (publicación aproximada el día 20 de cada mes). → satisface el requisito de ingesta
  continua.

## 4. Cobertura geográfica y temporal
- **Geográfica:** Nacional, desagregado municipal.
- **Temporal:** serie **desde 2015** (metodología vigente); confirmar en la prueba de descarga.

## 5. Esquema esperado (confirmar en prueba de descarga)
| Columna | Tipo | Nota |
|---|---|---|
| `cve_ent` | str (2) | Clave INEGI entidad |
| `cve_mun` | str (5) | Clave INEGI municipal (5 dígitos) |
| `anio` | int | Año |
| `mes` | str/int | Mes |
| `tipo_delito` | str | Subtipo/modalidad |
| `victimas` / `carpetas` | int | Conteo |

## 6. Llave de unión
- **Clave INEGI de 5 dígitos** (municipio). Se cruza con la escuela vía su municipio (DS-01/DS-02).

## 7. Driver que alimenta
- **D2 · Inseguridad del entorno.**

## 8. Licencia de uso
- Términos de Libre Uso MX — **confirmar** en la ficha oficial.

## 9. Prueba de descarga real — **🔴 BLOQUEADA** (Semana 1)
- [x] URL real localizada y verificada (resuelve, nombre de archivo confirmado)
- [ ] Archivo descargado físicamente — **bloqueado: exige login Microsoft/SharePoint**
- [ ] Abierto y con datos utilizables
- [ ] Registros contados: `______` (no se pudo obtener)
- [ ] Esquema verificado (columnas y tipos) (no se pudo obtener)
- [ ] Llave confirmada: `cve_mun` de 5 dígitos (no se pudo obtener)
- **Responsable:** Luis Enrique García Vázquez · **Fecha del intento:** 2026-08-14
- **Qué falta y por qué:** el enlace de descarga que publica SESNSP es un share de SharePoint que
  redirige a `login.microsoftonline.com` en cada intento (probado con y sin parámetro
  `download=1`, con user-agent de navegador). No es viable un extractor idempotente (`US-122b`)
  contra esta URL sin: (a) confirmar si existe un mirror público sin autenticación, o (b)
  credenciales/flujo de sesión autorizado por el Tech Lead. **Escalado a Diana Alvarez (Tech
  Lead) para definir cómo proceder antes de iniciar `US-122b`.**

## 10. Riesgos conocidos
- **Nuevo (2026-08-14):** el enlace oficial de descarga exige autenticación Microsoft — no es un
  extractor "URL pública + GET" simple; ver sección 9.
- Cambios de metodología/clasificación de delitos entre años.
- Subregistro (cifra negra): no todos los delitos se denuncian.
- Municipios con cero reportado que en realidad es falta de dato → aplicar criterio `SIN_DATO`.
- El archivo mensual puede reescribir históricos (revisiones).
