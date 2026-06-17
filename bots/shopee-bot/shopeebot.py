import schedule
import time
import signal
import sys
import os
import json
import requests
import sqlite3
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "supabase"))
from supabase_db import inserir_promocoes as inserir_supabase #type: ignore

from config import UPDATE_INTERVAL, SHOPEE_AFFILIATE_ID, DB_NAME
from database import init_db, inserir_produtos_em_lote, obter_estatisticas
from scraper import scraping_completo
from display import (
    console, exibir_cabecalho, exibir_estatisticas,
    exibir_lista_produtos, exibir_resumo_atualizacao,
    exibir_erro, exibir_mensagem_agendamento, exibir_titulo_secao
)

WEBHOOK = os.getenv("WEBHOOK")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
CARGO_SHOPEE = "1511789248771129514"

ENVIADOS_FILE = os.path.join(os.path.dirname(__file__), "enviados.json")


def carregar_enviados():
    if os.path.exists(ENVIADOS_FILE):
        with open(ENVIADOS_FILE, "r") as f:
            return json.load(f)
    return []


def salvar_enviados(enviados):
    with open(ENVIADOS_FILE, "w") as f:
        json.dump(enviados[-500:], f)


def filtrar_novos(produtos):
    enviados = carregar_enviados()
    novos = []
    for p in produtos:
        url = p.get("url_original", "")
        if url and url not in enviados:
            novos.append(p)
            enviados.append(url)
    salvar_enviados(enviados)
    return novos


CATEGORIA_EMOJI = {
    "tecnologia": "💻",
    "celular": "📱",
    "celulares": "📱",
    "notebook": "💻",
    "notebooks": "💻",
    "fones": "🎧",
    "smartwatch": "⌚",
    "eletrodomesticos": "🏠",
    "beleza": "💄",
    "games": "🎮",
    "moda": "👕",
    "esportes": "⚽",
    "casa": "🏡",
    "automotivo": "🚗",
    "ferramentas": "🔧",
    "geral": "🏷️",
}


def formatar_produto(produto):
    titulo = produto.get("titulo", "Sem titulo")
    preco_original = produto.get("preco_original")
    preco_desconto = produto.get("preco_desconto")
    desconto = produto.get("porcentagem_desconto")
    url = produto.get("url_afiliado") or produto.get("url_original", "")
    imagem = produto.get("imagem_url", "")
    categoria = produto.get("categoria", "geral")
    vendidos = produto.get("vendidos")

    emoji = CATEGORIA_EMOJI.get(categoria.lower(), "🏷️")

    if preco_desconto:
        preco_fmt = f"R$ {preco_desconto:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    else:
        preco_fmt = "Consultar"

    desc_label = ""
    if desconto and desconto > 0:
        if desconto >= 50:
            desc_label = f"🔥 **{desconto:.0f}% OFF**"
        elif desconto >= 30:
            desc_label = f"⚡ **{desconto:.0f}% OFF**"
        else:
            desc_label = f"💰 **{desconto:.0f}% OFF**"

    embed = {
        "url": url,
        "color": 0xF59E0B if desconto and desconto >= 30 else 0x22C55E,
    }

    if imagem:
        embed["image"] = {"url": imagem}

    embed["author"] = {
        "name": f"{emoji} {categoria.upper()}",
        "icon_url": "https://img.icons8.com/fluency/48/tag.png",
    }

    embed["title"] = titulo[:256]

    preco_linha = f"**{preco_fmt}**"
    if preco_original and preco_original > preco_desconto:
        preco_orig_fmt = f"R$ {preco_original:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        preco_linha = f"~~{preco_orig_fmt}~~ → **{preco_fmt}**"

    embed["description"] = preco_linha

    fields = []
    if desc_label:
        fields.append({"name": "Desconto", "value": desc_label, "inline": True})

    if vendidos:
        if vendidos >= 1000:
            vendidos_str = f"{vendidos/1000:.1f}k+"
        else:
            vendidos_str = str(vendidos)
        fields.append({"name": "Vendidos", "value": f"📦 {vendidos_str}", "inline": True})

    if fields:
        embed["fields"] = fields

    embed["footer"] = {
        "text": f"{'🔥 OFERTA QUENTE 🔥' if desconto and desconto >= 40 else '✨ Promoção Disponível ✨'}",
        "icon_url": "https://img.icons8.com/fluency/48/fire-element.png",
    }

    embed = {k: v for k, v in embed.items() if v is not None and v != []}

    return embed


def enviar_discord(embeds):
    if not WEBHOOK:
        return
    if not embeds:
        return

    for i in range(0, len(embeds), 10):
        batch = embeds[i:i+10]
        total = len(embeds)
        enviados = i + len(batch)

        payload = {
            "content": f"NOVAS PROMOÇÕES DE HOJE!\n**{enviados}/{total} Promoções da Shopee!** \n<@&{CARGO_SHOPEE}>",
            "username": "Infinity Promo",
            "avatar_url": "https://i.postimg.cc/gk159hF3/Infinity.png",
            "allowed_mentions": {"roles": [int(CARGO_SHOPEE)]},
            "embeds": batch,
        }

        try:
            response = requests.post(WEBHOOK, json=payload, timeout=10)
            if response.status_code == 204:
                console.print(f"[green]✓[/] Discord: {len(batch)} produtos enviados")
            elif response.status_code == 429:
                retry = response.json().get("retry_after", 5)
                console.print(f"[yellow]Rate limit, aguardando {retry}s...[/]")
                time.sleep(retry)
                continue
            else:
                console.print(f"[yellow]⚠[/] Discord: {response.status_code}")
            time.sleep(3)
        except Exception as e:
            console.print(f"[red]Erro Discord: {e}[/]")


