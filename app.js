const form = document.getElementById('product-form');
const searchInput = document.getElementById('search');
const tbody = document.getElementById('inventory-body');
const template = document.getElementById('row-template');

let products = [];

function formatCurrency(value) {
  return new Intl.NumberFormat('es-MX', { style: 'currency', currency: 'MXN' }).format(value);
}

function stockStatus(item) {
  return item.quantity <= item.minStock ? 'Bajo' : 'OK';
}

async function fetchProducts() {
  const query = searchInput.value.trim();
  const params = query ? `?q=${encodeURIComponent(query)}` : '';
  const response = await fetch(`/api/products${params}`);

  if (!response.ok) {
    throw new Error('No se pudo cargar el inventario.');
  }

  products = await response.json();
}

function renderTable() {
  tbody.innerHTML = '';

  for (const item of products) {
    const row = template.content.firstElementChild.cloneNode(true);

    row.querySelector('.name').textContent = item.name;
    row.querySelector('.sku').textContent = item.sku;
    row.querySelector('.price').textContent = formatCurrency(item.price);
    row.querySelector('.quantity').textContent = String(item.quantity);
    row.querySelector('.min-stock').textContent = String(item.minStock);

    const status = row.querySelector('.status');
    const state = stockStatus(item);
    status.textContent = state;
    status.className = `status ${state === 'OK' ? 'status-ok' : 'status-low'}`;

    row.querySelector('.delete').addEventListener('click', async () => {
      const response = await fetch(`/api/products/${item.id}`, { method: 'DELETE' });
      if (!response.ok) {
        alert('No se pudo eliminar el producto.');
        return;
      }
      await refresh();
    });

    row.querySelector('.adjust').addEventListener('click', async () => {
      const next = prompt(`Nuevo stock para ${item.name}:`, String(item.quantity));
      if (next === null) return;
      const value = Number.parseInt(next, 10);
      if (Number.isNaN(value) || value < 0) {
        alert('Ingresa una cantidad válida (0 o más).');
        return;
      }

      const response = await fetch(`/api/products/${item.id}/quantity`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ quantity: value }),
      });

      if (!response.ok) {
        alert('No se pudo actualizar el stock.');
        return;
      }

      await refresh();
    });

    tbody.appendChild(row);
  }
}

async function refresh() {
  try {
    await fetchProducts();
    renderTable();
  } catch (error) {
    alert(error.message);
  }
}

form.addEventListener('submit', async (event) => {
  event.preventDefault();

  const product = {
    id: crypto.randomUUID(),
    name: document.getElementById('name').value.trim(),
    sku: document.getElementById('sku').value.trim(),
    price: Number.parseFloat(document.getElementById('price').value),
    quantity: Number.parseInt(document.getElementById('quantity').value, 10),
    minStock: Number.parseInt(document.getElementById('minStock').value, 10),
  };

  const response = await fetch('/api/products', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(product),
  });

  if (!response.ok) {
    const payload = await response.json().catch(() => ({}));
    alert(payload.message || 'No se pudo guardar el producto.');
    return;
  }

  form.reset();
  await refresh();
});

searchInput.addEventListener('input', refresh);

refresh();
