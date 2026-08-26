# DevLog — 2026-08-26 — Eloisa González Rubio

## Historia: US-421

- Se recibió retroalimentación sobre el código de US-421: aprobado para hacer push desde la rama propia.
- Se resolvió el conflicto de puerto: API_PORT cambiado de 8000 a 8080 en .env local, según indicación recibida.
- Se detectó que curl no respondía por el proxy corporativo de HP (http_proxy=127.0.0.1:9000) interceptando conexiones a localhost.
- Solución aplicada: se agregó NO_PROXY=localhost,127.0.0.1 al archivo .env.
- Verificado con: curl --noproxy "*" http://127.0.0.1:8080/health → HTTP/1.1 200 OK, status "healthy".
