---
name: Correr tests
description: Corre las pruebas del frontend (Edge headless) y del backend (pytest) de GastaMejor y reporta PASS/FAIL
---

# Correr los tests de GastaMejor

Proyecto: `C:\Program Files\misProgramas\API SQL-PY` (repo `JJBrazdaJere/gastamejor`).

## Frontend (HTML/CSS/JS, Edge headless)

Desde `frontend/`:

```powershell
powershell -ExecutionPolicy Bypass -File .\tests\correr-tests.ps1
```

- Requiere: `python` en el PATH y Edge en
  `C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe`.
- Esperado hoy: **373 PASS / 0 FAIL** (el numero crece con el proyecto).
- Codigo de salida: `0` = todo bien, `1` = fallos, `2` = no se pudo leer.
- Alternativa manual: abrir `frontend/pruebas.html` con un servidor local
  (necesita mismo origen para el iframe).

## Backend (Python + PostgreSQL)

Desde la raiz del repo, con el venv:

```powershell
$env:CORREO_MODO = "test"   # no envia correos: imprime el codigo en consola
.\.venv\Scripts\python.exe -m pytest -v
```

- Esperado hoy: **98 passed**.
- Los tests de integracion corren contra PostgreSQL y **revierten** al final
  (`tests/conftest.py`): no dejan datos de prueba.

## Reglas
- Si algo falla, **no** commitear ni publicar hasta arreglarlo.
- En Windows, `git`/`python` escriben en stderr: mira `$LASTEXITCODE` y no te
  fies solo del texto.
