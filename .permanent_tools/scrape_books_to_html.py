import requests
from bs4 import BeautifulSoup
import os

def scrape_books_to_html(args: dict) -> dict:
    """Scrape https://books.toscrape.com/ and write results to an HTML file.
    Args dict must contain:
        - url: str, the page to scrape (e.g., 'https://books.toscrape.com/')
        - output_path: str, path where the HTML will be saved
    Returns a dict with keys 'ok' (bool) and either 'output_path' (str) or 'error' (str).
    """
    url = args.get('url')
    output_path = args.get('output_path')
    if not url or not output_path:
        return {'ok': False, 'error': 'Missing url or output_path'}
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        return {'ok': False, 'error': f'Network error: {e}'}
    try:
        soup = BeautifulSoup(response.text, 'html.parser')
        books = soup.select('article.product_pod')
        rows = []
        for book in books:
            title_tag = book.h3.a
            title = title_tag['title'] if title_tag.has_attr('title') else title_tag.text.strip()
            link = title_tag['href']
            # Ensure full URL
            link = requests.compat.urljoin(url, link)
            price_tag = book.select_one('p.price_color')
            price = price_tag.text.strip() if price_tag else 'N/A'
            rows.append((title, price, link))
        # Build HTML
        html_parts = [
            '<!DOCTYPE html>',
            '<html lang="en">',
            '<head>',
            '<meta charset="UTF-8">',
            '<title>Books Scraped from books.toscrape.com</title>',
            '<style>',
            'table {border-collapse: collapse; width: 100%;}',
            'th, td {border: 1px solid #ddd; padding: 8px;}',
            'th {background-color: #f2f2f2;}',
            '</style>',
            '</head>',
            '<body>',
            '<h1>Books from books.toscrape.com</h1>',
            '<table>',
            '<tr><th>Title</th><th>Price</th><th>Link</th></tr>'
        ]
        for title, price, link in rows:
            html_parts.append(
                f'<tr><td>{title}</td><td>{price}</td><td><a href="{link}" target="_blank">View</a></td></tr>'
            )
        html_parts.extend(['</table>', '</body>', '</html>'])
        html_content = '\n'.join(html_parts)
        # Write file
        os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        return {'ok': True, 'output_path': os.path.abspath(output_path)}
    except Exception as e:
        return {'ok': False, 'error': f'Parsing/IO error: {e}'}