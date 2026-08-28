#!/usr/bin/env bash
# Prueba verificar_plantilla_pr.sh contra cuerpos de PR reales.
#
# Ejercita el script de verdad, no una copia de su lógica. Correr con:
#   bash .github/scripts/probar_verificar_plantilla.sh
#
# Historia: US-503 · Regresión de BUG-014.
set -uo pipefail

AQUI="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BAJO_PRUEBA="$AQUI/verificar_plantilla_pr.sh"
FALLOS=0

verificar() {
  local nombre="$1" esperado="$2" cuerpo="$3" got
  if PR_BODY="$cuerpo" bash "$BAJO_PRUEBA" >/dev/null 2>&1; then
    got="PASA"
  else
    got="REPRUEBA"
  fi
  if [ "$got" = "$esperado" ]; then
    printf 'OK    %-9s %s\n' "$got" "$nombre"
  else
    printf 'FALLA %-9s (esperado %s) %s\n' "$got" "$esperado" "$nombre"
    FALLOS=1
  fi
}

# La plantilla REAL del repositorio, no una copia. Una copia sintética fue justo lo que dejó
# pasar la segunda mitad de BUG-014: no tenía las casillas opcionales, así que la prueba daba
# verde mientras el gate reprobaba PRs bien llenados. Leyéndola del archivo no puede desviarse.
PLANTILLA="$(cd "$AQUI/.." && pwd)/PULL_REQUEST_TEMPLATE.md"

# Como la llena un autor: marca lo suyo y deja las opcionales sin marcar.
llenada_por_autor() {
  sed '/<!-- opcional -->/!s/^\([[:space:]]*\)- \[ \]/\1- [x]/' "$PLANTILLA"
}

verificar "plantilla real, llenada por el autor" "PASA" "$(llenada_por_autor)"
verificar "plantilla real sin llenar" "REPRUEBA" "$(cat "$PLANTILLA")"
verificar "casilla opcional sin marcar" "PASA" \
"$(printf '## Uso de IA\n- [x] Usé IA\n- [ ] (Alternativa) No usé IA <!-- opcional -->\n')"

verificar "el autor dejó casillas sin marcar" "REPRUEBA" \
"$(printf '## Calidad\n- [x] vault limpio\n- [ ] pytest verde\n')"

# El corazón de BUG-014: explicar la sintaxis no debe reprobar el PR.
verificar "menciona la sintaxis dentro de una explicación" "PASA" \
"$(printf '## Qué cambia\nEl gate buscaba la marca en todo el cuerpo, no solo en listas: `[ ]`.\n- [x] revisado\n')"

verificar "casilla anidada sin marcar" "REPRUEBA" \
"$(printf '## Calidad\n- [x] uno\n  - [ ] sub-ítem pendiente\n')"

verificar "cuerpo sin casillas" "PASA" \
"$(printf 'Solo texto, sin plantilla.\n')"

echo
if [ "$FALLOS" -eq 0 ]; then
  echo "TODOS CORRECTOS"
else
  echo "HAY FALLAS"
  exit 1
fi
