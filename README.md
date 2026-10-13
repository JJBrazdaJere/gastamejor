# 💸 GastaMejor

App web de **finanzas personales** para distribuir el ingreso del mes entre
**necesidades, deseos y ahorro**, con perfiles de ahorro, plan de acción mes a
mes, historial y consejero.

El frontend es una app **estática (HTML/CSS/JS vanilla, sin frameworks)** que
funciona 100% en el navegador. El backend es un proyecto **Python + PostgreSQL**
pensado para dar soporte a cuentas de usuario e ingresos diarios.

## ✨ Funcionalidades

- Reparto del ingreso en tres grupos: **Necesidad / Deseo / Ahorro**
  (regla 50/30/20 y otros perfiles).
- Categorías en **porcentaje** o en **monto fijo** (los fijos se reservan primero).
- Gráfico de torta hecho a mano (**SVG**) con leyenda, subtotales y "Sin designar".
- **Exportar a PNG** y **generar link para compartir**.
- Ahorro en **dólares** con cotización en vivo (dólar Bolsa/MEP por defecto).
- Paneles de **Perfiles, Plan, Historial y Consejero**.
- **Tutorial interactivo**, **tour guiado** y **página de pruebas** (335 tests).
- **Responsive** (mobile-first desde 360px), en español y con formato ARS (`es-AR`).

## 🗂️ Estructura

```
.
├── frontend/                  # App (HTML/CSS/JS vanilla)
│   ├── index.html
│   ├── app.js
│   ├── styles.css
│   ├── storage.js
│   ├── pruebas.html / pruebas.js      # tests en el navegador
│   ├── tutorial.html / datos-ejemplo.js
│   └── tests/correr-tests.ps1         # runner headless (Edge)
│
├── main.py                    # Backend (Python + PostgreSQL)
├── config.py, conexion.py, base_datos.py, errores.py, validaciones.py
├── clientes.py, productos.py, proveedores.py, empleados.py, ventas.py, reportes.py
├── migrations/                # migraciones SQL
├── tests/                     # tests del backend (pytest)
├── requirements.txt
├── .env.example
└── README-BACKEND.md          # documentación detallada del backend
```

## 🚀 Cómo correrlo

### Frontend

Abrí `frontend/index.html` en el navegador (o servilo con
`python -m http.server` desde la carpeta `frontend`).

- Pruebas en el navegador: `frontend/pruebas.html`
- Pruebas headless (Windows + Edge): `frontend/tests/correr-tests.ps1`

### Backend (PostgreSQL)

1. Iniciá **PostgreSQL** (puerto `5432`).
2. Copiá `.env.example` a `.env` y completá tus credenciales.
3. `python -m pip install -r requirements.txt`
4. `python main.py`
5. Tests: `python -m pytest`

## 🧰 Tecnologías

- **Frontend:** HTML5, CSS3, JavaScript (vanilla), SVG.
- **Backend:** Python 3, psycopg 3, PostgreSQL, python-dotenv, pytest.

## 🗺️ Roadmap

- [ ] Cuentas de usuario (usuario + contraseña + email; teléfono opcional)
- [ ] Verificación de email
- [ ] Carga de **ingresos diarios** que se suman al total del mes
- [ ] Sincronización de configuración e historial con el backend

## 📄 Licencia

Este proyecto está bajo la licencia **MIT** — ver [LICENSE](LICENSE).
