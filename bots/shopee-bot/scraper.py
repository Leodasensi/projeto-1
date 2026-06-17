import time
import random
import json
import os
import pickle
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
import undetected_chromedriver as uc

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from config import (
    URL_BASE, MAX_PAGES, REQUEST_DELAY, VERBOSE,
    USER_AGENTS, get_affiliate_url, CATEGORIAS, DOMAIN
)

COOKIES_FILE = Path(__file__).parent / "cookies.pkl"
SHOPEE_EMAIL = os.getenv("SHOPEE_EMAIL", "")
SHOPEE_PASSWORD = os.getenv("SHOPEE_PASSWORD", "")


def detectar_versao_chrome():
    try:
        import winreg
        k = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Google\Chrome\BLBeacon")
        versao, _ = winreg.QueryValueEx(k, "version")
        return int(versao.split(".")[0])
    except Exception:
        pass
    return None


def criar_driver():
    options = uc.ChromeOptions()
    # options.add_argument("--headless=new")  # Desabilitado para testar
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument(f"user-agent={random.choice(USER_AGENTS)}")
    options.set_capability("goog:loggingPrefs", {"performance": "ALL"})

    versao = detectar_versao_chrome()
    log(f"Chrome detectado: versao {versao}")
    driver = uc.Chrome(options=options, version_main=versao)
    return driver


def salvar_cookies(driver):
    cookies = driver.get_cookies()
    pickle.dump(cookies, open(COOKIES_FILE, "wb"))
    log(f"Cookies salvos ({len(cookies)} cookies)")


def carregar_cookies(driver):
    if COOKIES_FILE.exists():
        try:
            driver.get(URL_BASE)
            time.sleep(2)
            cookies = pickle.load(open(COOKIES_FILE, "rb"))
            for cookie in cookies:
                try:
                    driver.add_cookie(cookie)
                except:
                    pass
            log(f"Cookies carregados ({len(cookies)} cookies)")
            return True
        except Exception as e:
            log(f"Erro ao carregar cookies: {e}")
            return False
    return False


def login_shopee(driver):
    if not SHOPEE_EMAIL or not SHOPEE_PASSWORD:
        log("Credenciais SHOPEE_EMAIL/SHOPEE_PASSWORD nao configuradas")
        return False

    # Tentar cookies primeiro
    if carregar_cookies(driver):
        driver.get(URL_BASE)
        time.sleep(3)
        # Verificar se esta logado
        page_source = driver.page_source.lower()
        if "login" not in driver.current_url.lower() and "entrar" not in page_source[:1000]:
            log("Login via cookies OK")
            return True
        log("Cookies expirados, fazendo login novamente")

    log("Fazendo login na Shopee...")
    driver.get(f"{URL_BASE}/buyer/login")
    time.sleep(5)

    try:
        # Selecionar idioma Portugues
        try:
            lang_btn = WebDriverWait(driver, 5).until(
                lambda d: d.find_element(By.XPATH, "//button[contains(text(), 'Portugu')]")
            )
            lang_btn.click()
            log("Idioma selecionado")
            time.sleep(2)
        except:
            pass

        # Aceitar cookies se aparecer
        try:
            cookie_btn = driver.find_element(By.XPATH, "//button[contains(text(), 'Aceitar')]")
            cookie_btn.click()
            time.sleep(1)
        except:
            pass

        email_input = WebDriverWait(driver, 10).until(
            lambda d: d.find_element(By.CSS_SELECTOR, "input[name='loginKey']")
        )
        email_input.clear()
        email_input.send_keys(SHOPEE_EMAIL)
        time.sleep(1)

        pass_input = driver.find_element(By.CSS_SELECTOR, "input[name='password']")
        pass_input.clear()
        pass_input.send_keys(SHOPEE_PASSWORD)
        time.sleep(1)

        # Botao ENTRAR via JS
        login_btn = WebDriverWait(driver, 5).until(
            lambda d: d.find_element(By.CSS_SELECTOR, "button.b5aVaf.PVSuiZ.Gqupku")
        )
        driver.execute_script("arguments[0].click();", login_btn)
        time.sleep(6)

        if "login" not in driver.current_url.lower():
            log("Login realizado com sucesso")
            salvar_cookies(driver)
            return True
        else:
            log("Falha no login - verifique credenciais")
            return False

    except Exception as e:
        log(f"Erro durante login: {e}")
        return False


def log(mensagem):
    if VERBOSE:
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"  [{timestamp}] {mensagem}")


def scroll_pagina(driver, vezes=5):
    for i in range(vezes):
        driver.execute_script("window.scrollBy(0, 800);")
        time.sleep(1.5)


