import requests
from bs4 import BeautifulSoup
import os

def scrape_books_to_html(args: dict) -> dict:
    """Scrape the list of books from the given URL and write an HTML table.

    Args:
        args (dict): {
            "url": "https://books.toscrape.com/",
            "output_path": "books.html"
        }
    Returns:
        dict: {"ok": True, "output_path": "books.html"} on success,
              or {"ok": False, "error": "msg"} on failure.
    """
    url = args.get("url")
    output_path = args.get("output_path", "books.html")
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        return {"ok": False, "error": f"Network error: {e}"}
    try:
        soup = BeautifulSoup(response.text, "html.parser")
        books = []
        for article in soup.select("article.product_pod"):
            a_tag = article.select_one("h3 a")
            title = a_tag.get("title", "").strip()
            link = a_tag.get("href", "")
            # Resolve relative URLs
            if not link.startswith("http"):
                link = requests.compat.urljoin(url, link)
            price_tag = article.select_one("p.price_color")
            price = price_tag.text.strip() if price_tag else ""
            books.append({"title": title, "price": price, "link": link})
    except Exception as e:
        return {"ok": False, "error": f"Parsing error: {e}"}
    # Build HTML
    html_parts = [
        "<!DOCTYPE html>",
        "<html lang='en'>",
        "<head><meta charset='UTF-8'><title>Books from books.toscrape.com</title>",
        "<style>table{border-collapse:collapse;width:100%}th,td{border:1px solid #ddd;padding:8px}th{background:#f2f2f2}</style>",
        "</head>",
        "<body>",
        "<h1>Books scraped from books.toscrape.com</h1>",
        "<table>",
        "<tr><th>Title</th><th>Price</th><th>Link</th></tr>"
    ]
    for b in books:
        html_parts.append(
            f"<tr><td>{b['title']}</td><td>{b['price']}</td><td><a href='{b['link']}' target='_blank'>View</a></td></tr>"
        )
    html_parts.extend(["</table>", "</body>", "</html>"])
    html_content = "\n".join(html_parts)
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_content)
    except OSError as e:
        return {"ok": False, "error": f"File write error: {e}"}
    return {"ok": True, "output_path": os.path.abspath(output_path)}
