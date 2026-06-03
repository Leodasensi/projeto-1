// Script da página de Busca
document.addEventListener('DOMContentLoaded', () => {
  const searchInput = document.getElementById('searchInput');
  const searchBtn = document.getElementById('searchBtn');
  const resultsInfo = document.getElementById('resultsInfo');
  const filterPills = document.getElementById('filterPills');
  const sortSelect = document.getElementById('sortSelect');
  const productsGrid = document.getElementById('productsGrid');
  const menuToggle = document.querySelector('.menu-toggle');
  const navLinks = document.querySelector('.nav-links');

  // Parâmetros da URL
  const urlParams = new URLSearchParams(window.location.search);
  const initialQuery = urlParams.get('q') || '';
  const initialCategory = urlParams.get('category') || 'all';

  let currentQuery = initialQuery;
  let currentCategory = initialCategory;
  let currentSort = 'discount';

  // Inicializar input de busca
  searchInput.value = initialQuery;

  // Renderizar pills de filtro
  function renderFilterPills() {
    const allCategories = ['all', ...new Set(products.map(p => p.category))];
    filterPills.innerHTML = allCategories.map(cat => `
      <button class="filter-pill ${cat === currentCategory ? 'active' : ''}" data-category="${cat}">
        ${cat === 'all' ? 'Todos' : cat}
      </button>
    `).join('');

    // Event listeners
    filterPills.querySelectorAll('.filter-pill').forEach(pill => {
      pill.addEventListener('click', () => {
        currentCategory = pill.dataset.category;
        updateURL();
        renderFilterPills();
        renderProducts();
      });
    });
  }

  // Filtrar e ordenar produtos
  function getFilteredProducts() {
    let filtered = [...products];

    // Filtrar por busca
    if (currentQuery) {
      const query = currentQuery.toLowerCase();
      filtered = filtered.filter(p =>
        p.name.toLowerCase().includes(query) ||
        p.description.toLowerCase().includes(query) ||
        p.category.toLowerCase().includes(query)
      );
    }

    // Filtrar por categoria
    if (currentCategory !== 'all') {
      filtered = filtered.filter(p => p.category === currentCategory);
    }

    // Ordenar
    switch (currentSort) {
      case 'discount':
        filtered.sort((a, b) => b.discount - a.discount);
        break;
      case 'price-asc':
        filtered.sort((a, b) => a.salePrice - b.salePrice);
        break;
      case 'price-desc':
        filtered.sort((a, b) => b.salePrice - a.salePrice);
        break;
      case 'recent':
        filtered.sort((a, b) => b.id - a.id);
        break;
    }

    return filtered;
  }

  // Renderizar produtos
  function renderProducts() {
    const filtered = getFilteredProducts();

    // Info dos resultados
    if (currentQuery) {
      resultsInfo.innerHTML = `Encontrados <strong>${filtered.length}</strong> resultados para "<strong>${currentQuery}</strong>"`;
    } else if (currentCategory !== 'all') {
      resultsInfo.innerHTML = `Mostrando <strong>${filtered.length}</strong> produtos em <strong>${currentCategory}</strong>`;
    } else {
      resultsInfo.innerHTML = `Mostrando todos os <strong>${filtered.length}</strong> produtos`;
    }

    // Grid vazio ou com produtos
    if (filtered.length === 0) {
      productsGrid.innerHTML = `
        <div class="empty-state">
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="11" cy="11" r="8"/>
            <path d="m21 21-4.3-4.3"/>
          </svg>
          <h3>Nenhum produto encontrado</h3>
          <p>Tente buscar por outros termos ou alterar os filtros.</p>
        </div>
      `;
    } else {
      productsGrid.innerHTML = filtered.map(product => createProductCard(product)).join('');
    }
  }

  // Criar card do produto
  function createProductCard(product) {
    return `
      <div class="product-card">
        <div class="product-image">
          <img src="https://picsum.photos/seed/${product.imageId}/400/300" alt="${product.name}">
          <span class="discount-badge">-${product.discount}%</span>
        </div>
        <div class="product-info">
          <span class="category-tag">${product.category}</span>
          <h3 class="product-name">${product.name}</h3>
          <p class="product-description">${product.description}</p>
          <div class="price-container">
            <p class="original-price">R$ ${product.originalPrice.toFixed(2).replace('.', ',')}</p>
            <p class="sale-price">R$ ${product.salePrice.toFixed(2).replace('.', ',')}</p>
          </div>
          <button class="product-btn">Ver oferta →</button>
        </div>
      </div>
    `;
  }

  // Atualizar URL
  function updateURL() {
    const params = new URLSearchParams();
    if (currentQuery) params.set('q', currentQuery);
    if (currentCategory !== 'all') params.set('category', currentCategory);
    const newURL = params.toString() ? `?${params.toString()}` : window.location.pathname;
    history.replaceState({}, '', newURL);
  }

  // Busca
  function handleSearch() {
    currentQuery = searchInput.value.trim();
    updateURL();
    renderProducts();
  }

  searchInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') handleSearch();
  });

  searchBtn.addEventListener('click', handleSearch);

  // Ordenação
  sortSelect.addEventListener('change', () => {
    currentSort = sortSelect.value;
    renderProducts();
  });

  // Menu mobile
  menuToggle.addEventListener('click', () => {
    navLinks.classList.toggle('active');
  });

  // Inicializar
  renderFilterPills();
  renderProducts();
});
