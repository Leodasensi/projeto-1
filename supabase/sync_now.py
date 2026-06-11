import sqlite3
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from supabase_db import inserir_promocoes, client

DB_PATH = r"C:\Users\glaon\OneDrive\Documents\VS code\programação\VS code\projetos incompletos\promocoes_shopee.db"

def buscar_no_sqlite(db_path, limite=500):
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

print(f"Banco: {DB_PATH}")
print(f"Existe: {os.path.exists(DB_PATH)}")

promocoes = buscar_no_sqlite(DB_PATH)
print(f"Produtos no SQLite: {len(promocoes)}")

if promocoes:
    for p in promocoes:
        p["loja"] = "shopee"
    
    inseridos = inserir_promocoes(promocoes)
    print(f"Sincronizados: {inseridos}")
else:
    print("Nenhum produto para sincronizar")
