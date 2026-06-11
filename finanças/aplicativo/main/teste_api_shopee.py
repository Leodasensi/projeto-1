import httpx
import json

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json",
    "Referer": "https://shopee.com.br/",
    "X-Requested-With": "XMLHttpRequest",
    "Accept-Language": "pt-BR,pt;q=0.9",
}

url = "https://shopee.com.br/api/v4/search/search_items"
params = {
    "by": "relevancy",
    "keyword": "celular",
    "limit": 20,
    "newest": 0,
    "order": "desc",
    "page_type": "search",
    "scenario": "PAGE_GLOBAL_SEARCH",
    "version": 2,
}

client = httpx.Client(headers=headers, follow_redirects=True, timeout=15)
resp = client.get(url, params=params)
print(f"Status: {resp.status_code}")
print(f"Content-Type: {resp.headers.get('content-type')}")

data = resp.json()
print(f"Keys: {list(data.keys())}")
items = data.get("items", [])
print(f"Items: {len(items)}")

if items:
    item = items[0]
    item_data = item.get("item_basic", item)
    print(f"\nFirst item:")
    print(f"  Name: {item_data.get('name', 'N/A')[:60]}")
    print(f"  Price: {item_data.get('price', 'N/A')}")
    print(f"  Price Max: {item_data.get('price_max', 'N/A')}")
    print(f"  Sold: {item_data.get('historical_sold', 'N/A')}")
    print(f"  Shop ID: {item_data.get('shopid', 'N/A')}")
    print(f"  Item ID: {item_data.get('itemid', 'N/A')}")
else:
    print(f"\nResponse: {json.dumps(data, indent=2)[:500]}")
