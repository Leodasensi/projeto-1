from dotenv import load_dotenv
import os
import sys
import requests
import time

sys.path.insert(0, os.path.dirname(__file__))
from supabase_db import buscar_promocoes

load_dotenv()
WEBHOOK = os.getenv("WEBHOOK")

CARGOpromoShopee = "1511789248771129514"
CARGOpromoMercadoLivre = "1511789008231993344"


def formatar_produto(produto):
    titulo = produto.get("titulo", "Sem titulo")
    preco_original = produto.get("preco_original")
    preco_desconto = produto.get("preco_desconto")
    desconto = produto.get("porcentagem_desconto")
    url = produto.get("url_afiliado") or produto.get("url_original", "")
    imagem = produto.get("imagem_url", "")

    if preco_original:
        preco_original = f"R$ {preco_original:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    else:
        preco_original = "N/A"

    if preco_desconto:
        preco_desconto = f"R$ {preco_desconto:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    else:
        preco_desconto = "N/A"

    embed = {
        "title": titulo[:256],
        "url": url,
        "color": 0x00FF00,
        "fields": [
            {"name": "De:", "value": preco_original, "inline": True},
            {"name": "Por:", "value": preco_desconto, "inline": True},
        ],
    }

    if desconto:
        embed["fields"].append({"name": "Desconto:", "value": f"{desconto}%", "inline": True})

    if imagem:
        embed["thumbnail"] = {"url": imagem}

    return embed


def enviar_discord(webhook_url, embeds, cargo_id, username, content_msg):
    if not embeds:
        return

    payload = {
        "content": content_msg,
        "username": username,
        "avatar_url": "https://i.postimg.cc/gk159hF3/Infinity.png",
        "allowed_mentions": {"roles": [int(cargo_id)]},
        "embeds": embeds[:10],
    }

    response = requests.post(webhook_url, json=payload)
    print(f"{username}: {response.status_code}")
    return response


def main():
    load_dotenv()
    webhook = os.getenv("WEBHOOK")

    if not webhook:
        print("WEBHOOK nao configurado no .env")
        return

    print("Buscando promocoes no Supabase...")
    promocoes = buscar_promocoes(10)

    if not promocoes:
        print("Nenhuma promocao encontrada")
        return

    print(f"Encontradas {len(promocoes)} promocoes")

    embeds_ml = [formatar_produto(p) for p in promocoes if p.get("loja") == "mercadolivre"]
    embeds_shopee = [formatar_produto(p) for p in promocoes if p.get("loja") == "shopee"]

    if embeds_ml:
        enviar_discord(
            webhook,
            embeds_ml,
            CARGOpromoMercadoLivre,
            "Bot da Infinity - MERCADO LIVRE",
            f"Promocoes do Mercado Livre! <@&{CARGOpromoMercadoLivre}>",
        )

    if embeds_shopee:
        time.sleep(1)
        enviar_discord(
            webhook,
            embeds_shopee,
            CARGOpromoShopee,
            "Bot da Infinity - SHOPEE",
            f"Promocoes da Shopee! <@&{CARGOpromoShopee}>",
        )

    print("Concluido!")


if __name__ == "__main__":
    main()
