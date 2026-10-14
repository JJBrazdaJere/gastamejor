# Publicar el backend de GastaMejor (gratis)

Esta guía deja la API de cuentas **en internet**, para que el sitio de
GitHub Pages pueda registrar usuarios, iniciar sesión y mandar el código
de verificación por email.

## Arquitectura

```
GitHub Pages (frontend estático)  ->  Render (backend Python, gratis)  ->  Neon (PostgreSQL, gratis)
                                                    \->  API HTTP de Brevo (email, HTTPS)
```

- **Render** ejecuta `servidor.py`. Duerme a los 15 min de inactividad
  (el primer acceso tarda ~1 min en despertar).
- **Neon** guarda la base. Es gratis y no expira (0.5 GB).
- **Brevo** manda los correos por su **API HTTP** (puerto 443). Se usa la
  API y no SMTP porque **Render free bloquea los puertos SMTP** (25/465/587).

> Render free bloquea SMTP desde septiembre 2025. Por eso `CORREO_MODO=api`.

---

## Paso 1 — Base de datos en Neon

1. Entrá a <https://neon.com> y creá una cuenta gratis (sin tarjeta).
2. **New Project** → elegí una región cercana (ej. `us-east-1` / Ohio).
3. Copiá la **Connection string** (la que incluye `sslmode=require`).
   Se ve así:
   ```
   postgresql://USUARIO:CLAVE@ep-xxxx.us-east-2.aws.neon.tech/neondb?sslmode=require
   ```
4. Separá esos datos (los vas a cargar en Render):

   | Variable  | Valor del ejemplo        |
   |-----------|--------------------------|
   | `PGHOST`    | `ep-xxxx.us-east-2.aws.neon.tech` |
   | `PGPORT`    | `5432`                   |
   | `PGDATABASE`| `neondb`                 |
   | `PGUSER`    | `USUARIO`                |
   | `PGPASSWORD`| `CLAVE`                  |
   | `PGSSLMODE` | `require`                |

   > ⚠️ **Importante — usá el host SIN `-pooler`.** Neon da dos hosts: uno con
   > `-pooler` (PgBouncer) y uno directo. El **pooler deja `search_path` vacío**
   > y además rechaza `search_path`, así que la app **no encontraría las
   > tablas**. Usá el host **directo** (sin `-pooler`), por ejemplo
   > `ep-xxxx.us-east-2.aws.neon.tech`, y asegurate de tener
   > `search_path` en `public` (se deja así con una sola vez:
   > `ALTER DATABASE neondb SET search_path TO public;`).

## Paso 2 — Crear las tablas en Neon

Ojo: las migraciones de `migrations/` solo **modifican** un esquema que ya
existía (no crean las tablas base). Para una base nueva lo más simple y
seguro es **copiar el esquema de tu base local**. Con PostgreSQL instalado:

```powershell
# 1) Volcar SOLO el esquema de la base local (sin datos)
$env:PGPASSWORD = "TU_CLAVE_LOCAL"
& pg_dump --schema-only --no-owner --no-privileges -h localhost -U postgres -d practica_sql -f esquema.sql

# 2) Cargarlo en Neon (host DIRECTO, sin -pooler)
$env:PGPASSWORD = "CLAVE_NEON"
$url = "postgresql://USUARIO:CLAVE@ep-xxxx.us-east-2.aws.neon.tech/neondb?sslmode=require"
& psql -d $url -v ON_ERROR_STOP=1 -f esquema.sql

# 3) Dejar search_path en public (una sola vez)
& psql -d $url -c "ALTER DATABASE neondb SET search_path TO public;"

# 4) Verificar
& psql -d $url -c "\dt"
& psql -d $url -c "select count(*) from clientes;"
```

> Si preferís arrancar de cero, primero creá las tablas base y después sí
> aplicá las migraciones en orden (ignorando las `*_rollback.sql`).

## Paso 3 — Clave de la API de Brevo

1. En Brevo: **Settings → SMTP & API → API Keys → Create a new API key**.
2. Copiala (empieza con `xkeysib-...`). Esa es `BREVO_API_KEY`.
   No confundir con la clave SMTP (`xsmtpsib-...`), que no se usa acá.
3. Asegurate de tener verificado el remitente
   (`jerebrazda7@gmail.com`) en **Senders**.

## Paso 4 — Desplegar en Render

1. Entrá a <https://render.com> y creá una cuenta gratis (sin tarjeta).
2. **New → Blueprint** → conectá el repo `JJBrazdaJere/gastamejor`.
3. Render lee `render.yaml` y te pide completar las variables `sync: false`:
   - `PGHOST`, `PGDATABASE`, `PGUSER`, `PGPASSWORD` (los de Neon, Paso 1)
   - `BREVO_API_KEY` (Paso 3)
4. **Apply / Deploy** y esperá el build.
5. Cuando termine, copiá la URL del servicio, por ejemplo:
   ```
   https://gastamejor-api.onrender.com
   ```
6. Probá: abrí `https://gastamejor-api.onrender.com/api/salud`
   → tiene que responder `{"ok":true,"db":true}`.

> Alternativa sin Blueprint: **New → Web Service** → repo → Build Command
> `pip install -r requirements.txt` → Start Command `python servidor.py`,
> y cargá TODAS las variables de `render.yaml` a mano en **Environment**.

## Paso 5 — Apuntar el frontend al backend

Editá `frontend/config.js` y poné la URL de Render:

```js
var URL_BACKEND = "https://gastamejor-api.onrender.com";
```

Después `git commit` + `git push`. A partir de ahí, el sitio de Pages
usa ese backend para las cuentas.

---

## Probar

1. Abrí <https://jjbrazdajere.github.io/gastamejor/cuenta.html>.
2. "Crear cuenta" → poné un email real → debería llegar el código.
3. Verificá y entrá.

## Alternativa 100 % local

Si no querés publicar nada, el backend local ya sirve:

```powershell
python servidor.py
# y abrí http://127.0.0.1:8000/cuenta.html
```

## Notas

- `CORREO_MODO=api` usa la API de Brevo (HTTPS). `smtp` y `test` siguen
  disponibles para desarrollo local.
- Las credenciales viven **solo** en el panel de Render y en el `.env`
  local. Nunca se suben al repo (`.env` está en `.gitignore`).
- La base gratis de Neon es chica (0.5 GB) pero sobra para este proyecto.
- Render free duerme por inactividad; el primer request puede tardar ~1 min.
