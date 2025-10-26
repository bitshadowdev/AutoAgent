import requests
from bs4 import BeautifulSoup
import os

def scrape_books_to_html(args):
    url = args.get('url')
    output_path = args.get('output_path')
    result = {'ok': False, 'error': None, 'output_path': None}
    # Download the page
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        result['error'] = f'Network error: {e}'
        return result
    # Parse the HTML and extract data
    try:
        soup = BeautifulSoup(response.text, 'html.parser')
        books = []
        for article in soup.select('article.product_pod'):
            title_tag = article.select_one('h3 a')
            title = title_tag['title'].strip() if title_tag else 'N/A'
            link = title_tag['href'].strip() if title_tag else '#'
            price_tag = article.select_one('p.price_color')
            price = price_tag.text.strip() if price_tag else 'N/A'
            books.append({'title': title, 'price': price, 'link': link})
        # Build HTML content
        html_parts = [
            '<html>',
            '<head><meta charset="utf-8"><title>Books</title></head>',
            '<body>',
            '<h1>Books from books.toscrape.com</h1>',
            '<table border="1" cellpadding="5" cellspacing="0">',
            '<tr><th>Title</th><th>Price</th><th>Link</th></tr>'
        ]
        for b in books:
            html_parts.append(
                f"<tr><td>{b['title']}</td><td>{b['price']}</td><td><a href='{b['link']}'>Link</a></td></tr>"
            )
        html_parts.extend(['</table>', '</body>', '</html>'])
        html_content = '\n'.join(html_parts)
        # Write to file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        result['ok'] = True
        result['output_path'] = os.path.abspath(output_path)
    except Exception as e:
        result['error'] = f'Parsing or writing error: {e}'
    return result