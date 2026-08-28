#!/usr/bin/env bash
# Verifica que el autor no haya dejado casillas sin marcar en la plantilla del PR.
#
# Lee el cuerpo del PR de la variable de entorno PR_BODY. Sale 0 si está completa,
# 1 si quedan casillas del autor sin marcar.
#
# Vive aquí y no dentro de quality_gate.yml para poder probarlo: lo ejercita
# .github/scripts/probar_verificar_plantilla.sh con casos reales. Una sola
# implementación, sin copia que se desincronice.
#
# Historia: US-503 · Corrige BUG-014.
set -uo pipefail

# Solo la parte que le toca al AUTOR. La sección de aprobación es del PM y se marca al
# revisar, así que contarla haría que la plantilla oficial no pudiera pasar su propio gate.
CUERPO_AUTOR=$(printf '%s\n' "${PR_BODY:-}" | sed '/^## Aprobaci/,$d')

# Casillas que la plantilla marca como opcionales: alternativas mutuamente excluyentes
# ("(Alternativa) No usé IA") y condicionales que no aplican a todo PR ("Si toqué esquema…").
# Exigirlas obligaría a mentir para pasar el gate. El marcador es invisible al renderizar y
# cualquier autor puede usarlo donde una casilla genuinamente no aplique.
OPCIONAL='<!-- opcional -->'

# Solo casillas REALES de lista. El patrón anterior buscaba "[ ]" en todo el texto: bastaba
# mencionarlo dentro de una explicación —aunque fuera entre backticks— para reprobar el PR.
PATRON='^[[:space:]]*-[[:space:]]*\[ \]'

CUERPO_AUTOR=$(printf '%s\n' "$CUERPO_AUTOR" | grep -vF "$OPCIONAL")

if printf '%s\n' "$CUERPO_AUTOR" | grep -qE "$PATRON"; then
  echo "❌ Error: quedan casillas sin marcar en la plantilla del Pull Request:"
  printf '%s\n' "$CUERPO_AUTOR" | grep -nE "$PATRON"
  echo ""
  echo "Márcalas con [x] o bórralas si no aplican."
  echo "El check vuelve a correr al editar la descripción; no hace falta un push vacío."
  exit 1
fi

echo "✅ Plantilla completada correctamente."
