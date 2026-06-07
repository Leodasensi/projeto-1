import sqlite3
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(__file__))
from supabase_db import inserir_promocoes, buscar_promocoes


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
    from supabase_db import client

    try:
        result = (
            client.table("promocoes")
            .select("id")
            .eq("titulo", titulo)
            .eq("url_original", url_original)
            .limit(1)
            .execute()
        )
        return len(result.data) > 0
    except Exception:
        return False


def sincronizar(db_path, loja="mercadolivre"):
    print(f"=== Sincronizando SQLite -> Supabase ===")
    print(f"Banco local: {db_path}")

    promocoes = buscar_no_sqlite(db_path)
    print(f"Encontradas {len(promocoes)} promocoes no SQLite")

    if not promocoes:
        print("Nenhuma promocao para sincronizar")
        return

    novas = []
    duplicadas = 0

    for p in promocoes:
        p["loja"] = loja

        if not ja_existe_no_supabase(p.get("titulo", ""), p.get("url_original", "")):
            novas.append(p)
        else:
            duplicadas += 1

    print(f"Novas: {len(novas)} | Duplicadas: {duplicadas}")

    if novas:
        inseridos = inserir_promocoes(novas)
        print(f"Sincronizados {inseridos} registros")
    else:
        print("Nada para sincronizar")


def sincronizar_ml():
    paths = [
        os.path.join(os.path.dirname(__file__), "mercado-livre-bot", "promocoes.db"),
        os.path.join(os.path.dirname(__file__), "..", "..", "..", "promocoes.db"),
    ]

    for path in paths:
        if os.path.exists(path):
            sincronizar(path, loja="mercadolivre")
            return

    print("Banco do Mercado Livre nao encontrado")


def sincronizar_shopee():
    paths = [
        os.path.join(os.path.dirname(__file__), "shopee-bot", "promocoes_shopee.db"),
        os.path.join(os.path.dirname(__file__), "shopee-bot", "promocoes.db"),
    ]

    for path in paths:
        if os.path.exists(path):
            sincronizar(path, loja="shopee")
            return

    print("Banco da Shopee nao encontrado")


if __name__ == "__main__":
    print("1. Sincronizar Mercado Livre")
    print("2. Sincronizar Shopee")
    print("3. Sincronizar ambos")

    opcao = input("\nEscolha: ").strip()

    if opcao == "1":
        sincronizar_ml()
    elif opcao == "2":
        sincronizar_shopee()
    elif opcao == "3":
        sincronizar_ml()
        sincronizar_shopee()
    else:
        print("Opcao invalida")
