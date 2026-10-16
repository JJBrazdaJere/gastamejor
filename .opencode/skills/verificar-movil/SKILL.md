---
name: Verificar movil
description: Verifica el layout responsive (mobile-first, 360px) de las paginas con Edge headless
---

# Verificar el layout movil de GastaMejor

Mobile-first desde **360px**. Edge headless:
`C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe`

## Trampa importante
`--headless=new` **ignora** anchos menores a ~500px (los clampea a ~492).
Para probar 320-420px **no** sirve `--window-size`; usa un **iframe** de ancho
fijo: las media queries usan el viewport del iframe, no el de la ventana.

## Receta (iframe + medicion)
1. Servir la carpeta: `python -m http.server 8799 --bind 127.0.0.1` en `frontend/`.
2. Crear un HTML **temporal** que inserte iframes de 320/360/420 px apuntando a
   la pagina; dentro de la pagina, medir con `getBoundingClientRect()`
   (left/right/top/bottom, `scrollWidth` vs `clientWidth`) y volcar el resultado
   en un `data-*` del `<body>`.
3. Correr:
   ```
   msedge --headless=new --disable-gpu --force-device-scale-factor=1 ^
     --virtual-time-budget=15000 --window-size=1200,1000 ^
     --dump-dom "http://127.0.0.1:8799/_verif.html" > dump.html
   ```
4. Leer `data-result` del dump (ojo: las comillas vienen escapadas como `&quot;`).
5. **Borrar los archivos temporales** antes de commitear.

## Screenshot
```powershell
msedge --headless=new --force-device-scale-factor=1 --window-size=380,1000 `
  --screenshot="C:\Users\Usuario\captura.png" "http://127.0.0.1:8799/index.html"
```

## Que mirar
- Campos que se pisen (ej. Fecha vs Monto en `cuenta.html`).
- Elementos que se salgan del recuadro (`.tarjeta` / `.contenedor`).
- Botones >= 48px y barra de pestanas abajo.
- Solapamiento real = interseccion en **ambos** ejes (no solo el horizontal).
