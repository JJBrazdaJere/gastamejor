# API SQL-PY

Sistema de gestión en Python conectado a PostgreSQL. Maneja **productos**,
**proveedores**, **clientes**, **empleados** y **ventas**, más **reportes**
de solo lectura. Está pensado para seguir creciendo (por ejemplo, con una
interfaz web con Django).

El objetivo del proyecto es ser **robusto y seguro**: validaciones centralizadas,
manejo de errores con excepciones, operaciones atómicas y credenciales fuera
del código.

## Requisitos

- Python 3.10 o superior (probado con 3.14)
- PostgreSQL en ejecución
- Dependencias: `psycopg`, `python-dotenv`, `pytest`

```powershell
python -m pip install -r requirements.txt
```

## Configuración (credenciales)

Las credenciales **no** están en el código: se leen del archivo `.env`,
que está excluido de Git (`.gitignore`).

1. Copiá la plantilla:

   ```powershell
   Copy-Item .env.example .env
   ```

2. Editá `.env` con tus datos reales:

   ```
   PGHOST=localhost
   PGPORT=5432
   PGDATABASE=practica_sql
   PGUSER=postgres
   PGPASSWORD=tu_password_aqui
   ```

> `config.py` carga ese archivo y expone `DB_CONFIG`. Si falta algún dato
> obligatorio (`PGDATABASE`, `PGUSER`, `PGPASSWORD`), el programa avisa y no
> intenta conectarse.

## Base de datos: migraciones

Los cambios de estructura de la base viven en `migrations/`, numerados y con
su script de reversión. Se aplican con `psql` (o con el cliente que prefieras):

```powershell
$env:PGPASSWORD = "tu_password"
$psql = "C:\Program Files\PostgreSQL\18\bin\psql.exe"
& $psql -h localhost -U postgres -d practica_sql -v ON_ERROR_STOP=1 -f migrations\001_identity_ids.sql
& $psql -h localhost -U postgres -d practica_sql -v ON_ERROR_STOP=1 -f migrations\002_constraints.sql
& $psql -h localhost -U postgres -d practica_sql -v ON_ERROR_STOP=1 -f migrations\003_precio_unitario.sql
& $psql -h localhost -U postgres -d practica_sql -v ON_ERROR_STOP=1 -f migrations\004_clientes_auth.sql
& $psql -h localhost -U postgres -d practica_sql -v ON_ERROR_STOP=1 -f migrations\005_ingresos.sql
& $psql -h localhost -U postgres -d practica_sql -v ON_ERROR_STOP=1 -f migrations\006_sesiones.sql
& $psql -h localhost -U postgres -d practica_sql -v ON_ERROR_STOP=1 -f migrations\007_vista_ingresos_mes.sql
& $psql -h localhost -U postgres -d practica_sql -v ON_ERROR_STOP=1 -f migrations\008_recuperacion.sql
```

| Migración | Qué hace |
|---|---|
| `001_identity_ids` | Autoincremento `IDENTITY` en `clientes`, `empleados` y `ventas` |
| `002_constraints` | `CHECK` de cantidad/precio/stock y `DEFAULT CURRENT_DATE` en `ventas.fecha` |
| `003_precio_unitario` | Agrega `detalle_ventas.precio_unitario` (precio del momento de la venta) |
| `004_clientes_auth` | Cuenta de usuario: `usuario`, `password_hash`, `email_verificado`, código de verificación, `ingreso_fijo_mensual`, `moneda` |
| `005_ingresos` | Tabla `ingresos` (ingresos **diarios** por usuario) |
| `006_sesiones` | Tabla `sesiones` (tokens de login con vencimiento) |
| `007_vista_ingresos_mes` | Vista `ingresos_mes` (total y cantidad de ingresos por usuario y mes) |
| `008_recuperacion` | Recuperar contraseña: código de recuperación, vencimiento, intentos y último envío |

Cada archivo `NOMBRE_rollback.sql` revierte su migración.

## Uso

```powershell
python main.py
```

Se abre un menú:

```
=== SISTEMA DE GESTION ===
1) Productos
2) Proveedores
3) Clientes
4) Empleados
5) Ventas
6) Reportes
0) Salir
```

Cada entidad tiene su submenú (listar, ver por ID, agregar, actualizar, eliminar).
**Ventas** permite registrar (descuenta stock) y anular (devuelve stock).
**Reportes** es de solo lectura.

> Los textos se imprimen sin acentos a propósito (compatibilidad con consolas
> antiguas); la salida se fuerza a UTF-8 para que sí se vean los acentos de los
> **datos**.

