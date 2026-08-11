---
id: DOC-ONBOARD
title: "Developer Onboarding"
owner: "Edgar Edmundo Coronel Navarrete"
status: approved
source_of_truth: true
last_reviewed: "2026-08-06"
tags: [onboarding, engineering]
---

# Developer Onboarding — FARO

> → [[00_Start_Here/PROJECT_INDEX|Índice del Proyecto]]

## 1. Requisitos
- Python 3.11 · Airflow · dbt · Postgres · Superset · MLflow · FastAPI · Docker · GCP instalado
- Acceso al repo: https://github.com/edgarcoroneln/escuela-concausa-bi
- Editor con soporte Markdown (Obsidian recomendado para el vault)

## 2. Setup
```bash
git clone https://github.com/edgarcoroneln/escuela-concausa-bi
cd escuela-concausa-bi
# instalar dependencias según el stack
```

## 3. Tu primer día
1. Lee [[00_Start_Here/How_To_Navigate]] y [[_Meta/Vault_Rules]].
2. Lee tu **Agent Context**: `09_AI_Governance/Agent_Contexts/{tu-nombre}.md`.
3. Lee [[05_Engineering/Engineering_Workflow]] y [[05_Engineering/Definition_of_Done]].
4. Toma una `TASK-###` del sprint activo ([[12_Roadmap_Sprints/_index]]).

## 4. Directorio del equipo

Los nombres, niveles, células y roles provienen del
[[12_Roadmap_Sprints/PLAN_MAESTRO|Plan Maestro]]. Esta tabla agrega únicamente la identidad de
GitHub necesaria para invitaciones, asignaciones, revisiones y `CODEOWNERS`.

| Persona (nombre canónico) | Nivel canónico | Célula | GitHub User | Estado |
|---|---|---|---|---|
| Edgar Edmundo Coronel Navarrete | Medio | PO | `edgarcoroneln` | Confirmado |
| Diana Aracely Alvarez Varela | Alto | Célula 1 | `DianaVarela96` | Confirmado |
| Deni Garrido Fragoso | Medio | Célula 1 | `dgdeni` | Confirmado |
| Luis Enrique García Vázquez | Bajo | Célula 1 | `LuisEGarciaV` | Confirmado |
| Emilio Galnares Ruiz | Bajo | Célula 1 | `Starcrossedboy` | Confirmado |
| Manuel Alejandro Serranía Reinada | Alto | Célula 2 | `mserraniaa-png` | Confirmado |
| Marina García del Buey | Medio | Célula 2 | `marina-gdb` | Confirmado |
| Monserrat Xcaret Miranda Olivas | Medio | Célula 2 | `monserratxmiranda` | Confirmado |
| Eloisa González Rubio | Bajo | Célula 4 | `EloisaGonzalezRubio` | Confirmado |
| Andrés González Habib | Alto | Célula 3 | `Agh28` | Confirmado |
| Héctor Rafael Morales Marbán | Medio | Célula 3 | `hector677-mm` | Confirmado |
| Estefany Lucero Hernández Loredo | Bajo | Célula 3 | `stephi-coder` | Confirmado |
| Carlos Guillermo Mayorga Tapia | Bajo | Célula 3 | `cmayorgat44` | Confirmado |
| Karla Alejandra Monter Benitez | Medio | Célula 4 | `marlakonter` | Confirmado |
| Christian Imanol Ruiz Hurtado | Alto | Célula 4 | `ImanolRuiz00` | Confirmado |
| Juan Carlos Macías Mayen | Medio | Célula 4 | `juanmmayen98` | Usuario confirmado; nivel por conciliar |
| Oscar Antonio Quiroz Lázaro | Bajo | Célula 2 | `oscarqlazaro-lab` | Confirmado |
| Luis Téllez Domínguez | Medio | Célula 5 | `LuisTellez03` | Confirmado |
| Edgar Ulises Jiménez López | Bajo | Célula 5 | `EJ-by-Me` | Confirmado |
| Alejandro Velázquez Mendoza | Bajo | Célula 5 | `avmxk01` | Confirmado |
| Edward Ulysses Ruiz Bustillos | Bajo | Célula 5 | `Dr4wde064` | Confirmado |

> Usa **siempre** el nombre canónico de esta tabla (ver [[_Meta/Naming_Conventions]]). La lista
> recibida el 2026-08-06 marcó a Juan Carlos como nivel Bajo; el Plan Maestro y su Agent Context lo
> registran como **Medio**, que se conserva hasta una decisión explícita.

### Pendientes para la sesión del 2026-08-06

- **Usuarios de GitHub: 21/21 confirmados.** Oscar Antonio Quiroz Lázaro (`oscarqlazaro-lab`) quedó
  confirmado el 2026-08-07; ya no hay usuarios pendientes en el directorio.
- Abrir cada perfil antes de enviar la invitación para validar la escritura exacta y que la cuenta
  pertenezca a la persona indicada.
- Conciliar el nivel de Juan Carlos Macías Mayen; si cambia, actualizar el Plan Maestro, su Agent
  Context y cualquier asignación afectada en el mismo PR.
- Verificar que las 21 personas acepten la invitación al repositorio antes de asignarles issues o
  solicitarles revisión.

El revisor obligatorio de todo el repo es el PM (`* @edgarcoroneln`) en
[`.github/CODEOWNERS`](../.github/CODEOWNERS) — **compuerta única desde 2026-08-09 (DEC-003)**. Los
Tech Leads revisan de forma técnica no bloqueante; se les solicita como revisores de apoyo.

## 5. Flujo de trabajo (resumen)
Rama `feat/...` → commits → PR con template → CI verde + **1 aprobación del PM** → merge.
Nunca push directo a la rama protegida. Toda sesión con IA → DevLog.

## 6. Integrantes que completaron onboarding
- Deni Garrido Fragoso (`dgdeni`)