def extrair_produtos_via_js(driver):
    """Extrai dados dos produtos via JavaScript executado no browser"""
    try:
        produtos = driver.execute_script("""
            var produtos = [];

            // Tentar pegar de diferentes seletores
            var cards = document.querySelectorAll(
                '.shopee-search-item-result__item, ' +
                '[data-sqe="item"], ' +
                '.col-xs-2-4, ' +
                'a[data-sqe="link"]'
            );

            cards.forEach(function(card) {
                try {
                    var titulo = '';
                    var link = '';
                    var precoOriginal = null;
                    var precoDesconto = null;
                    var imagem = '';
                    var vendidos = '';

                    // Titulo
                    var tituloEl = card.querySelector(
                        '[data-sqe="name"], ' +
                        '.shopee-search-item-result__item-name, ' +
                        'div._24kIg, ' +
                        'div._1s31Jj, ' +
                        'div.ie3A\\+n, ' +
                        'div.line-clamp-2'
                    );
                    if (tituloEl) titulo = tituloEl.innerText.trim();

                    // Link
                    var linkEl = card.querySelector('a[href*="/product/"], a[href*="-i."]');
                    if (!linkEl) linkEl = card.closest('a') || card.querySelector('a');
                    if (linkEl) link = linkEl.href || linkEl.getAttribute('href') || '';

                    // Imagem
                    var imgEl = card.querySelector('img');
                    if (imgEl) imagem = imgEl.src || imgEl.dataset.src || '';

                    // Precos - pegar todos os spans com valores
                    var priceEls = card.querySelectorAll('span');
                    var precos = [];
                    priceEls.forEach(function(el) {
                        var texto = el.innerText.trim();
                        if (texto.match(/R\\$/) || texto.match(/\\d+[,.]\\d+/)) {
                            var valor = texto.replace('R$', '').replace('.', '').replace(',', '.').trim();
                            valor = parseFloat(valor);
                            if (valor > 0 && valor < 100000) precos.push(valor);
                        }
                    });

                    if (precos.length >= 2) {
                        precoOriginal = Math.max.apply(null, precos);
                        precoDesconto = Math.min.apply(null, precos);
                    } else if (precos.length === 1) {
                        precoDesconto = precos[0];
                    }

                    // Vendidos
                    var soldEl = card.querySelector(
                        '.shopee-search-item-result__item-sold, ' +
                        'div._245-SC, ' +
                        'span[class*="sold"]'
                    );
                    if (soldEl) vendidos = soldEl.innerText.trim();

                    if (titulo && link) {
                        produtos.push({
                            titulo: titulo,
                            url: link,
                            precoOriginal: precoOriginal,
                            precoDesconto: precoDesconto,
                            imagem: imagem,
                            vendidos: vendidos
                        });
                    }
                } catch(e) {}
            });

            return produtos;
        """)
        return produtos or []
    except Exception as e:
        log(f"Erro ao extrair via JS: {e}")
        return []


def extrair_produtos_api_log(driver):
    """Tenta extrair dados dos logs de performance (API responses)"""
    produtos = []
    try:
        logs = driver.get_log("performance")
        for entry in logs:
            try:
                msg = json.loads(entry["message"])["message"]
                if msg["method"] == "Network.responseReceived":
                    url = msg["params"]["response"]["url"]
                    if "/api/v4/search/search_items" in url or "/api/v4/recommend" in url:
                        request_id = msg["params"]["requestId"]
                        try:
                            body = driver.execute_cdp_cmd(
                                "Network.getResponseBody", {"requestId": request_id}
                            )
                            data = json.loads(body["body"])
                            items = data.get("items", [])
                            for item in items:
                                item_data = item.get("item_basic", item)
                                if not item_data.get("name"):
                                    continue

                                preco_original = (item_data.get("price_max", 0) or item_data.get("price", 0))
                                preco_desconto = (item_data.get("price", 0) or item_data.get("price_min", 0))
                                if preco_original > 100000: preco_original /= 100000
                                if preco_desconto > 100000: preco_desconto /= 100000

                                imagem = item_data.get("image", "")
                                if imagem and not imagem.startswith("http"):
                                    imagem = f"https://down-br.img.susercontent.com/file/{imagem}"

                                shop_id = item_data.get("shopid", "")
                                item_id = item_data.get("itemid", "")
                                url_produto = f"https://shopee.com.br/product/{shop_id}/{item_id}"

                                desconto = None
                                if preco_original > preco_desconto > 0:
                                    desconto = round(((preco_original - preco_desconto) / preco_original) * 100, 1)

                                rating = item_data.get("item_rating", {})
                                stars = rating.get("rating_star") if isinstance(rating, dict) else None

                                produtos.append({
                                    "produto_id": str(item_id),
                                    "titulo": item_data.get("name", ""),
                                    "url_original": url_produto,
                                    "url_afiliado": get_affiliate_url(url_produto),
                                    "preco_original": round(preco_original, 2) if preco_original else None,
                                    "preco_desconto": round(preco_desconto, 2) if preco_desconto else None,
                                    "porcentagem_desconto": desconto,
                                    "imagem_url": imagem,
                                    "especificacoes": "",
                                    "categoria": detectar_categoria(item_data.get("name", "")),
                                    "vendedor": "",
                                    "avaliacoes": stars,
                                    "vendidos": item_data.get("historical_sold") or item_data.get("sold"),
                                    "localizacao": "",
                                    "data_coleta": datetime.now().isoformat(),
                                })
                        except Exception:
                            pass
            except Exception:
                continue
    except Exception:
        pass
    return produtos


