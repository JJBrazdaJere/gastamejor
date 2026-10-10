# API SQL-PY

Sistema de gestión en Python conectado a PostgreSQL. Por ahora maneja
**productos**, **proveedores** y **clientes**; está pensado para seguir
agregando módulos (empleados, ventas...).

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

## Uso

```powershell
python main.py
```

Se abre un menú:

```
=== SISTEMA DE GESTIÓN ===
1) Productos
2) Proveedores
0) Salir
```

Cada entidad tiene su submenú: listar, ver por ID, agregar, actualizar y eliminar.

## Tests

```powershell
python -m pytest -v
```

- **Unitarios** (`tests/test_validaciones.py`): validan las funciones de
  validación sin tocar la base.
- **Integración** (`tests/test_integridad.py`): ejecutan CRUD real pero dentro
  de una transacción que **se revierte al final**, así no quedan datos de prueba.

## Estructura

| Archivo | Responsabilidad |
|---|---|
| `conexion.py` | Crear la conexión a PostgreSQL |
| `config.py` | Leer el `.env` y exponer `DB_CONFIG` |
| `base_datos.py` | Helpers genéricos `leer_db` / `commit_db` |
| `productos.py` | Lógica y validaciones de productos |
| `proveedores.py` | Lógica y validaciones de proveedores |
| `clientes.py` | Lógica y validaciones de clientes (plantilla) |
| `main.py` | Menú / punto de entrada |
| `tests/` | Pruebas automáticas |

## Nota sobre los `id`

- `productos` y `proveedores` tienen **identidad** en la base (el `id` se genera solo).
- `clientes` (y también `empleados`, `ventas`) **no** tienen auto-incremento.
  Por eso `agregar_cliente` calcula el id con `COALESCE(MAX(id),0)+1`.
  Es suficiente para practicar; para producción convendría una secuencia/IDENTITY
  en la base de datos.
