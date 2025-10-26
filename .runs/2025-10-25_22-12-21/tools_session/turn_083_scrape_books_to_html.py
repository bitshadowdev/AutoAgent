import os
import requests
from bs4 import BeautifulSoup

def scrape_books_to_html(args: dict) -> dict:
    """Scrape https://books.toscrape.com/ and save results to an HTML file.
    Args:
        args: {
            "url": "https://books.toscrape.com/",  # optional, defaults to site
            "output_path": "books.html"            # where to write the HTML
        }
    Returns:
        dict with keys 'ok' (bool), 'output_path' (str) and optional 'error'.
    """
    url = args.get('url', 'https://books.toscrape.com/')
    output_path = args.get('output_path', 'books.html')
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        return {"ok": False, "error": f"Network error: {e}"}
    try:
        soup = BeautifulSoup(response.text, 'html.parser')
        books = []
        for article in soup.select('article.product_pod'):
            title_tag = article.select_one('h3 a')
            title = title_tag['title'] if title_tag else 'N/A'
            link = title_tag['href'] if title_tag else '#'
            # Build absolute URL
            link = requests.compat.urljoin(url, link)
            price_tag = article.select_one('p.price_color')
            price = price_tag.get_text(strip=True) if price_tag else 'N/A'
            books.append({'title': title, 'price': price, 'link': link})
    except Exception as e:
        return {"ok": False, "error": f"Parsing error: {e}"}
    # Build HTML
    html_parts = []
    html_parts.append('<!DOCTYPE html>')
    html_parts.append('<html lang="en">')
    html_parts.append('<head><meta charset="UTF-8"><title>Books to Scrape</title>')
    html_parts.append('<style>table{border-collapse:collapse;width:100%;}th,td{border:1px solid #ddd;padding:8px;}th{background:#f2f2f2;}</style>')
    html_parts.append('</head><body>')
    html_parts.append('<h1>Books from books.toscrape.com</h1>')
    html_parts.append('<table>')
    html_parts.append('<tr><th>#</th><th>Title</th><th>Price</th></tr>')
    for i, b in enumerate(books, start=1):
        html_parts.append(f'<tr><td>{i}</td><td><a href="{b["link"]}" target="_blank">{b["title"]}</a></td><td>{b["price"]}</td></tr>')
    html_parts.append('</table>')
    html_parts.append('</body></html>')
    html_content = "\n".join(html_parts)
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
    except OSError as e:
        return {"ok": False, "error": f"File write error: {e}"}
    # Verify file exists
    if not os.path.isfile(output_path):
        return {"ok": False, "error": "File was not created."}
    return {"ok": True, "output_path": os.path.abspath(output_path)}