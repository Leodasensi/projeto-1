import sys
sys.path.insert(0, r"C:\Users\glaon\OneDrive\Documents\VS code\programação\VS code\projetos incompletos\finanças\aplicativo\main\shopee-bot")
from scraper import scraping_completo

produtos = scraping_completo()
print(f"Total: {len(produtos)} produtos")
for p in produtos[:5]:
    titulo = p.get("titulo", "")[:50]
    preco = p.get("preco_desconto", 0)
    print(f"  - {titulo} | R$ {preco}")
