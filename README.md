# API SQL-PY

Sistema de gestión en Python conectado a PostgreSQL. Maneja **productos**,
**proveedores**, **clientes**, **empleados** y **ventas**, más **reportes**
de solo lectura. Tiene un **CLI** (menú en consola) y una **interfaz web**
(admin de Django).

El objetivo del proyecto es ser **robusto y seguro**: validaciones centralizadas,
manejo de errores con excepciones, operaciones atómicas y credenciales fuera
del código.

## Requisitos

- Python 3.10 o superior (probado con 3.14)
- PostgreSQL en ejecución
- Dependencias: `psycopg[binary]`, `python-dotenv`, `pytest`, `Django`, `pytest-django`

Se recomienda un entorno virtual:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
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
   PGDATABASE=practica_django
   PGUSER=postgres
   PGPASSWORD=tu_password_aqui

   # --- Django (interfaz web) ---
   DJANGO_SECRET_KEY=cambiar_por_una_clave_secreta_larga
   DJANGO_DEBUG=True
   DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
   ```

> `config.py` carga ese archivo y expone `DB_CONFIG`. Si falta algún dato
> obligatorio (`PGDATABASE`, `PGUSER`, `PGPASSWORD`), el programa avisa y no
> intenta conectarse.

## Bases de datos: `practica_sql` y `practica_django`

El proyecto trabaja ahora contra **`practica_django`**, una copia de la base
original **`practica_sql`** (misma estructura y datos). La migración se hizo así:

1. Respaldo: `pg_dump practica_sql > backups\practica_sql_AAAAMMDD.sql`
2. Crear: `CREATE DATABASE practica_django WITH TEMPLATE template0 ENCODING 'UTF8';`
3. Restaurar: `psql -d practica_django -f backups\practica_sql_AAAAMMDD.sql`
4. Apuntar `PGDATABASE=practica_django` en `.env`.

`practica_sql` queda como respaldo. Tanto el CLI (`main.py`) como el
**admin de Django** usan la **misma** `practica_django`.

## Base de datos: migraciones

Los cambios de estructura de la base viven en `migrations/`, numerados y con
su script de reversión. Se aplican con `psql` (o con el cliente que prefieras):

```powershell
$env:PGPASSWORD = "tu_password"
$psql = "C:\Program Files\PostgreSQL\18\bin\psql.exe"
& $psql -h localhost -U postgres -d practica_django -v ON_ERROR_STOP=1 -f migrations\001_identity_ids.sql
& $psql -h localhost -U postgres -d practica_django -v ON_ERROR_STOP=1 -f migrations\002_constraints.sql
& $psql -h localhost -U postgres -d practica_django -v ON_ERROR_STOP=1 -f migrations\003_precio_unitario.sql
```

| Migración | Qué hace |
|---|---|
| `001_identity_ids` | Autoincremento `IDENTITY` en `clientes`, `empleados` y `ventas` |
| `002_constraints` | `CHECK` de cantidad/precio/stock y `DEFAULT CURRENT_DATE` en `ventas.fecha` |
| `003_precio_unitario` | Agrega `detalle_ventas.precio_unitario` (precio del momento de la venta) |

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

## Interfaz web (Django admin)

Hay una GUI web con el **admin de Django**, en la carpeta `sitio/`. Usa la
**misma** base (`practica_django`). Los modelos son **espejo** de las tablas y
vistas reales y están en `managed = False`: Django nunca crea ni altera las
tablas del proyecto (el esquema lo siguen definiendo las migraciones SQL).

```powershell
cd sitio
..\.venv\Scripts\python.exe manage.py migrate         # crea solo las tablas internas de Django
..\.venv\Scripts\python.exe manage.py createsuperuser
..\.venv\Scripts\python.exe manage.py runserver
```

Luego entrá a http://127.0.0.1:8000/admin/ .

Qué podés hacer:

- Alta/baja/modificación de **productos, proveedores, clientes, empleados**
  y **ventas** (con sus líneas de detalle).
- Ver (solo lectura) los **reportes**: `reporte_stock`, `stock_bajo` y
  `reporte_ventas`.

> El admin **no** aplica las reglas de negocio (descontar stock, validar stock
> suficiente): esas reglas viven en el CLI (`ventas.py`). Por eso registrar una
> venta desde el admin **no** descuenta stock. Para operar con las reglas, usá
> el menú del CLI.

Las tablas internas de Django (`django_*`, `auth_*`, `sessions`) sí se crean
con `migrate`; son las únicas que Django administra.

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
| `empleados.py` | Lógica de empleados |
| `ventas.py` | Lógica de ventas (cabecera + líneas + stock) |
| `reportes.py` | Consultas de solo lectura sobre las vistas |
| `main.py` | Menú / punto de entrada |
| `migrations/` | Cambios de estructura versionados |
| `tests/` | Pruebas automáticas |
| `sitio/` | Proyecto Django (admin web); modelos `managed=False` |
| `backups/` | Respaldos `pg_dump` (fuera de Git) |

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

## Nota sobre los `id`

Todos los `id` los genera la base de datos con `IDENTITY`
(`clientes`, `empleados`, `ventas`, `productos`, `proveedores`) o son clave
compuesta (`detalle_ventas`). El código **nunca** calcula el `id`.
