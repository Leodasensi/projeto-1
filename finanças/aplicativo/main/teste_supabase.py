from dotenv import load_dotenv
import os
from supabase import create_client

load_dotenv(os.path.join(os.path.dirname(__file__), "shopee-bot", ".env"))

url = os.getenv("SUPABASE_URL", "")
key = os.getenv("SUPABASE_KEY", "")

print(f"URL: {url}")
print(f"KEY: {key[:20]}...")

client = create_client(url, key)
print("Conexao OK!")

tabelas = ["produtos", "promocoes", "products", "promotions", "users", "orders", "promos"]

for tabela in tabelas:
    try:
        result = client.table(tabela).select("*").limit(1).execute()
        print(f'Tabela "{tabela}": {len(result.data)} registros')
        if result.data:
            print(f"  Colunas: {list(result.data[0].keys())}")
    except Exception as e:
        print(f'Tabela "{tabela}": nao existe')
