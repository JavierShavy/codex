# APP de inventario con base de datos (SQLite)

Aplicación web para gestionar inventario de un negocio pequeño usando frontend estático y backend Python con SQLite.

## Funcionalidades

- Alta de productos con nombre, SKU, precio, cantidad y stock mínimo.
- Búsqueda por nombre o SKU.
- Indicador de stock bajo.
- Ajuste rápido de existencias.
- Eliminación de productos.
- Persistencia real en base de datos `SQLite` (`inventory.db`).

## Stack

- Frontend: HTML + CSS + JavaScript.
- Backend: Python (`http.server`).
- Base de datos: SQLite (`sqlite3` de la librería estándar).

## Ejecutar

```bash
python3 server.py
```

Luego abre:

- `http://localhost:4173`

## Trabajar con VSCode

Este repositorio ya incluye configuración en `.vscode/` para que sigas trabajando rápido:

- **Debug**: configuración `Python: server.py` en `Run and Debug`.
- **Tasks**:
  - `Run inventory server`
  - `Check Python syntax`
  - `Check frontend syntax`
- **Recomendaciones de extensiones**: Python, Pylance y Prettier.

Pasos sugeridos en VSCode:

1. Abrir carpeta del proyecto.
2. Instalar extensiones recomendadas cuando VSCode lo sugiera.
3. Ejecutar la tarea **Run inventory server** o iniciar debug con **Python: server.py**.
4. Abrir `http://localhost:4173` en tu navegador.

## API expuesta

- `GET /api/products?q=texto`
- `POST /api/products`
- `PATCH /api/products/:id/quantity`
- `DELETE /api/products/:id`
