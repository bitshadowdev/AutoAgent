import requests
from bs4 import BeautifulSoup
import os

def scrape_books_to_html(args: dict) -> dict:
    """
    Scrape the main page of https://books.toscrape.com/ and generate an HTML file
    with a table of book title, price and link.
    Args expects keys:
        url: str - URL to scrape (e.g., 'https://books.toscrape.com/')
        output_path: str - Path to write the generated HTML file
    Returns a dict with 'ok': bool and either 'output_path' or 'error'.
    """
    url = args.get('url')
    output_path = args.get('output_path')
    if not url or not output_path:
        return {'ok': False, 'error': 'Missing required arguments: url and output_path'}
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
            title_tag = book.select_one('h3 a')
            title = title_tag['title'].strip() if title_tag and 'title' in title_tag.attrs else 'N/A'
            link = title_tag['href'].strip() if title_tag and 'href' in title_tag.attrs else '#'
            # Build absolute URL for link
            link = requests.compat.urljoin(url, link)
            price_tag = book.select_one('p.price_color')
            price = price_tag.text.strip() if price_tag else 'N/A'
            rows.append((title, price, link))
        # Build HTML
        html_content = ['<!DOCTYPE html>', '<html lang="en">', '<head>', '<meta charset="UTF-8">',
                        '<title>Books to Scrape - Extracted Data</title>',
                        '<style>',
                        'table {border-collapse: collapse; width: 100%;}',
                        'th, td {border: 1px solid #ddd; padding: 8px;}',
                        'th {background-color: #f2f2f2; text-align: left;}',
                        'tr:hover {background-color: #f5f5f5;}',
                        '</style>', '</head>', '<body>',
                        '<h1>Books extracted from books.toscrape.com</h1>',
                        '<table>', '<tr><th>Title</th><th>Price</th><th>Link</th></tr>']
        for title, price, link in rows:
            html_content.append(f'<tr><td>{title}</td><td>{price}</td><td><a href="{link}" target="_blank">View</a></td></tr>')
        html_content.extend(['</table>', '</body>', '</html>'])
        html_str = "\n".join(html_content)
        # Ensure directory exists
        os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_str)
        return {'ok': True, 'output_path': os.path.abspath(output_path)}
    except Exception as e:
        return {'ok': False, 'error': f'Parsing or writing error: {e}'}
