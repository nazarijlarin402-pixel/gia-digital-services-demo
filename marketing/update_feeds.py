"""Deterministic RSS and sitemap for original GIA educational pages.

Only links owned by this GitHub Pages portfolio are added to sitemap.xml.
No advertising blast, paid APIs, user profiles, or client data.
"""
from __future__ import annotations

import datetime as dt
import email.utils
import html.parser
import pathlib
import subprocess
import xml.etree.ElementTree as ET

BASE="https://nazarijlarin402-pixel.github.io/gia-digital-services-demo/"
NS="http://www.sitemaps.org/schemas/sitemap/0.9"
ATOM="http://www.w3.org/2005/Atom"
LEGACY=[
    ("How to export spreadsheet-safe CSV","guides/safe-csv-export.md",
     "Practical, reproducible CSV export and safety checks."),
    ("Static landing page project brief","guides/landing-page-project-brief.md",
     "Short preparation checklist for a static website."),
    ("UI localization checklist","guides/ui-localization-checklist.md",
     "Review terminology and placeholders in English, Ukrainian and Polish.")
]

class Metadata(html.parser.HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.title_mode=False
        self.title=""
        self.description=""
        self.article=False
    def handle_starttag(self,tag,attrs):
        attrs=dict(attrs)
        if tag=="title":
            self.title_mode=True
        if tag=="meta" and attrs.get("name","").lower()=="description":
            self.description=attrs.get("content","")
    def handle_endtag(self,tag):
        if tag=="title":
            self.title_mode=False
    def handle_data(self,data):
        if self.title_mode:
            self.title+=data

def commit_date(path):
    value=subprocess.run(["git","log","-1","--format=%cs","--",str(path)],
        check=True,stdout=subprocess.PIPE,text=True).stdout.strip()
    if not value:
        raise ValueError("Publication file must be committed: "+str(path))
    return dt.date.fromisoformat(value)

def items():
    index=pathlib.Path("index.html")
    if not index.is_file():
        raise ValueError("Portfolio homepage unavailable")
    result=[(index,"GIA — Original Digital Task Demonstrations",
             "Practical samples and guides of small digital services.")]
    for path in sorted(pathlib.Path("guides").glob("*.html")):
        if path.name.startswith(".") or not path.is_file():
            continue
        html=path.read_text(encoding="utf-8")
        if not ("GIA" in html and "https://gia-2p2.pages.dev/" in html):
            continue
        parser=Metadata()
        parser.feed(html)
        if not parser.title.strip() or not parser.description.strip():
            continue
        result.append((path,parser.title.strip()[:160],parser.description.strip()[:300]))
        if len(result)>150:
            raise ValueError("Too many articles: inspect new content before publishing")
    return result

def render():
    items_list=items()
    ET.register_namespace("",NS)
    root=ET.Element("{"+NS+"}urlset")
    for path,_,_ in items_list:
        entry=ET.SubElement(root,"{"+NS+"}url")
        ET.SubElement(entry,"{"+NS+"}loc").text=BASE+(
            "" if path.name=="index.html" else path.as_posix())
        ET.SubElement(entry,"{"+NS+"}lastmod").text=commit_date(path).isoformat()
    ET.indent(root,space="  ")
    sitemap=ET.tostring(root,encoding="utf-8",xml_declaration=True)+b"\n"

    ET.register_namespace("atom",ATOM)
    rss=ET.Element("rss",{"version":"2.0"})
    channel=ET.SubElement(rss,"channel")
    def node(name,text,parent=channel):
        ET.SubElement(parent,name).text=text
    node("title","GIA — Practical Digital Guides")
    node("link",BASE)
    node("description","Original digital-work guides and reproducible examples, not client testimonials.")
    node("language","en")
    ET.SubElement(channel,"{"+ATOM+"}link",{
        "href":BASE+"feed.xml","rel":"self","type":"application/rss+xml"})
    for path,title,description in items_list[1:]:
        url=BASE+path.as_posix()
        date=commit_date(path)
        item=ET.SubElement(channel,"item")
        node("title",title,item)
        node("link",url,item)
        node("guid",url,item)
        node("description",description,item)
        node("pubDate",email.utils.format_datetime(
            dt.datetime.combine(date,dt.time(12),dt.timezone.utc)),item)
    for title,path,description in LEGACY:
        if not pathlib.Path(path).is_file():
            continue
        url="https://github.com/nazarijlarin402-pixel/gia-digital-services-demo/blob/main/"+path
        item=ET.SubElement(channel,"item")
        node("title",title,item)
        node("link",url,item)
        node("guid",url,item)
        node("description",description,item)
        date=commit_date(path)
        node("pubDate",email.utils.format_datetime(
            dt.datetime.combine(date,dt.time(12),dt.timezone.utc)),item)
    ET.indent(rss,space="  ")
    feed=ET.tostring(rss,encoding="utf-8",xml_declaration=True)+b"\n"
    return {"sitemap.xml":sitemap,"feed.xml":feed}

def main():
    for filename,payload in render().items():
        output=pathlib.Path(filename)
        before=output.read_bytes() if output.exists() else b""
        if before!=payload:
            output.write_bytes(payload)
            print("updated",filename)
        else:
            print("unchanged",filename)

if __name__=="__main__":
    main()
