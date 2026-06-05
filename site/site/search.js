document.addEventListener('DOMContentLoaded', () => {
  const searchInput = document.getElementById('searchInput');
  const searchBtn = document.getElementById('searchBtn');
  const resultsInfo = document.getElementById('resultsInfo');
  const filterPills = document.getElementById('filterPills');
  const sortSelect = document.getElementById('sortSelect');
  const productsGrid = document.getElementById('productsGrid');
  const menuToggle = document.querySelector('.menu-toggle');
  const navLinks = document.querySelector('.nav-links');

  const urlParams = new URLSearchParams(window.location.search);
  const initialQuery = urlParams.get('q') || '';
  const initialCategory = urlParams.get('category') || 'all';

  let products = window.mockProducts ? window.mockProducts.slice() : [];
  let currentQuery = initialQuery;
  let currentCategory = initialCategory;
  let currentSort = 'discount';

  searchInput.value = initialQuery;

  function renderFilterPills() {
    const allCategories = ['all', ...new Set(products.map(p => p.category))];
    filterPills.innerHTML = allCategories.map(cat => `
      <button class="filter-pill ${cat === currentCategory ? 'active' : ''}" data-category="${cat}">
        ${cat === 'all' ? 'Todos' : cat}
      </button>
    `).join('');

    filterPills.querySelectorAll('.filter-pill').forEach(pill => {
      pill.addEventListener('click', () => {
        currentCategory = pill.dataset.category;
        updateURL();
        renderFilterPills();
        renderProducts();
      });
    });
  }

  function getFilteredProducts() {
    let filtered = [...products];

    if (currentQuery) {
      const query = currentQuery.toLowerCase();
      filtered = filtered.filter(p =>
        p.name.toLowerCase().includes(query) ||
        p.description.toLowerCase().includes(query) ||
        p.category.toLowerCase().includes(query)
      );
    }

    if (currentCategory !== 'all') {
      filtered = filtered.filter(p => p.category === currentCategory);
    }

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

  function renderProducts() {
    const filtered = getFilteredProducts();

    if (currentQuery) {
      resultsInfo.innerHTML = `Encontrados <strong>${filtered.length}</strong> resultados para "<strong>${currentQuery}</strong>"`;
    } else if (currentCategory !== 'all') {
      resultsInfo.innerHTML = `Mostrando <strong>${filtered.length}</strong> produtos em <strong>${currentCategory}</strong>`;
    } else {
      resultsInfo.innerHTML = `Mostrando todos os <strong>${filtered.length}</strong> produtos`;
    }

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

  function updateURL() {
    const params = new URLSearchParams();
    if (currentQuery) params.set('q', currentQuery);
    if (currentCategory !== 'all') params.set('category', currentCategory);
    const newURL = params.toString() ? `?${params.toString()}` : window.location.pathname;
    history.replaceState({}, '', newURL);
  }

  function handleSearch() {
    currentQuery = searchInput.value.trim();
    updateURL();
    renderProducts();
  }

  searchInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') handleSearch();
  });

  searchBtn.addEventListener('click', handleSearch);

  sortSelect.addEventListener('change', () => {
    currentSort = sortSelect.value;
    renderProducts();
  });

  menuToggle.addEventListener('click', () => {
    navLinks.classList.toggle('active');
  });

  renderFilterPills();
  renderProducts();

  if (window.ProductsAPI) {
    let promise;
    if (initialQuery && typeof window.ProductsAPI.searchProducts === 'function') {
      promise = window.ProductsAPI.searchProducts(initialQuery);
    } else if (initialCategory !== 'all' && typeof window.ProductsAPI.getProductsByCategory === 'function') {
      promise = window.ProductsAPI.getProductsByCategory(initialCategory);
    } else if (typeof window.ProductsAPI.getAllProducts === 'function') {
      promise = window.ProductsAPI.getAllProducts();
    }

    if (promise) {
      promise.then(data => {
        if (Array.isArray(data) && data.length > 0) {
          products = data;
          renderFilterPills();
          renderProducts();
        }
      }).catch(err => {
        console.warn('Falha ao atualizar do Supabase, mantendo mock:', err);
      });
    }
  }
});
