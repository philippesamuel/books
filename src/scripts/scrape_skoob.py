# /// script
# requires-python = ">=3.6"
# dependencies = [
#     "beautifulsoup4>=4.9",
# ]
# ///

from bs4 import BeautifulSoup
import csv, re

status_map = {
    "text-statusRead": "Lido",
    "text-statusReading": "Lendo",
    "text-statusWantToRead": "Quero ler",
    "text-statusRereading": "Relendo",
}

def parse_page(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f.read(), "html.parser")

    books = []
    # Each book card is a <div> containing an <h2> (title) and <h3> (author)
    for h2 in soup.find_all("h2"):
        title = h2.get_text(strip=True)
        if not title:
            continue

        # Author is the next <h3> sibling inside the same parent
        h3 = h2.find_next_sibling("h3")
        author = h3.get_text(strip=True) if h3 else ""

        # Status: the bookmark SVG sits just before the <img> cover,
        # inside a parent <div class="flex">. Its class contains the status color.
        # We walk up from h2 to find the card container, then look for the status SVG.
        card = h2.find_parent("div", class_=re.compile(r"flex"))
        # Go up until we find the outermost card wrapper (contains the cover img)
        while card and not card.find("img", attrs={"alt": re.compile("Capa do livro")}):
            card = card.find_parent("div")

        status = "Desconhecido"
        if card:
            status_svg = card.find("svg", class_=re.compile("text-status"))
            if status_svg:
                for cls in status_svg.get("class", []):
                    if cls in status_map:
                        status = status_map[cls]
                        break
            # If no status SVG found, check for "text-contrast" which is used for "Abandonei"
            if status == "Desconhecido":
                # Abandonei uses text-contrast on the bookmark svg specifically
                bookmark_svg = card.find("svg", class_=re.compile("text-contrast"))
                if bookmark_svg and bookmark_svg.find("path", attrs={"d": re.compile("16.50")}):
                    status = "Abandonei"

        # Rating: a <span> with text like "3.5" next to a star SVG
        rating = ""
        if card:
            star_svg = card.find("svg", class_=re.compile("text-warning"))
            if star_svg:
                rating_span = star_svg.find_next_sibling("span")
                if rating_span:
                    rating = rating_span.get_text(strip=True)

        # Pages: a <span> containing "páginas"
        pages = ""
        if card:
            for span in card.find_all("span"):
                txt = span.get_text(strip=True)
                if "páginas" in txt and txt != "0 páginas":
                    pages = txt.replace("páginas", "").strip()
                    break

        books.append({
            "title": title,
            "author": author,
            "status": status,
            "rating": rating,
            "pages": pages,
        })

    return books

all_books = []
all_books.extend(parse_page("/mnt/user-data/uploads/skoob-bokshelf-page1.html"))
all_books.extend(parse_page("/mnt/user-data/uploads/skoob-bookshelf-page2.html"))

with open("/mnt/user-data/outputs/skoob_books.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=["title", "author", "status", "rating", "pages"])
    writer.writeheader()
    writer.writerows(all_books)

for b in all_books:
    print(f"{b['status']:20} | {b['rating']:>4} | {b['pages']:>4}p | {b['title']} — {b['author']}")

print(f"\n{len(all_books)} books total → skoob_books.csv")
