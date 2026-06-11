from dotenv import load_dotenv
import os
from supabase import create_client

load_dotenv(os.path.join(os.path.dirname(__file__), "shopee-bot", ".env"))

url = os.getenv("SUPABASE_URL", "")
key = os.getenv("SUPABASE_KEY", "")
assert url and key, "SUPABASE_URL e SUPABASE_KEY devem estar configurados no .env"
client = create_client(url, key)


def criar_tabela():
    sql = """
    CREATE TABLE IF NOT EXISTS promocoes (
        id BIGSERIAL PRIMARY KEY,
        produto_id TEXT,
        titulo TEXT NOT NULL,
        url_original TEXT,
        url_afiliado TEXT,
        preco_original NUMERIC,
        preco_desconto NUMERIC,
        porcentagem_desconto NUMERIC,
        imagem_url TEXT,
        especificacoes TEXT,
        categoria TEXT,
        loja TEXT DEFAULT 'mercadolivre',
        vendidos INTEGER,
        avaliacoes NUMERIC,
        criado_em TIMESTAMP DEFAULT NOW()
    );
    """

    try:
        result = client.rpc("exec_sql", {"query": sql}).execute()
        print("Tabela criada via RPC!")
        return True
    except Exception as e:
        print(f"RPC falhou: {e}")
        return False


def inserir_dados_teste():
    dados_teste = [
        {
            "titulo": "iPhone 14 Pro Max 256GB",
            "url_original": "https://www.mercadolivre.com.br/iphone-14-pro-max",
            "url_afiliado": "https://www.mercadolivre.com.br/iphone-14-pro-max?matt_tool=123",
            "preco_original": 9499.00,
            "preco_desconto": 7999.00,
            "porcentagem_desconto": 15.8,
            "imagem_url": "https://http2.mlstatic.com/D_NQ_NP_123.jpg",
            "categoria": "celular",
            "loja": "mercadolivre",
        },
        {
            "titulo": "Notebook Dell Inspiron 15",
            "url_original": "https://www.mercadolivre.com.br/notebook-dell",
            "url_afiliado": "https://www.mercadolivre.com.br/notebook-dell?matt_tool=123",
            "preco_original": 4599.00,
            "preco_desconto": 3299.00,
            "porcentagem_desconto": 28.3,
            "imagem_url": "https://http2.mlstatic.com/D_NQ_NP_456.jpg",
            "categoria": "computador",
            "loja": "mercadolivre",
        },
        {
            "titulo": "Fone Bluetooth JBL Tune 510",
            "url_original": "https://www.shopee.com.br/fone-jbl",
            "url_afiliado": "https://www.shopee.com.br/fone-jbl?af_id=456",
            "preco_original": 299.00,
            "preco_desconto": 179.00,
            "porcentagem_desconto": 40.1,
            "imagem_url": "https://cf.shopee.com.br/fone-jbl.jpg",
            "categoria": "audio",
            "loja": "shopee",
        },
    ]

    try:
        result = client.table("promocoes").insert(dados_teste).execute()
        print(f"Inseridos {len(result.data)} dados de teste!")
        return True
    except Exception as e:
        print(f"Erro ao inserir: {e}")
        return False


def verificar_tabela():
    try:
        result = client.table("promocoes").select("*").limit(1).execute()
        print(f"Tabela existe! {len(result.data)} registros")
        return True
    except Exception as e:
        print(f"Tabela nao existe: {e}")
        return False


if __name__ == "__main__":
    print("=== Setup Supabase ===")

    if not verificar_tabela():
        print("\nTentando criar tabela...")
        if criar_tabela():
            print("Tabela criada! Inserindo dados de teste...")
            inserir_dados_teste()
        else:
            print("\nNao foi possivel criar tabela via API.")
            print("Crie manualmente no Supabase Dashboard > SQL Editor:")
            print("""
CREATE TABLE promocoes (
    id BIGSERIAL PRIMARY KEY,
    produto_id TEXT,
    titulo TEXT NOT NULL,
    url_original TEXT,
    url_afiliado TEXT,
    preco_original NUMERIC,
    preco_desconto NUMERIC,
    porcentagem_desconto NUMERIC,
    imagem_url TEXT,
    especificacoes TEXT,
    categoria TEXT,
    loja TEXT DEFAULT 'mercadolivre',
    vendidos INTEGER,
    avaliacoes NUMERIC,
    criado_em TIMESTAMP DEFAULT NOW()
);
            """)
    else:
        print("Tabela ja existe!")
        result = client.table("promocoes").select("*").limit(5).execute()
        for p in result.data:
            print(f"  - {p.get('titulo', 'N/A')[:40]} | {p.get('loja', 'N/A')}")
