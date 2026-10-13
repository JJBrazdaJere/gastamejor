# 💸 GastaMejor

[![Demo en vivo](https://img.shields.io/badge/demo-en%20vivo-2ea44f?logo=githubpages&logoColor=white)](https://jjbrazdajere.github.io/gastamejor/)
[![GitHub Pages](https://img.shields.io/badge/GitHub%20Pages-publicado-222222?logo=github&logoColor=white)](https://jjbrazdajere.github.io/gastamejor/)
[![Licencia: MIT](https://img.shields.io/badge/Licencia-MIT-blue.svg)](LICENSE)

App web de **finanzas personales** para distribuir el ingreso del mes entre
**necesidades, deseos y ahorro**, con perfiles de ahorro, plan de acción mes a
mes, historial y consejero.

El frontend es una app **estática (HTML/CSS/JS vanilla, sin frameworks)** que
funciona 100% en el navegador. El backend es un proyecto **Python + PostgreSQL**
pensado para dar soporte a cuentas de usuario e ingresos diarios.

## 🔗 Demo en vivo

👉 **https://jjbrazdajere.github.io/gastamejor/**

Se publica automáticamente con **GitHub Pages** en cada push a `main`
(workflow `.github/workflows/deploy-pages.yml`).

## ✨ Funcionalidades

- Reparto del ingreso en tres grupos: **Necesidad / Deseo / Ahorro**
  (regla 50/30/20 y otros perfiles).
- Categorías en **porcentaje** o en **monto fijo** (los fijos se reservan primero).
- Gráfico de torta hecho a mano (**SVG**) con leyenda, subtotales y "Sin designar".
- **Exportar a PNG** y **generar link para compartir**.
- Ahorro en **dólares** con cotización en vivo (dólar Bolsa/MEP por defecto).
- Paneles de **Perfiles, Plan, Historial y Consejero**.
- **Ingresos diarios** 💵: si cobrás por día, cargás cada jornada y la app suma
  el mes (con **ingreso fijo mensual** opcional) y lo usa para el reparto.
- **Cuentas de usuario** (opcional): registro con **email verificado**, login y
  teléfono opcional; se puede seguir usando la app como invitado.
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
│   ├── cuenta.html / cuenta.js / api.js  # cuenta + ingresos diarios
│   ├── pruebas.html / pruebas.js      # tests en el navegador
│   ├── tutorial.html / datos-ejemplo.js
│   └── tests/correr-tests.ps1         # runner headless (Edge)
│
├── main.py                    # Backend (Python + PostgreSQL)
├── servidor.py                # API HTTP JSON (y sirve frontend/)
├── config.py, conexion.py, base_datos.py, errores.py, validaciones.py
├── seguridad.py, correo.py, cuentas.py, ingresos.py
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

> ⚠️ **`python -m http.server` sirve solo archivos estáticos.** Con él la app
> funciona en **modo invitado** y se abren `pruebas.html`/`tutorial.html`, pero
> **no** hay cuentas ni ingresos diarios: cualquier `POST /api/...` responde
> **`501`** (o `404`). Para las cuentas usá **`python servidor.py`** (ver abajo).

- Pruebas en el navegador: `frontend/pruebas.html`
- Pruebas headless (Windows + Edge): `frontend/tests/correr-tests.ps1`

### Backend (PostgreSQL)

1. Iniciá **PostgreSQL** (puerto `5432`).
2. Copiá `.env.example` a `.env` y completá tus credenciales.
3. `python -m pip install -r requirements.txt`
4. Aplicá las migraciones de `migrations/` (ver [README-BACKEND.md](README-BACKEND.md)).
5. `python main.py` — menú de consola, **o**
   `python servidor.py` — API HTTP para la app (sirve también `frontend/`, así
   que podés abrir `http://127.0.0.1:8000/cuenta.html` y probar todo junto).
6. Tests: `python -m pytest`

> Las cuentas y los ingresos diarios necesitan el backend encendido. Sin él, la
> app sigue funcionando igual en **modo invitado** (todo local en el navegador).

#### 🛠️ Solución de problemas

- **«Error 501» o «no se encontró la API» al crear una cuenta.** Estás sobre un
  servidor de archivos estáticos (`python -m http.server`) o GitHub Pages, que no
  entienden `/api`. Cortá ese servidor y arrancá `python servidor.py`; después
  abrí `http://127.0.0.1:8000/cuenta.html`. Si publicaste el backend en otro
  lado, pegá su URL en la página de cuenta, sección **«Servidor (avanzado)»**.
- **Un solo servidor por puerto.** `python -m http.server` y `python servidor.py`
  usan el **8000** por defecto: no pueden correr a la vez. Cortá uno (`Ctrl+C`) o
  arrancá el otro en otro puerto, por ejemplo `python servidor.py --puerto 8080`.

## 🧰 Tecnologías

- **Frontend:** HTML5, CSS3, JavaScript (vanilla), SVG.
- **Backend:** Python 3, psycopg 3, PostgreSQL, python-dotenv, pytest.

## 🗺️ Roadmap

- [x] Cuentas de usuario (usuario + contraseña + email; teléfono opcional)
- [x] Verificación de email (en modo test imprime el código; con SMTP envía de verdad)
- [x] Carga de **ingresos diarios** que se suman al total del mes
- [ ] Sincronización de configuración e historial con el backend
- [ ] Publicar el backend en un hosting gratuito (para las cuentas online)

## 📄 Licencia

Este proyecto está bajo la licencia **MIT** — ver [LICENSE](LICENSE).