def detectar_categoria(titulo):
    titulo_lower = titulo.lower()
    categorias_map = {
        "celular": ["celular", "smartphone", "iphone", "samsung galaxy", "motorola", "xiaomi", "redmi"],
        "computador": ["notebook", "computador", "pc", "desktop", "macbook", "chromebook", "mac"],
        "monitor": ["monitor", "tela", "display", "ultrawide"],
        "tv": ["tv", "televisao", "smart tv", "led tv", "oled", "qled"],
        "audio": ["fone", "headphone", "caixa de som", "bluetooth", "airpods", "audifono", "speaker"],
        "gaming": ["gamer", "xbox", "playstation", "ps5", "ps4", "nintendo", "controle", "game"],
        "eletrodomesticos": ["geladeira", "microondas", "lavadora", "aspirador", "air fryer", "cafeteira"],
        "casa": ["ventilador", "ar condicionado", "luminaria", "cadeira", "mesa", "decoracao"],
        "esportes": ["bicicleta", "esteira", "halteres", "bola", "esportivo", "fitness"],
        "beleza": ["maquiagem", "cabelo", "pele", "perfume", "skincare", "batom"],
        "automotivo": ["carro", "moto", "pneu", "oleo", "acessorio automotivo", "led automotivo"],
        "ferramentas": ["furadeira", "parafusadeira", "serra", "ferramenta", "multimetro"],
        "moda": ["camisa", "calca", "vestido", "tenis", "sapato", "bolsa", "relogio"],
    }
    for categoria, palavras in categorias_map.items():
        for palavra in palavras:
            if palavra in titulo_lower:
                return categoria
    return "geral"


