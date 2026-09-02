#!/usr/bin/env python3
"""Verifica que un Pull Request respete la identidad, la rama y el alcance de su autor.

Lee `vault/_Meta/ownership.yml` —la fuente única— y comprueba tres cosas sobre el PR:

1. **Identidad reconocida.** El handle de GitHub del autor existe en el padrón.
2. **Rama correcta.** El PR sale de `dev/{identidad}` y de ninguna otra. Esto es lo que
   impide que reaparezcan ramas gemelas: una rama con el apellido materno, con el segundo
   nombre o con el nombre de una historia no pasa de aquí.
3. **Alcance respetado.** Cada archivo tocado cae en el verde o el amarillo de esa persona,
   o en las rutas comunes a todos.

Además avisa —sin reprobar— cuando el PR toca una ruta crítica de otra persona, para que el
revisor sepa a quién pedirle la revisión del área (regla 7 de Vault_Rules).

Sin dependencias externas: el gate corre en un job que no instala nada, igual que
`vault_lint.py`. Por eso el YAML se lee con un intérprete mínimo del subconjunto que usa
`ownership.yml`, no con PyYAML.

Uso:
    python3 vault/_Meta/scripts/check_ownership.py --autor <login> --rama <ref> [--base origin/main]

Variables de entorno equivalentes: PR_AUTHOR, PR_BRANCH, PR_BASE.
"""

import argparse
import fnmatch
import os
import re
import subprocess
import sys
import unicodedata

OWNERSHIP = "vault/_Meta/ownership.yml"

# [Nombre Apellido] - descripción (ID) - [sync|CI|DoF|DevLog]
TITULO = re.compile(
    r"^\[(?P<nombre>[^\]]+)\]\s*-\s*(?P<desc>.+?)\s*"
    r"\((?P<id>(US|REQ|AC|ADR|TASK|TEST|BUG|SEC|RISK|INC|DEC|DS|ML)-[0-9]+[a-z]?"
    r"(?:\s*[,/]\s*(US|REQ|AC|ADR|TASK|TEST|BUG|SEC|RISK|INC|DEC|DS|ML)-[0-9]+[a-z]?)*)\)"
    r"\s*-\s*\[sync\|CI\|DoF\|DevLog\]$"
)


def _plano(texto):
    """Minúsculas, sin acentos y con los espacios colapsados, para comparar nombres."""
    sin = "".join(c for c in unicodedata.normalize("NFD", texto)
                  if unicodedata.category(c) != "Mn")
    return " ".join(sin.lower().split())


def leer_ownership(ruta):
    """Intérprete mínimo del subconjunto de YAML que usa ownership.yml.

    Soporta exactamente lo que el archivo necesita: mapas anidados por indentación,
    listas de cadenas con `- `, escalares con y sin comillas, y comentarios `#`.
    """
    raiz = {}
    pila = [(-1, raiz)]
    with open(ruta, encoding="utf-8") as fh:
        for cruda in fh:
            linea = cruda.split("#")[0].rstrip() if not cruda.lstrip().startswith("#") else ""
            if not linea.strip():
                continue
            sangria = len(linea) - len(linea.lstrip())
            texto = linea.strip()

            while pila and sangria <= pila[-1][0]:
                pila.pop()
            contenedor = pila[-1][1]

            if texto.startswith("- "):
                valor = texto[2:].strip().strip('"').strip("'")
                if hasattr(contenedor, "append"):
                    contenedor.append(valor)
                continue

            clave, _, resto = texto.partition(":")
            clave = clave.strip().strip('"').strip("'")
            resto = resto.strip()
            if resto:
                contenedor[clave] = resto.strip('"').strip("'")
            else:
                # Se decide lista o mapa al ver la primera línea hija.
                nuevo = _Pendiente()
                contenedor[clave] = nuevo
                pila.append((sangria, nuevo))
    return _resolver(raiz)


class _Pendiente(dict):
    """Contenedor cuyo tipo (mapa o lista) se decide al recibir su primer hijo."""

    def __init__(self):
        super().__init__()
        self.items_lista = []

    def append(self, valor):
        self.items_lista.append(valor)


def _resolver(nodo):
    if isinstance(nodo, _Pendiente):
        if nodo.items_lista:
            return nodo.items_lista
        return {k: _resolver(v) for k, v in nodo.items()}
    if isinstance(nodo, dict):
        return {k: _resolver(v) for k, v in nodo.items()}
    return nodo


def _display(identidad):
    """`diana-alvarez` -> `Diana Alvarez`: cómo se firma un PR."""
    return " ".join(parte.capitalize() for parte in identidad.split("-"))


def coincide(ruta, patrones):
    """¿La ruta cae bajo alguno de los patrones glob? `a/**` cubre también `a/` completo."""
    for patron in patrones:
        if fnmatch.fnmatch(ruta, patron):
            return True
        if patron.endswith("/**") and ruta.startswith(patron[:-2]):
            return True
    return False


