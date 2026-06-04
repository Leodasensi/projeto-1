document.addEventListener('DOMContentLoaded', () => {
  const urlParams = new URLSearchParams(window.location.search);
  const slug = urlParams.get('slug');
  const product = slug ? findProductBySlug(slug) : null;

  const menuToggle = document.querySelector('.menu-toggle');
  const navLinks = document.querySelector('.nav-links');
  if (menuToggle) {
    menuToggle.addEventListener('click', () => {
      navLinks.classList.toggle('active');
    });
  }

  if (!product) {
    document.getElementById('productNotFound').style.display = 'block';
    document.getElementById('productMain').style.display = 'none';
    document.querySelector('.product-specs-section').style.display = 'none';
    document.querySelector('.related-section').style.display = 'none';
    document.getElementById('mobileCtaBar').style.display = 'none';
    document.getElementById('breadcrumb').style.display = 'none';
    document.title = 'Produto não encontrado — Infinity Promo';
    return;
  }

  updateSEO(product);
  renderBreadcrumb(product);
  renderGallery(product);
  renderDetails(product);
  initCountdownTimer(document.getElementById('countdownContainer'), product.slug);
  initSaveButton(product);
  renderSpecs(product);
  renderRelated(product);
  initMobileCta(product);
});

function updateSEO(product) {
  document.title = `${product.name} — Infinity Promo`;
  const desc = `De R$ ${product.originalPrice.toFixed(2).replace('.', ',')} por R$ ${product.salePrice.toFixed(2).replace('.', ',')}. ${product.description}`;
  setMeta('description', desc);
  setMeta('og:title', `${product.name} — Infinity Promo`, 'property');
  setMeta('og:description', desc, 'property');
  setMeta('og:image', `https://picsum.photos/seed/${product.imageId}/800/600`, 'property');
  setMeta('og:type', 'product', 'property');
}

function setMeta(name, content, attr = 'name') {
  let el = document.querySelector(`meta[${attr}="${name}"]`);
  if (!el) {
    el = document.createElement('meta');
    el.setAttribute(attr, name);
    document.head.appendChild(el);
  }
  el.setAttribute('content', content);
}

function renderBreadcrumb(product) {
  document.getElementById('breadcrumbCategory').textContent = product.category;
  document.getElementById('breadcrumbCategory').href = `busca.html?category=${encodeURIComponent(product.category)}`;
  document.getElementById('breadcrumbCurrent').textContent = product.name;
}

function renderGallery(product) {
  const mainImage = document.getElementById('mainImage');
  const skeleton = document.getElementById('gallerySkeleton');
  const badge = document.getElementById('galleryBadge');
  const thumbs = document.querySelectorAll('.product-thumbs .thumb');

  const gallerySeeds = [product.imageId, `${product.imageId}-2`, `${product.imageId}-3`];
  const imageUrls = gallerySeeds.map(s => `https://picsum.photos/seed/${s}/800/600`);

  mainImage.src = imageUrls[0];
  mainImage.alt = product.name;
  mainImage.addEventListener('load', () => {
    skeleton.style.display = 'none';
    mainImage.style.display = 'block';
  }, { once: true });

  mainImage.addEventListener('error', () => {
    skeleton.style.display = 'none';
    mainImage.style.display = 'block';
  }, { once: true });

  badge.textContent = `-${product.discount}%`;
  badge.style.display = 'block';

  thumbs.forEach((thumb, i) => {
    const img = thumb.querySelector('img');
    img.src = imageUrls[i];
    img.alt = `${product.name} - vista ${i + 1}`;
    thumb.addEventListener('click', () => {
      thumbs.forEach(t => t.classList.remove('active'));
      thumb.classList.add('active');
      mainImage.style.opacity = '0';
      setTimeout(() => {
        mainImage.src = imageUrls[i];
        mainImage.onload = () => { mainImage.style.opacity = '1'; };
      }, 150);
    });
  });
}

function renderDetails(product) {
  document.getElementById('productCategory').textContent = product.category;
  document.getElementById('productTitle').textContent = product.name;
  document.getElementById('originalPrice').textContent = `R$ ${product.originalPrice.toFixed(2).replace('.', ',')}`;
  document.getElementById('salePrice').textContent = `R$ ${product.salePrice.toFixed(2).replace('.', ',')}`;
  const savings = product.originalPrice - product.salePrice;
  document.getElementById('savingsLine').innerHTML = `Você economiza <strong>R$ ${savings.toFixed(2).replace('.', ',')}</strong>`;
  document.getElementById('storeLink').href = product.link;
  document.getElementById('storeName').textContent = product.store.name;
  if (product.store.freeShipping) {
    document.getElementById('freeShipping').style.display = 'inline-flex';
  }
}

function initSaveButton(product) {
  const btn = document.getElementById('saveBtn');
  const text = document.getElementById('saveBtnText');
  const key = `saved-${product.slug}`;

  function update(saved) {
    if (saved) {
      btn.classList.add('saved');
      text.textContent = '✓ Salvo!';
    } else {
      btn.classList.remove('saved');
      text.textContent = 'Salvar promoção';
    }
  }

  update(localStorage.getItem(key) === 'true');

  btn.addEventListener('click', () => {
    const isSaved = localStorage.getItem(key) === 'true';
    const newState = !isSaved;
    localStorage.setItem(key, newState.toString());
    update(newState);
  });
}

function renderSpecs(product) {
  const table = document.getElementById('specsTable');
  const rows = Object.entries(product.specs)
    .map(([key, value]) => `
      <div class="specs-row">
        <span class="specs-label">${key}</span>
        <span class="specs-value">${value}</span>
      </div>
    `).join('');
  table.innerHTML = rows;
  document.getElementById('productLongDescription').textContent = product.longDescription;
}

function renderRelated(product) {
  const related = getRelatedProducts(product.id, product.category, 3);
  const grid = document.getElementById('relatedGrid');
  if (related.length === 0) {
    document.querySelector('.related-section').style.display = 'none';
    return;
  }
  grid.innerHTML = related.map(p => createProductCard(p)).join('');
}

function initMobileCta(product) {
  document.getElementById('mobileCtaPrice').textContent = `R$ ${product.salePrice.toFixed(2).replace('.', ',')}`;
  document.getElementById('mobileCtaDiscount').textContent = `-${product.discount}% OFF`;
  document.getElementById('mobileCtaBtn').href = product.link;
}
