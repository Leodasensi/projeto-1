(function () {
  const cfg = window.SUPABASE_CONFIG || {};
  const PLACEHOLDER_URL = 'https://kywgmckuoueojcsomaxu.supabase.co';
  const PLACEHOLDER_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imt5d2dtY2t1b3Vlb2pjc29tYXh1Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODA2MTUwODQsImV4cCI6MjA5NjE5MTA4NH0.bMcDF9xWXrkZa32NXdzVWnOJzXRDU3EuBppN1j-yeUE';

  const isConfigured = !!(
    cfg.url &&
    cfg.anonKey &&
    cfg.url !== PLACEHOLDER_URL &&
    cfg.anonKey !== PLACEHOLDER_KEY &&
    !cfg.url.includes('kywgmckuoueojcsomaxu') &&
    !cfg.anonKey.includes('eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imt5d2dtY2t1b3Vlb2pjc29tYXh1Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODA2MTUwODQsImV4cCI6MjA5NjE5MTA4NH0.bMcDF9xWXrkZa32NXdzVWnOJzXRDU3EuBppN1j-yeUE')
  );

  const supabase = isConfigured && window.supabase ? window.supabase.createClient(cfg.url, cfg.anonKey) : null;
  const usingSupabase = !!supabase;

  function transformRow(p) {
    if (!p) return p;
    return {
      id: p.id,
      slug: p.slug,
      name: p.name,
      description: p.description,
      longDescription: p.description,
      category: p.category,
      originalPrice: Number(p.original_price),
      salePrice: Number(p.sale_price),
      discount: p.discount,
      imageId: p.slug,
      imageUrl: p.image_url,
      store: {
        name: p.store_name,
        freeShipping: !!p.free_shipping
      },
      coupon: p.coupon || null,
      link: p.link,
      specs: p.specs || {},
      createdAt: p.created_at
    };
  }

  function cloneMock() {
    return (window.mockProducts || []).map(p => Object.assign({}, p, {
      store: Object.assign({}, p.store),
      specs: Object.assign({}, p.specs)
    }));
  }

  async function fetchFromSupabase(queryBuilder) {
    const { data, error } = await queryBuilder;
    if (error) throw error;
    return (data || []).map(transformRow);
  }

  function fallback(supabaseCall) {
    return async function () {
      if (usingSupabase) {
        try {
          const result = await supabaseCall();
          if (Array.isArray(result)) {
            if (result.length === 0) return cloneMock();
            return result;
          }
          return result || cloneMock();
        } catch (err) {
          console.warn('[products] Supabase falhou, usando mock:', err && err.message ? err.message : err);
          return cloneMock();
        }
      }
      return cloneMock();
    };
  }

  const API = {
    usingSupabase: usingSupabase,

    getAllProducts: fallback(async function (limit) {
      let q = supabase
        .from('products')
        .select('*')
        .eq('active', true)
        .order('created_at', { ascending: false });
      if (limit) q = q.limit(limit);
      return fetchFromSupabase(q);
    }),

    getProductBySlug: fallback(async function (slug) {
      const { data, error } = await supabase
        .from('products')
        .select('*')
        .eq('slug', slug)
        .eq('active', true)
        .maybeSingle();
      if (error) throw error;
      if (!data) {
        const mock = (window.mockProducts || []).find(p => p.slug === slug);
        return mock ? Object.assign({}, mock, { store: Object.assign({}, mock.store), specs: Object.assign({}, mock.specs) }) : null;
      }
      return transformRow(data);
    }),

    getProductsByCategory: fallback(async function (category) {
      const q = supabase
        .from('products')
        .select('*')
        .eq('category', category)
        .eq('active', true)
        .order('created_at', { ascending: false });
      return fetchFromSupabase(q);
    }),

    searchProducts: fallback(async function (query) {
      const q = supabase
        .from('products')
        .select('*')
        .eq('active', true)
        .ilike('name', '%' + query + '%')
        .order('created_at', { ascending: false });
      return fetchFromSupabase(q);
    }),

    getRelatedProducts: fallback(async function (category, excludeSlug, limit) {
      const lim = limit || 3;
      const q = supabase
        .from('products')
        .select('*')
        .eq('category', category)
        .eq('active', true)
        .neq('slug', excludeSlug)
        .limit(lim);
      return fetchFromSupabase(q);
    })
  };

  window.ProductsAPI = API;
})();
