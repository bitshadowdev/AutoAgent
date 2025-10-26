import requests
import os
from bs4 import BeautifulSoup

def scrape_books_to_html(args: dict) -> dict:
    """Scrape books.toscrape.com and generate an HTML table.
    Args:
        args: {
            "url": str,          # URL to scrape (e.g., 'https://books.toscrape.com/')
            "output_path": str    # Path for the generated HTML file
        }
    Returns:
        dict with keys 'ok' (bool) and either 'output_path' (str) on success
        or 'error' (str) on failure.
    """
    url = args.get('url')
    output_path = args.get('output_path')
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        return {"ok": False, "error": f"Network error: {e}"}
    try:
        soup = BeautifulSoup(response.text, 'html.parser')
        books = []
        for article in soup.select('article.product_pod'):
            a_tag = article.select_one('h3 a')
            title = a_tag['title'].strip() if a_tag and a_tag.has_attr('title') else 'N/A'
            link = a_tag['href'] if a_tag and a_tag.has_attr('href') else '#'
            # Build absolute URL
            link = requests.compat.urljoin(url, link)
            price_tag = article.select_one('p.price_color')
            price = price_tag.get_text().strip() if price_tag else 'N/A'
            books.append({"title": title, "price": price, "link": link})
        # Build HTML
        html_parts = []
        html_parts.append('<!DOCTYPE html>')
        html_parts.append('<html lang="en">')
        html_parts.append('<head><meta charset="UTF-8"><title>Books Scrape</title>')
        html_parts.append('<style>table {border-collapse: collapse; width: 100%;} th, td {border: 1px solid #ddd; padding: 8px;} th {background-color: #f2f2f2;}</style>')
        html_parts.append('</head><body>')
        html_parts.append('<h1>Books from books.toscrape.com</h1>')
        html_parts.append('<table>')
        html_parts.append('<tr><th>Title</th><th>Price</th><th>Link</th></tr>')
        for b in books:
            html_parts.append(f'<tr><td>{b["title"]}</td><td>{b["price"]}</td><td><a href="{b["link"]}" target="_blank">View</a></td></tr>')
        html_parts.append('</table>')
        html_parts.append('</body></html>')
        html_content = "\n".join(html_parts)
        # Write to file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        # Verify file exists
        if not os.path.isfile(output_path):
            return {"ok": False, "error": "Failed to create HTML file."}
        return {"ok": True, "output_path": os.path.abspath(output_path)}
    except Exception as e:
        return {"ok": False, "error": f"Processing error: {e}"}
