-- =============================================================================
-- db03_cubo_escuela_360  ·  DB-03 Ficha de escuela
-- -----------------------------------------------------------------------------
-- Historia   : US-211a  (Marina Garcia del Buey, Celula 2 - Analytics & BI)
--              Repunteo US-205 (Manuel Alejandro Serrania Reinada, C2)
-- Contrato   : 04_UX_Design/Cube_Specs_DB03_DB04.md  (DOC-CUBESPEC-DB0304) §3
-- Grano      : una fila por cct x id_ciclo
--
-- REPUNTEO A CUBOS FISICOS (US-205 / US-113): passthrough 1:1 de
--   gold.cubo_escuela_360 (C1). La lista de columnas es EXPLICITA a proposito:
--   documenta el contrato de salida y evita que un ADD COLUMN futro del cubo
--   cambie silenciosamente los tableros.
--
-- Las reglas del contrato ya estan garantizadas por C1 (ver cubo_escuela_360):
--   R1  las salidas de ML llegan por LEFT JOIN (gold.predicciones /
--       gold.recomendaciones) con la llave completa y el filtro de modelo.
--   R2  SIN_DATO explicito: cada driver viaja con su bandera d#_cobertura y la
--       ausencia de ML con cobertura_prediccion / cobertura_recomendacion.
--   R3  umbral de negocio 0.6 (en_riesgo), ratificado el 2026-08-13.
--   R5  Gold ya viene acotado a SCOPE_ENTIDADES.
-- =============================================================================

SELECT
    -- ---------- identidad y llaves -------------------------------------------
    s.cct,
    s.id_ciclo,
    s.ciclo,
    s.anio_inicio,

    -- ---------- perfil de la escuela -----------------------------------------
    s.nombre_escuela,
    s.nivel,                                   -- filtro global: nivel educativo
    s.sostenimiento,
    s.latitud,
    s.longitud,
    s.cve_ent,                                 -- filtro global: entidad
    s.cve_mun,                                 -- salto a DB-04
    s.nombre_municipio,
    s.nombre_entidad,

    -- ---------- metricas observadas ------------------------------------------
    s.matricula_total,
    s.matricula_ciclo_anterior,                -- denominador directo de KPI-02 (BUG-031/ADR-007)
    s.variacion_matricula,                     -- alumnos absolutos observados (perfil), no la razón
    s.indice_completitud_drivers,

    -- ---------- los 6 drivers con su bandera de cobertura --------------------
    s.d1, s.d1_cobertura,
    s.d2, s.d2_cobertura,
    s.d3, s.d3_cobertura,
    s.d4, s.d4_cobertura,
    s.d5, s.d5_cobertura,
    s.d6, s.d6_cobertura,

    -- ---------- infraestructura CEMABE (perfil, D3/D4) -----------------------
    s.agua,
    s.drenaje,
    s.electricidad,
    s.sanitarios,
    s.internet,
    s.computadoras,

    -- ---------- salida de ML-01 (prediccion) ---------------------------------
    s.indice_riesgo,
    s.en_riesgo,
    s.variacion_proyectada,
    s.probabilidad,
    s.cobertura_prediccion,

    -- ---------- salida de ML-02/ML-03 (recomendacion prescriptiva) -----------
    s.driver_dominante,
    s.nombre_driver,
    s.recomendacion,
    s.prioridad,
    s.cobertura_recomendacion,

    -- ---------- navegacion cruzada hacia DB-04 (US-214a) ---------------------
    -- Ruta `DB-03 -> DB-04` del contrato drill_down (metrics_db03_db04.yaml).
    -- Superset no tiene columna nativa tipo link (SIP-77 fue rechazada) y ni el
    -- cross-filtering ni "Drill to Detail" cruzan de un tablero a otro: el unico
    -- mecanismo es un <a href> con `native_filters` en RISON. Mismo patron que
    -- `link_db08` de US-214b (Monserrat), reusado a proposito.
    --
    -- Los IDs de filtro nativo se fijan POR POSICION en `filtros_globales` del
    -- tablero destino (`_filtros_nativos()` emite NATIVE_FILTER-US203-{indice}).
    -- En db04_comparador_municipio.yaml: id_ciclo = 0, cve_mun = 4.
    -- >>> Si alguien REORDENA esa lista, este link apunta al filtro equivocado
    -- >>> en silencio. La guarda esta en tests/test_drill_down_db03_db04.py.
    --
    -- Ambos valores se citan con %27: `cve_mun` ('09002') y `id_ciclo`
    -- ('2024-2025') tienen forma que RISON obliga a citar, y el backend de
    -- Superset usa ese mismo reemplazo de ' por %27 en reports/models.py.
    --
    -- Si cve_mun o id_ciclo fueran NULL, `||` anula toda la cadena y la celda
    -- sale vacia: preferible a un link roto.
    '<a href="/superset/dashboard/db04-comparador-municipio/?native_filters=' ||
        '(NATIVE_FILTER-US203-0:(extraFormData:(filters:!((col:id_ciclo,op:IN,val:!(%27' || s.id_ciclo || '%27)))),' ||
        'filterState:(label:id_ciclo,validateStatus:!f,value:!(%27' || s.id_ciclo || '%27)),' ||
        'id:NATIVE_FILTER-US203-0,ownState:()),' ||
        'NATIVE_FILTER-US203-4:(extraFormData:(filters:!((col:cve_mun,op:IN,val:!(%27' || s.cve_mun || '%27)))),' ||
        'filterState:(label:cve_mun,validateStatus:!f,value:!(%27' || s.cve_mun || '%27)),' ||
        'id:NATIVE_FILTER-US203-4,ownState:()))' ||
        '" target="_blank">Comparar su municipio →</a>' AS link_db04

FROM gold.cubo_escuela_360 s