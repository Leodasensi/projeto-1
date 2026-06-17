export function transformProduct(p) {
  if (!p) return p;
  return {
    id: p.id,
    slug: p.slug || p.produto_id,
    name: p.name || p.titulo,
    description: p.description || p.especificacoes || "",
    longDescription: p.description || p.especificacoes || "",
    category: p.category || p.categoria || "geral",
    originalPrice: Number(p.original_price || p.preco_original || 0),
    salePrice: Number(p.sale_price || p.preco_desconto || 0),
    discount: p.discount || p.porcentagem_desconto || 0,
    imageId: p.image_id || p.produto_id || p.imagem_url,
    store: {
      name: p.store_name || p.loja || "Mercado Livre",
      freeShipping: !!p.free_shipping
    },
    coupon: p.coupon || null,
    link: p.link || p.url_afiliado || p.url_original,
    specs: p.specs || {}
  }
}