## Cuentas de usuario e ingresos diarios

El proyecto también incluye cuentas de usuario (login con email verificado,
teléfono opcional) e **ingresos diarios**: cada usuario carga lo que gana cada
día y el total del mes es la suma de esos ingresos **más** su
`ingreso_fijo_mensual` (opcional).

- `cuentas.py`: registro, verificación de email, login/sesión, perfil, cambio
  de contraseña, **recuperación de contraseña** (código por email con
  vencimiento, enfriamiento entre pedidos y auto-login) y **eliminación de
  cuenta** (con contraseña; en cascada borra ingresos y sesiones). Usa la tabla
  `clientes` (ampliada por las migraciones 004 y 008).
- `ingresos.py`: alta/baja/listado de ingresos diarios y resúmenes por mes/año.
- `seguridad.py`: **scrypt** con sal aleatoria para las contraseñas, tokens de
  sesión y códigos de verificación aleatorios.
- `correo.py`: envío de correos. Por defecto `CORREO_MODO=test`: **no envía**,
  imprime el código en la consola (ideal para probar). Con `CORREO_MODO=smtp`
  y datos SMTP en el `.env` envía de verdad.

## API HTTP (`servidor.py`)

El frontend es estático, así que el backend se expone con un servidor HTTP
JSON (solo biblioteca estándar + psycopg, sin frameworks):

```powershell
python servidor.py                 # http://127.0.0.1:8000
python servidor.py --puerto 8080   # otro puerto
```

Además de la API, sirve los archivos de `frontend/`, así que abriendo
`http://127.0.0.1:8000/cuenta.html` se prueba todo local en un solo servidor
(el frontend usa por defecto la misma dirección).

> ⚠️ **No lo reemplaces por `python -m http.server`.** Un servidor de archivos
> sirve solo el frontend estático: no entiende `/api`, así que un
> `POST /api/...` responde `501`/`404` y las cuentas no funcionan. Para la API
> usá `servidor.py`.
>
> ⚠️ **Un solo servidor por puerto.** `servidor.py` y `python -m http.server`
> usan el **8000** por defecto: no pueden correr juntos. Cortá uno (`Ctrl+C`) o
> cambiá el puerto con `python servidor.py --puerto 8080`.

Además de `GET`, `POST`, `PATCH` y `DELETE`, el servidor responde `HEAD` (como
`GET`, sin cuerpo). Cualquier otro verbo (`PUT`, `TRACE`, …) y los `POST` sobre
archivos estáticos devuelven **`405` en JSON** con la cabecera `Allow`, en vez
del `501` en HTML que da `http.server` por defecto.

| Método | Ruta | Qué hace |
|---|---|---|
| GET | `/api/salud` | Estado del servidor y la base |
| POST | `/api/registro` | Crea la cuenta y envía el código |
| POST | `/api/verificar` | Verifica el email con el código |
| POST | `/api/reenviar` | Reenvía el código de verificación |
| POST | `/api/login` | Inicia sesión → `token` |
| POST | `/api/recuperar` | Envía un código para recuperar la contraseña (`email`) |
| POST | `/api/restablecer` | Cambia la contraseña con el código (`email`, `codigo`, `nueva`) y devuelve `token` |
| POST | `/api/logout` | Cierra la sesión |
| GET | `/api/perfil` | Datos de la cuenta |
| PATCH | `/api/perfil` | Actualiza teléfono / ingreso fijo / moneda |
| POST | `/api/password` | Cambia la contraseña |
| DELETE | `/api/cuenta` | Borra la cuenta (pide `password`) y todos sus datos |
| GET | `/api/ingresos?mes=AAAA-MM` | Lista los ingresos (de un mes o todos) |
| POST | `/api/ingresos` | Agrega un ingreso diario |
| DELETE | `/api/ingresos/{id}` | Elimina un ingreso |
| GET | `/api/resumen?mes=AAAA-MM` | Totales del mes (diarios + fijo) |
| GET | `/api/resumen/anual?anio=AAAA` | Totales mes a mes del año |

La autenticación usa el encabezado `Authorization: Bearer <token>`.

El dinero viaja como **texto con 2 decimales** (ej. `"3500.50"`), nunca como
`float`, para no arrastrar errores de redondeo.

## Tests

```powershell
python -m pytest -v
```

- **Unitarios** (`tests/test_validaciones.py`): prueban las validaciones sin
  tocar la base.
