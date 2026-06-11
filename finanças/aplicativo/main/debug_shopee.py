import time
import random
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

chrome_options = Options()
chrome_options.add_argument("--headless=new")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=1920,1080")
chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
chrome_options.add_argument("--disable-blink-features=AutomationControlled")
chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)

print("Acessando Shopee...")
driver.get("https://shopee.com.br/search?keyword=celular")
time.sleep(10)

# Scroll
for i in range(5):
    driver.execute_script("window.scrollBy(0, 800);")
    time.sleep(2)

# Salvar HTML
html = driver.page_source
with open("shopee_debug.html", "w", encoding="utf-8") as f:
    f.write(html)
print(f"HTML salvo: {len(html)} chars")

# Tentar extrair com diferentes seletores
from bs4 import BeautifulSoup
soup = BeautifulSoup(html, "lxml")

seletores = [
    ".shopee-search-item-result__item",
    "[data-sqe='item']",
    ".col-xs-2-4",
    "a[data-sqe='link']",
    "[class*='search-item']",
    "[class*='product-card']",
    "[class*='item-card']",
    "div[class*='result']",
    "div[class*='grid'] > div",
]

for sel in seletores:
    itens = soup.select(sel)
    print(f"Seletor '{sel}': {len(itens)} itens")

# Verificar se tem algum div com classes relevantes
all_divs = soup.find_all("div", class_=True)
classes_unicas = set()
for div in all_divs:
    for cls in div.get("class", []):
        if any(palavra in cls.lower() for palavra in ["item", "product", "card", "grid", "result", "search"]):
            classes_unicas.add(cls)

print(f"\nClasses relevantes encontradas: {classes_unicas}")

# Verificar se a pagina tem conteudo dinamico
scripts = soup.find_all("script")
print(f"\nScripts encontrados: {len(scripts)}")

# Verificar se tem algum dado no __NEXT_DATA__ ou similar
for script in scripts:
    text = script.string or ""
    if "__NEXT_DATA__" in text or "__INITIAL_STATE__" in text:
        print(f"Encontrado script com dados: {text[:200]}")

driver.quit()
