from dotenv import load_dotenv
import os
from supabase import create_client

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

url = os.getenv("SUPABASE_URL", "")
key = os.getenv("SUPABASE_KEY", "")
assert url and key, "SUPABASE_URL e SUPABASE_KEY devem estar configurados no .env"
client = create_client(url, key)


def criar_tabela_promocoes():
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

    CREATE INDEX IF NOT EXISTS idx_promocoes_categoria ON promocoes(categoria);
    CREATE INDEX IF NOT EXISTS idx_promocoes_loja ON promocoes(loja);
    CREATE INDEX IF NOT EXISTS idx_promocoes_criado ON promocoes(criado_em);
    """

    try:
        result = client.rpc("exec_sql", {"query": sql}).execute()
        print("Tabela criada com sucesso!")
        return True
    except Exception as e:
        print(f"Erro ao criar tabela via RPC: {e}")
        print("Tentando inserir dados diretamente...")
        return False


def inserir_promocoes(promocoes):
    if not promocoes:
        print("Nenhuma promocao para inserir")
        return 0

    dados = []
    for p in promocoes:
        dado = {
            "produto_id": str(p.get("produto_id", "")),
            "titulo": p.get("titulo", ""),
            "url_original": p.get("url_original", ""),
            "url_afiliado": p.get("url_afiliado", ""),
            "preco_original": p.get("preco_original"),
            "preco_desconto": p.get("preco_desconto"),
            "porcentagem_desconto": p.get("porcentagem_desconto"),
            "imagem_url": p.get("imagem_url", ""),
            "especificacoes": p.get("especificacoes", ""),
            "categoria": p.get("categoria", "geral"),
            "loja": p.get("loja", "mercadolivre"),
            "vendidos": p.get("vendidos"),
            "avaliacoes": p.get("avaliacoes"),
        }
        dados.append(dado)

    try:
        result = client.table("promocoes").insert(dados).execute()
        print(f"Inseridos {len(result.data)} registros no Supabase")
        return len(result.data)
    except Exception as e:
        print(f"Erro ao inserir: {e}")
        return 0


def buscar_promocoes(limite=50):
    try:
        result = (
            client.table("promocoes")
            .select("*")
            .order("criado_em", desc=True)
            .limit(limite)
            .execute()
        )
        return result.data
    except Exception as e:
        print(f"Erro ao buscar: {e}")
        return []


def limpar_promocoes_antigas(dias=7):
    try:
        result = (
            client.table("promocoes")
            .delete()
            .lt("criado_em", f"now()-interval'{dias} days'")
            .execute()
        )
        print(f"Registros antigos removidos")
    except Exception as e:
        print(f"Erro ao limpar: {e}")


if __name__ == "__main__":
    print("=== Teste Supabase ===")
    print(f"URL: {url}")
    print(f"Conexao: OK")

    promocoes = buscar_promocoes(5)
    print(f"Promocoes no banco: {len(promocoes)}")
