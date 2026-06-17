import sqlite3
import os
import sys
import re
from datetime import datetime

sys.path.insert(0, os.path.dirname(__file__))
from supabase_db import inserir_produtos, buscar_produtos, client


def slugify(text):
    text = text.lower()
    text = re.sub(r'[\s\-]+', '-', text)
    text = re.sub(r'[^a-z0-9\-]', '', text)
    return text[:50]


def buscar_no_sqlite(db_path, limite=100):
    if not os.path.exists(db_path):
        print(f"Banco nao encontrado: {db_path}")
        return []

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT produto_id, titulo, url_original, url_afiliado,
               preco_original, preco_desconto, porcentagem_desconto,
               imagem_url, especificacoes, categoria,
               vendidos, avaliacoes
        FROM produtos
        ORDER BY data_coleta DESC
        LIMIT ?
    """, (limite,))

    resultados = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return resultados


def ja_existe_no_supabase(titulo, url_original):
    try:
        result = (
            client.table("products")
            .select("id")
            .eq("name", titulo)
            .eq("link", url_original)
            .limit(1)
            .execute()
        )
        return len(result.data) > 0
    except Exception:
        return False


def mapear_produto(p, loja="mercadolivre"):
    return {
        "slug": f"{loja}-{slugify(p.get('titulo', ''))}-{p.get('produto_id', '')[:8]}",
        "name": p.get("titulo", ""),
        "description": p.get("especificacoes", "") or "",
        "category": p.get("categoria", "geral"),
        "original_price": p.get("preco_original"),
        "sale_price": p.get("preco_desconto"),
        "discount": p.get("porcentagem_desconto"),
        "image_id": p.get("produto_id", "")[:20] or p.get("imagem_url", ""),
        "store_name": loja.title() if loja == "mercadolivre" else "Shopee",
        "free_shipping": True,
        "link": p.get("url_afiliado", "") or p.get("url_original", ""),
        "active": True
    }


def sincronizar_mercadolivre():
    db_paths = [
        os.path.join(os.path.dirname(__file__), "..", "finanças", "aplicativo", "main", "mercado-livre-bot", "promocoes.db"),
        "promocoes.db"
    ]

    for db_path in db_paths:
        if os.path.exists(db_path):
            print(f"Sincronizando Mercado Livre: {db_path}")
            produtos = buscar_no_sqlite(db_path, limite=50)

            novos = []
            duplicados = 0

            for p in produtos:
                if not ja_existe_no_supabase(p.get("titulo", ""), p.get("url_original", "")):
                    novos.append(mapear_produto(p, "mercadolivre"))
                else:
                    duplicados += 1

            if novos:
                inserir_produtos(novos)
            print(f"Novos: {len(novos)} | Duplicados: {duplicados}")
            return

    print("Banco do Mercado Livre nao encontrado")


def sincronizar_shopee():
    db_paths = [
        os.path.join(os.path.dirname(__file__), "..", "finanças", "aplicativo", "main", "shopee-bot", "promocoes_shopee.db"),
        "promocoes_shopee.db"
    ]

    for db_path in db_paths:
        if os.path.exists(db_path):
            print(f"Sincronizando Shopee: {db_path}")
            produtos = buscar_no_sqlite(db_path, limite=50)

            novos = []
            duplicados = 0

            for p in produtos:
                if not ja_existe_no_supabase(p.get("titulo", ""), p.get("url_original", "")):
                    novos.append(mapear_produto(p, "shopee"))
                else:
                    duplicados += 1

            if novos:
                inserir_produtos(novos)
            print(f"Novos: {len(novos)} | Duplicados: {duplicados}")
            return

    print("Banco da Shopee nao encontrado")


if __name__ == "__main__":
    print("1. Sincronizar Mercado Livre")
    print("2. Sincronizar Shopee")
    print("3. Sincronizar ambos")

    opcao = input("\nEscolha: ").strip()

    if opcao == "1":
        sincronizar_mercadolivre()
    elif opcao == "2":
        sincronizar_shopee()
    elif opcao == "3":
        sincronizar_mercadolivre()
        sincronizar_shopee()