def enviar_telegram(produtos):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        return
    if not produtos:
        return

    api_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"

    header = f"🔥 *Promoções da Shopee!*\n📦 {len(produtos)} ofertas encontradas\n"
    header += "━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    send_message(api_url, TELEGRAM_CHAT_ID, header)

    for i, p in enumerate(produtos[:20]):
        titulo = p.get("titulo", "Sem título")[:80]
        preco_original = p.get("preco_original")
        preco_desconto = p.get("preco_desconto")
        desconto = p.get("porcentagem_desconto")
        url = p.get("url_afiliado") or p.get("url_original", "")
        categoria = p.get("categoria", "geral")
        imagem = p.get("imagem_url", "")

        emoji = CATEGORIA_EMOJI.get(categoria.lower(), "🏷️")

        msg = f"{emoji} *{titulo}*\n\n"

        if preco_desconto:
            preco_fmt = f"R$ {preco_desconto:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            msg += f"💰 *{preco_fmt}*"

            if preco_original and preco_original > preco_desconto:
                preco_orig_fmt = f"R$ {preco_original:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                msg += f" ~~~{preco_orig_fmt}~~~"

            msg += "\n"

        if desconto:
            msg += f"🔥 {desconto:.0f}% OFF\n"

        msg += f"\n🔗 [Ver oferta]({url})"

        if imagem:
            send_photo(api_url, TELEGRAM_CHAT_ID, imagem, msg)
        else:
            send_message(api_url, TELEGRAM_CHAT_ID, msg)

        time.sleep(2)

    console.print(f"[green]✓[/] Telegram: {min(len(produtos), 20)} produtos enviados")


def send_message(api_url, chat_id, text):
    try:
        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "Markdown",
            "disable_web_page_preview": True,
        }
        requests.post(f"{api_url}/sendMessage", json=payload, timeout=10)
    except Exception:
        pass


def send_photo(api_url, chat_id, photo_url, caption):
    try:
        payload = {
            "chat_id": chat_id,
            "photo": photo_url,
            "caption": caption[:1024],
            "parse_mode": "Markdown",
        }
        requests.post(f"{api_url}/sendPhoto", json=payload, timeout=10)
    except Exception:
        pass


def sincronizar_supabase(produtos):
    try:
        dados = []
        for p in produtos:
            dados.append({
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
                "loja": "shopee",
                "vendidos": p.get("vendidos"),
                "avaliacoes": p.get("avaliacoes"),
            })
        
        inseridos = inserir_supabase(dados)
        console.print(f"[green]✓[/] Supabase: {inseridos} produtos sincronizados")
        return inseridos
    except Exception as e:
        console.print(f"[red]Erro Supabase: {e}[/]")
        return 0


def reload_env():
    global WEBHOOK, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID
    load_dotenv(os.path.join(os.path.dirname(__file__), ".env"), override=True)
    WEBHOOK = os.getenv("WEBHOOK")
    TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
    TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")


def executar_scraping():
    reload_env()
    console.clear()
    exibir_cabecalho()

    if not SHOPEE_AFFILIATE_ID:
        console.print("[yellow]AVISO: ID de afiliado nao configurado. Links serao gerados sem rastreamento.[/]")
        console.print("[dim]Configure a variavel SHOPEE_AFFILIATE_ID no arquivo .env[/]")
        console.print()

    exibir_titulo_secao("INICIANDO SCRAPING DA SHOPEE")

    try:
        produtos = scraping_completo()

        if produtos:
            exibir_titulo_secao("SALVANDO NO BANCO DE DADOS")
            inseridos = inserir_produtos_em_lote(produtos)
            console.print(f"[green]✓[/] {inseridos} produtos salvos com sucesso")

            stats = obter_estatisticas()

            console.clear()
            exibir_cabecalho()
            exibir_estatisticas()
            exibir_lista_produtos(produtos)
            exibir_resumo_atualizacao(inseridos, stats["total_produtos"])

            embeds = [formatar_produto(p) for p in produtos[:10]]
            enviar_discord(embeds)

            produtos_novos = filtrar_novos(produtos)
            console.print(f"[dim]Produtos novos: {len(produtos_novos)} (de {len(produtos)} coletados)[/]")

            enviar_telegram(produtos_novos)

            sincronizar_supabase(produtos)
        else:
            exibir_erro("Nenhum produto encontrado nesta execucao")

    except Exception as e:
        exibir_erro(f"Erro durante o scraping: {str(e)}")


def agendar_execucoes():
    schedule.every(UPDATE_INTERVAL).seconds.do(executar_scraping)

    proxima = datetime.now() + timedelta(seconds=UPDATE_INTERVAL)
    exibir_mensagem_agendamento(proxima.strftime("%d/%m/%Y %H:%M:%S"))

    while True:
        schedule.run_pending()
        time.sleep(1)


def signal_handler(sig, frame):
    console.print("\n[yellow]Bot encerrado pelo usuario.[/]")
    sys.exit(0)


def main():
    signal.signal(signal.SIGINT, signal_handler)

    console.clear()

    init_db()

    exibir_cabecalho()
    console.print("[bold orange1]Bot de Promocoes da Shopee[/]")
    console.print("[dim]Pressione Ctrl+C a qualquer momento para parar[/]")
    console.print()

    if not SHOPEE_AFFILIATE_ID:
        console.print("[yellow]AVISO: Configure seu ID de afiliado no arquivo .env[/]")
        console.print()

    executar_scraping()

    agendar_execucoes()


if __name__ == "__main__":
    main()
