---
name: Publicar frontend
description: Publica GastaMejor en GitHub Pages (tests, commit, push a main y verificacion en vivo)
---

# Publicar el frontend de GastaMejor

Repo: `C:\Program Files\misProgramas\API SQL-PY` -> `https://github.com/JJBrazdaJere/gastamejor`.

GitHub Pages se publica **desde `frontend/`** con
`.github/workflows/deploy-pages.yml`, disparado por **push a `main`**.
Sitio: `https://jjbrazdajere.github.io/gastamejor/`.

## Pasos
1. **Tests primero** (skill `correr-tests`): que de todo PASS.
2. Ver que cambio: `git -C "C:\Program Files\misProgramas\API SQL-PY" status --short`.
3. `git add <archivos>` y commit con mensaje claro en espanol.
4. `git push origin main`.
5. Esperar ~30-60 s y **verificar en vivo con cache-buster**:
   ```powershell
   $cb = [guid]::NewGuid()
   (Invoke-WebRequest "https://jjbrazdajere.github.io/gastamejor/styles.css?cb=$cb" -UseBasicParsing).Content
   ```
   Confirma que el archivo trae el cambio (una regla/version concreta).

## Reglas
- **Nunca** commitear `.env` (ya esta en `.gitignore`).
- En PowerShell 5.1 `git` escribe en stderr: comprueba `$LASTEXITCODE`.
- Verifica contra la URL en vivo, no contra el local.
- Si toca el backend (Render), eso es aparte: este flujo es solo Pages (frontend).
