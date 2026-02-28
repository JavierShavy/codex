import json
import sqlite3
import uuid
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

PORT = 4173
DB_PATH = Path(__file__).with_name('inventory.db')


def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_connection()
    conn.execute(
        '''
        CREATE TABLE IF NOT EXISTS products (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            sku TEXT NOT NULL UNIQUE,
            price REAL NOT NULL,
            quantity INTEGER NOT NULL,
            min_stock INTEGER NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        '''
    )
    conn.commit()
    conn.close()


class InventoryHandler(SimpleHTTPRequestHandler):
    def _json_response(self, status: int, payload: dict | list | None = None):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.end_headers()
        if payload is not None:
            self.wfile.write(json.dumps(payload).encode('utf-8'))

    def _read_json_body(self):
        content_length = int(self.headers.get('Content-Length', '0'))
        if content_length <= 0:
            return {}
        raw = self.rfile.read(content_length)
        return json.loads(raw.decode('utf-8'))

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path != '/api/products':
            return super().do_GET()

        search = parse_qs(parsed.query).get('q', [''])[0].strip().lower()

        conn = get_db_connection()
        if search:
            rows = conn.execute(
                '''
                SELECT id, name, sku, price, quantity, min_stock AS minStock
                FROM products
                WHERE LOWER(name) LIKE ? OR LOWER(sku) LIKE ?
                ORDER BY datetime(created_at) DESC
                ''',
                (f'%{search}%', f'%{search}%'),
            ).fetchall()
        else:
            rows = conn.execute(
                '''
                SELECT id, name, sku, price, quantity, min_stock AS minStock
                FROM products
                ORDER BY datetime(created_at) DESC
                '''
            ).fetchall()
        conn.close()

        products = [dict(row) for row in rows]
        self._json_response(HTTPStatus.OK, products)

    def do_POST(self):
        if self.path != '/api/products':
            self._json_response(HTTPStatus.NOT_FOUND, {'message': 'Ruta no encontrada.'})
            return

        try:
            payload = self._read_json_body()
            product_id = payload.get('id') or str(uuid.uuid4())
            name = payload.get('name', '').strip()
            sku = payload.get('sku', '').strip()
            price = float(payload.get('price'))
            quantity = int(payload.get('quantity'))
            min_stock = int(payload.get('minStock'))
            if not name or not sku or price < 0 or quantity < 0 or min_stock < 0:
                raise ValueError
        except (ValueError, TypeError, json.JSONDecodeError):
            self._json_response(HTTPStatus.BAD_REQUEST, {'message': 'Datos de producto inválidos.'})
            return

        conn = get_db_connection()
        try:
            conn.execute(
                '''
                INSERT INTO products (id, name, sku, price, quantity, min_stock)
                VALUES (?, ?, ?, ?, ?, ?)
                ''',
                (product_id, name, sku, price, quantity, min_stock),
            )
            conn.commit()
            row = conn.execute(
                'SELECT id, name, sku, price, quantity, min_stock AS minStock FROM products WHERE id = ?',
                (product_id,),
            ).fetchone()
            self._json_response(HTTPStatus.CREATED, dict(row))
        except sqlite3.IntegrityError:
            self._json_response(HTTPStatus.CONFLICT, {'message': 'El SKU ya existe. Usa uno distinto.'})
        finally:
            conn.close()

    def do_PATCH(self):
        if not self.path.startswith('/api/products/') or not self.path.endswith('/quantity'):
            self._json_response(HTTPStatus.NOT_FOUND, {'message': 'Ruta no encontrada.'})
            return

        product_id = self.path.split('/')[3]
        try:
            payload = self._read_json_body()
            quantity = int(payload.get('quantity'))
            if quantity < 0:
                raise ValueError
        except (ValueError, TypeError, json.JSONDecodeError):
            self._json_response(HTTPStatus.BAD_REQUEST, {'message': 'Cantidad inválida.'})
            return

        conn = get_db_connection()
        result = conn.execute('UPDATE products SET quantity = ? WHERE id = ?', (quantity, product_id))
        conn.commit()
        conn.close()

        if result.rowcount == 0:
            self._json_response(HTTPStatus.NOT_FOUND, {'message': 'Producto no encontrado.'})
            return
        self._json_response(HTTPStatus.NO_CONTENT)

    def do_DELETE(self):
        if not self.path.startswith('/api/products/'):
            self._json_response(HTTPStatus.NOT_FOUND, {'message': 'Ruta no encontrada.'})
            return

        product_id = self.path.split('/')[3]
        conn = get_db_connection()
        result = conn.execute('DELETE FROM products WHERE id = ?', (product_id,))
        conn.commit()
        conn.close()

        if result.rowcount == 0:
            self._json_response(HTTPStatus.NOT_FOUND, {'message': 'Producto no encontrado.'})
            return

        self._json_response(HTTPStatus.NO_CONTENT)


if __name__ == '__main__':
    init_db()
    server = ThreadingHTTPServer(('0.0.0.0', PORT), InventoryHandler)
    print(f'Servidor de inventario activo en http://localhost:{PORT}')
    server.serve_forever()