- **Integración** (`tests/test_*.py`): ejecutan operaciones reales contra
  PostgreSQL, pero dentro de una transacción que **se revierte al final**
  (ver `tests/conftest.py`). Un fallo dentro de un test usa **savepoints**, así
  no borra lo ya preparado en ese mismo test. No quedan datos de prueba.

Las **secuencias** de los `id` sí avanzan aunque el test se revierta (es normal:
PostgreSQL no revierte los `nextval`).

## Arquitectura

La lógica de negocio está separada de la presentación:

- Los módulos de dominio (`productos`, `proveedores`, ...) **no imprimen**:
  devuelven datos o levantan una excepción.
- `main.py` solo pide datos, muestra resultados y avisa de los errores.
- Los errores son excepciones propias (`errores.py`), lo que permite reutilizar
  la lógica en una futura interfaz gráfica o web sin reescribirla.

| Archivo | Responsabilidad |
|---|---|
| `conexion.py` | Crear la conexión (en `autocommit`) |
| `config.py` | Leer el `.env` y exponer `DB_CONFIG` |
| `base_datos.py` | Acceso genérico + `transaccion()` (atomicidad) |
| `errores.py` | Excepciones propias del sistema |
| `validaciones.py` | Validaciones reutilizables (`validar_email`, etc.) |
| `productos.py` | Lógica de productos |
| `proveedores.py` | Lógica de proveedores |
| `clientes.py` | Lógica de clientes |
| `cuentas.py` | Cuentas de usuario (registro, verificación, login, perfil) |
| `ingresos.py` | Ingresos diarios y resúmenes por mes/año |
| `seguridad.py` | Hash de contraseñas (scrypt), tokens y códigos |
| `correo.py` | Envío de correos (con modo test) |
| `empleados.py` | Lógica de empleados |
| `ventas.py` | Lógica de ventas (cabecera + líneas + stock) |
| `reportes.py` | Consultas de solo lectura sobre las vistas |
| `main.py` | Menú / punto de entrada de consola |
| `servidor.py` | API HTTP JSON (y sirve el `frontend/`) |
| `migrations/` | Cambios de estructura versionados |
| `tests/` | Pruebas automáticas |

## Transacciones (atomicidad)

`base_datos.transaccion(db)` agrupa varias operaciones: se confirman todas
juntas o se revierten todas. Es lo que hace que registrar una venta
(cabecera + líneas + descuento de stock) nunca quede a medias:

```python
with transaccion(db):
    ejecutar(db, "INSERT INTO ventas ...")
    ejecutar(db, "INSERT INTO detalle_ventas ...")
    ejecutar(db, "UPDATE productos SET stock = stock - %s ...")
```

Si ya hay una transacción en curso, usa un **SAVEPOINT** automáticamente.

## Decisiones de robustez

- **Dinero con `Decimal`**: precios y salarios se guardan como `numeric` y se
  validan con `Decimal` (no `float`), evitando errores de redondeo.
- **Enteros estrictos**: `validar_entero` rechaza decimales (Python truncaría
  `1.5` a `1`, peligroso para stock o cantidades).
- **Bloqueo ordenado en ventas**: los bloqueos de producto se toman en orden
  de `producto_id`, para no provocar *deadlocks* entre ventas concurrentes.
- **`%` literal seguro**: una consulta como `LIKE 'a%'` no se confunde con un
  marcador aunque se pase una tupla de parámetros vacía.
- **Contraseñas con `scrypt` + sal aleatoria**: nunca se guarda la contraseña;
  la comparación usa `hmac.compare_digest` (tiempo constante).
- **Tokens de sesión aleatorios** (256 bits) con vencimiento en la base.
- **Códigos de verificación** con vencimiento y comparación segura.
- **Mismo mensaje de error** para usuario inexistente y contraseña incorrecta,
  para no dar pistas a quien intenta adivinar.
- **CORS configurable** (`API_ORIGENES`) y **servido de archivos estáticos** con
  control de rutas (evita salir de `frontend/`).
- **Método no permitido = `405` JSON**: los verbos sin manejador (`PUT`, `TRACE`,
  …) y los `POST` sobre archivos estáticos responden `405` con la cabecera
  `Allow`, en lugar del `501` en HTML de `http.server`. Mensajes claros para
  distinguir «el backend no está» de un error real de la API.

## Nota sobre los `id`

Todos los `id` los genera la base de datos con `IDENTITY`
(`clientes`, `empleados`, `ventas`, `productos`, `proveedores`) o son clave
compuesta (`detalle_ventas`). El código **nunca** calcula el `id`.