def scraping_pagina(driver, url, max_paginas=None):
    if max_paginas is None:
        max_paginas = MAX_PAGES

    todos_produtos = []
    log(f"Acessando: {url}")

    try:
        driver.get(url)
        time.sleep(6)

        WebDriverWait(driver, 15).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )
        time.sleep(3)

        scroll_pagina(driver, 8)
        time.sleep(3)

        # Metodo 1: Extrair via JS do DOM
        produtos_js = extrair_produtos_via_js(driver)
        log(f"Via DOM: {len(produtos_js)} produtos")

        for p in produtos_js:
            preco_orig = p.get("precoOriginal")
            preco_desc = p.get("precoDesconto")
            desconto = None
            if preco_orig and preco_desc and preco_orig > preco_desc > 0:
                desconto = round(((preco_orig - preco_desc) / preco_orig) * 100, 1)

            vendidos_num = None
            sold_text = p.get("vendidos", "")
            if sold_text:
                sold_text = sold_text.lower().replace("vendidos", "").replace("vendido", "").strip()
                if "k" in sold_text:
                    try: vendidos_num = int(float(sold_text.replace("k", "")) * 1000)
                    except: pass
                else:
                    try: vendidos_num = int(sold_text)
                    except: pass

            url_produto = p.get("url", "")
            if url_produto and not url_produto.startswith("http"):
                url_produto = f"https://{DOMAIN}{url_produto}"

            todos_produtos.append({
                "produto_id": "",
                "titulo": p.get("titulo", ""),
                "url_original": url_produto,
                "url_afiliado": get_affiliate_url(url_produto),
                "preco_original": preco_orig,
                "preco_desconto": preco_desc,
                "porcentagem_desconto": desconto,
                "imagem_url": p.get("imagem", ""),
                "especificacoes": "",
                "categoria": detectar_categoria(p.get("titulo", "")),
                "vendedor": "",
                "avaliacoes": None,
                "vendidos": vendidos_num,
                "localizacao": "",
                "data_coleta": datetime.now().isoformat(),
            })

        # Metodo 2: Extrair via logs de API
        produtos_api = extrair_produtos_api_log(driver)
        log(f"Via API: {len(produtos_api)} produtos")
        todos_produtos.extend(produtos_api)

        for pagina in range(1, max_paginas):
            log(f"Scraping pagina {pagina + 1}/{max_paginas}")
            try:
                next_btn = driver.find_element(
                    By.CSS_SELECTOR,
                    "button.shopee-icon-button--right, [class*='next-page']"
                )
                driver.execute_script("arguments[0].click();", next_btn)
                time.sleep(4)
                scroll_pagina(driver, 5)
                time.sleep(2)

                produtos_js = extrair_produtos_via_js(driver)
                log(f"Via DOM: {len(produtos_js)} produtos")
                for p in produtos_js:
                    preco_orig = p.get("precoOriginal")
                    preco_desc = p.get("precoDesconto")
                    desconto = None
                    if preco_orig and preco_desc and preco_orig > preco_desc > 0:
                        desconto = round(((preco_orig - preco_desc) / preco_orig) * 100, 1)
                    url_produto = p.get("url", "")
                    if url_produto and not url_produto.startswith("http"):
                        url_produto = f"https://{DOMAIN}{url_produto}"
                    todos_produtos.append({
                        "produto_id": "", "titulo": p.get("titulo", ""),
                        "url_original": url_produto, "url_afiliado": get_affiliate_url(url_produto),
                        "preco_original": preco_orig, "preco_desconto": preco_desc,
                        "porcentagem_desconto": desconto, "imagem_url": p.get("imagem", ""),
                        "especificacoes": "", "categoria": detectar_categoria(p.get("titulo", "")),
                        "vendedor": "", "avaliacoes": None, "vendidos": None,
                        "localizacao": "", "data_coleta": datetime.now().isoformat(),
                    })

                produtos_api = extrair_produtos_api_log(driver)
                log(f"Via API: {len(produtos_api)} produtos")
                todos_produtos.extend(produtos_api)

            except NoSuchElementException:
                log("Nao ha mais paginas")
                break

    except Exception as e:
        log(f"Erro ao acessar pagina: {e}")

    return todos_produtos


def scraping_ofertas_do_dia(driver, max_paginas=None):
    url = f"{URL_BASE}/daily_discover"
    return scraping_pagina(driver, url, max_paginas)


def scraping_flash_sale(driver):
    url = f"{URL_BASE}/flash_sale"
    return scraping_pagina(driver, url, 1)


def scraping_categoria(driver, categoria_nome, categoria_url, max_paginas=None):
    log(f"Scraping categoria: {categoria_nome}")
    produtos = scraping_pagina(driver, categoria_url, max_paginas)
    for p in produtos:
        if not p.get("categoria") or p["categoria"] == "geral":
            p["categoria"] = categoria_nome
    return produtos


def scraping_completo(categorias_selecionadas=None):
    driver = criar_driver()
    todos_produtos = []

    try:
        log("Iniciando scraping completo da Shopee...")

        if not login_shopee(driver):
            log("Nao foi possivel fazer login. Continuando sem login...")
            driver.get(URL_BASE)
            time.sleep(5)

        # Focar em buscas que tem produtos
        categorias_busca = [
            "tecnologia", "celulares", "notebooks", "fones", 
            "smartwatch", "eletrodomesticos", "beleza", "games"
        ]
        
        if categorias_selecionadas:
            categorias_busca = [c for c in categorias_selecionadas if c in CATEGORIAS]
        
        for nome_cat in categorias_busca:
            if nome_cat in CATEGORIAS:
                url_cat = CATEGORIAS[nome_cat]
                if "/search?" in url_cat:
                    produtos_cat = scraping_categoria(driver, nome_cat, url_cat, max_paginas=1)
                    todos_produtos.extend(produtos_cat)
                    log(f"Categoria {nome_cat}: {len(produtos_cat)} produtos")

    finally:
        driver.quit()

    produtos_unicos = remover_duplicatas(todos_produtos)
    log(f"Total final: {len(produtos_unicos)} produtos unicos")
    return produtos_unicos


def remover_duplicatas(produtos):
    urls_vistas = set()
    produtos_unicos = []
    for produto in produtos:
        url = produto.get("url_original", "")
        if url and url not in urls_vistas:
            urls_vistas.add(url)
            produtos_unicos.append(produto)
    return produtos_unicos