def archivos_cambiados(base):
    """Archivos que el PR toca frente a su punto de divergencia con la base."""
    try:
        punto = subprocess.run(
            ["git", "merge-base", base, "HEAD"],
            capture_output=True, text=True, check=True,
        ).stdout.strip()
    except subprocess.CalledProcessError:
        punto = base
    salida = subprocess.run(
        ["git", "diff", "--name-only", f"{punto}...HEAD"],
        capture_output=True, text=True, check=True,
    ).stdout
    return [linea for linea in salida.splitlines() if linea.strip()]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--autor", default=os.environ.get("PR_AUTHOR", ""))
    ap.add_argument("--rama", default=os.environ.get("PR_BRANCH", ""))
    ap.add_argument("--base", default=os.environ.get("PR_BASE", "origin/main"))
    ap.add_argument("--titulo", default=os.environ.get("PR_TITLE", ""))
    args = ap.parse_args()

    if not os.path.exists(OWNERSHIP):
        print(f"❌ No se encontró {OWNERSHIP}")
        return 1

    datos = leer_ownership(OWNERSHIP)
    personas = datos.get("personas", {})
    comunes = datos.get("comunes", [])
    criticos = datos.get("criticos", {})

    autor = args.autor.strip()
    if not autor:
        print("❌ Falta el autor del PR (--autor o PR_AUTHOR).")
        return 1

    por_handle = {d["github"].lower(): (pid, d) for pid, d in personas.items()}
    if autor.lower() not in por_handle:
        print(f"❌ El handle de GitHub `{autor}` no está en el padrón de {OWNERSHIP}.")
        print("   Toda persona que contribuye tiene que estar registrada ahí, con su")
        print("   identidad, su rama y su alcance. Pídele al PM que te dé de alta.")
        return 1
    identidad, persona = por_handle[autor.lower()]

    print(f"Autor      : {persona['nombre']}  (@{autor})")
    print(f"Identidad  : {identidad}")

    problemas = 0

    # ── 1. La rama tiene que ser la rama fija de esa persona ──────────────────
    esperada = persona["rama"]
    rama = args.rama.strip().replace("refs/heads/", "")
    if rama and rama != esperada:
        print(f"\n❌ Rama incorrecta: `{rama}`")
        print(f"   {persona['nombre']} trabaja siempre en `{esperada}`, su única rama.")
        print("   No se abren ramas por historia, por sprint ni por tema.")
        problemas += 1
    elif rama:
        print(f"Rama       : {rama} ✅")

    # ── 2. El título del PR sigue el estándar y va firmado por su autor ───────
    titulo = args.titulo.strip()
    if titulo:
        m = TITULO.match(titulo)
        if not m:
            print(f"\n❌ Título fuera de estándar: {titulo}")
            print("   Formato: [Nombre Apellido] - Descripción concisa (ID) - [sync|CI|DoF|DevLog]")
            print(f"   Ejemplo: [{_display(identidad)}] - Extractor de CEMABE con reintentos "
                  "(US-113) - [sync|CI|DoF|DevLog]")
            problemas += 1
        else:
            firmado = _plano(m.group("nombre"))
            validos = {_plano(identidad.replace("-", " ")), _plano(persona["nombre"])}
            if firmado not in validos:
                print(f"\n❌ El PR va firmado como «{m.group('nombre')}», que no es su autor.")
                print(f"   {persona['nombre']} firma como «{_display(identidad)}».")
                problemas += 1
            else:
                print(f"Título     : {m.group('id')} ✅")

    # ── 3. Todo lo tocado cae en su alcance ───────────────────────────────────
    permitido = list(persona.get("verde", [])) + list(persona.get("amarillo", []))
    permitido += [p.replace("{id}", identidad) for p in comunes]
    permitido.append(persona["plan"])

    cambios = archivos_cambiados(args.base)
    fuera = [f for f in cambios if not coincide(f, permitido)]

    print(f"\nArchivos tocados: {len(cambios)}")
    if fuera:
        print(f"\n❌ {len(fuera)} archivo(s) fuera del alcance de {persona['nombre']}:")
        for f in sorted(fuera):
            dueno = next((d for pat, d in criticos.items() if coincide(f, [pat])), None)
            extra = f"  → dueño: {dueno}" if dueno else ""
            print(f"     {f}{extra}")
        print("\n   Su alcance está en:")
        print(f"     vault/09_AI_Governance/Agent_Contexts/{identidad}-agent-context.md")
        print("   Para tocar algo ajeno: pídeselo a su dueño y que él lo lleve en su rama.")
        problemas += 1
    else:
        print("   Todos dentro de su alcance ✅")

    # ── 4. Aviso (no reprueba) sobre rutas críticas de otra persona ───────────
    avisos = {}
    for f in cambios:
        for patron, dueno in criticos.items():
            if coincide(f, [patron]) and dueno != identidad:
                avisos.setdefault(dueno, set()).add(patron)
    if avisos:
        print("\n⚠️  Toca rutas críticas de otra persona (regla 7 de Vault_Rules).")
        print("   Pide su revisión en el PR antes de mergear:")
        for dueno, patrones in sorted(avisos.items()):
            quien = personas.get(dueno, {}).get("nombre", dueno)
            print(f"     {quien:38} {', '.join(sorted(patrones))}")

    if problemas:
        print(f"\n❌ {problemas} problema(s) de propiedad. El PR no puede mergearse así.")
        return 1
    print("\n✅ Identidad, rama y alcance correctos.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
