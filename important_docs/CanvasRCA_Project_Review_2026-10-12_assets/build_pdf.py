"""Render the English meeting report to PDF; no experiment code is executed.

Requires markdown, beautifulsoup4, weasyprint and pymupdf.
Usage: python build_pdf.py [report.md] [output.pdf]
"""
from pathlib import Path
import re
import sys
from urllib.parse import unquote

import markdown
from bs4 import BeautifulSoup
import fitz
from weasyprint import HTML, CSS

HERE = Path(__file__).resolve().parent
NAME = "CanvasRCA_Project_Review_and_Research_Roadmap_2026-10-12"
REPORT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else HERE.parent / (NAME + ".md")
OUTPUT = Path(sys.argv[2]).resolve() if len(sys.argv) > 2 else REPORT.with_suffix(".pdf")

body = markdown.markdown(REPORT.read_text(), extensions=["tables", "fenced_code", "toc", "sane_lists"])
soup = BeautifulSoup(body, "html.parser")
# Use the vector editions of analytical figures in print. Original dashboards
# keep their exact high-resolution pixel content.
for img in soup.find_all("img"):
    src = img["src"]
    if Path(src).name.startswith("fig_") and src.endswith(".png"):
        img["src"] = src[:-4] + ".svg"
    paragraph = img.parent
    if paragraph.name == "p":
        figure = soup.new_tag("figure")
        paragraph.replace_with(figure)
        figure.append(paragraph)
        nxt = figure.find_next_sibling()
        if nxt and nxt.name == "p" and nxt.get_text().startswith("Figure "):
            nxt.name = "figcaption"
            figure.append(nxt.extract())
        prev = figure.find_previous_sibling()
        if prev and prev.name == "p" and re.match(r"[A-E]\. RQ", prev.get_text()):
            prev["class"] = ["example-title"]
            figure.insert(0, prev.extract())
            figure["class"] = ["dashboard-example"]
for table in soup.find_all("table"):
    cols = len(table.find("tr").find_all(["th", "td"], recursive=False))
    table["class"] = [f"cols-{cols}"]
    if "What remains in text" in table.get_text():
        table["class"].append("hybrid-table")
        group = soup.new_tag("colgroup")
        for width in (20, 23, 20, 37):
            col = soup.new_tag("col", style=f"width: {width}%")
            group.append(col)
        table.insert(0, group)
    if table.find("th").get_text() == "Label":
        table["class"].append("glossary-table")
# Add safe break opportunities to long identifiers without changing their text.
for code in soup.find_all("code"):
    if code.parent.name == "pre":
        continue
    value = code.get_text()
    code.clear()
    for part in re.split(r"(?<=[_/])", value):
        code.append(part)
        code.append(soup.new_tag("wbr"))

html = '<!doctype html><html lang="en"><head><meta charset="utf-8">'
html += '<title>CanvasRCA - Project Review and Research Roadmap</title>'
html += '<meta name="author" content="CanvasRCA project"></head><body>'
html += str(soup) + '</body></html>'
OUTPUT.parent.mkdir(parents=True, exist_ok=True)
raw = OUTPUT.with_suffix(".rendering.pdf")
HTML(string=html, base_url=str(REPORT.parent)).write_pdf(raw, stylesheets=[CSS(filename=str(HERE / "report_pdf.css"))])
# Keep local citations portable instead of embedding this machine's file:// URI.
doc = fitz.open(raw)
prefix = REPORT.parent.as_uri() + "/"
converted = 0
for page in doc:
    for link in page.get_links():
        uri = link.get("uri", "")
        if uri.startswith(prefix):
            link["uri"] = unquote(uri[len(prefix):])
            page.update_link(link)
            converted += 1
        elif link.get("kind") == fitz.LINK_LAUNCH:
            # File-launch actions open the Markdown source, not its web anchor.
            target = Path(unquote(link.get("file", "")).split("#", 1)[0])
            if target.is_absolute() and target.is_relative_to(REPORT.parent):
                link["file"] = str(target.relative_to(REPORT.parent))
                page.update_link(link)
                converted += 1
doc.save(OUTPUT, garbage=4, deflate=True)
print({"pdf": str(OUTPUT), "pages": len(doc), "portable_links": converted, "bytes": OUTPUT.stat().st_size})
doc.close()
raw.unlink()
