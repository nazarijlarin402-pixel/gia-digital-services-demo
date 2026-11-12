"""Daily GIA media kit, generated and published to owner-controlled Pages.

No client data, ads, fake screenshots or unauthorized social-platform writes.
Creates original typographic JPEG posters and their caption/alt metadata.
"""
from __future__ import annotations
import datetime as dt
import hashlib
import html
import json
from pathlib import Path
from zoneinfo import ZoneInfo

from visual_renderer import COPY,LANGUAGES,TOPICS,SIZES,draw_card,caption

ROOT=Path(__file__).resolve().parent.parent
ZONE=ZoneInfo("Europe/Warsaw")
BASE="https://nazarijlarin402-pixel.github.io/gia-digital-services-demo/"
WEB="https://gia-2p2.pages.dev/"
RETENTION=30

def _write_if_changed(path,body):
    path.parent.mkdir(parents=True,exist_ok=True)
    if path.is_file() and path.read_bytes()==body:
        return False
    path.write_bytes(body)
    return True

def build(now=None):
    today=(dt.datetime.now(ZONE) if now is None else now.astimezone(ZONE)).date()
    date=today.isoformat()
    lang=LANGUAGES[today.toordinal()%len(LANGUAGES)]
    topic=TOPICS[(today.toordinal()//2)%len(TOPICS)]
    folder=ROOT/"media"/date
    folder.mkdir(parents=True,exist_ok=True)
    text=caption(lang,topic)
    details={
        "date":date,"language":lang,"topic":topic,
        "caption":text,"disclosure":"Original programmatic illustration; not a photo",
        "source":"original GIA services portfolio",
        "channels":{"instagram":"awaiting_verified_connection",
                    "facebook":"awaiting_verified_connection",
                    "linkedin":"awaiting_verified_connection"},
        "images":{}
    }
    for fmt,(width,height) in SIZES.items():
        path=folder/(fmt+".jpg")
        # Do not regenerate already committed daily graphics when scheduled
        # actions run more than once on the same day.
        if not path.is_file():
            image=draw_card(date,fmt,lang,topic)
            from io import BytesIO
            buffer=BytesIO()
            image.save(buffer,format="JPEG",quality=84,optimize=True,
                       progressive=True)
            _write_if_changed(path,buffer.getvalue())
        if path.stat().st_size>800000:
            raise ValueError("Media is too large for safe public posting")
        details["images"][fmt]={
           "url":BASE+"media/"+date+"/"+fmt+".jpg",
           "width":width,"height":height,
           "sha256":hashlib.sha256(path.read_bytes()).hexdigest()
        }
    _write_if_changed(folder/"captions.json",
                      (json.dumps(details,ensure_ascii=False,indent=2)+"\n").encode("utf-8"))
    # Keep history finite. Public posts already stored elsewhere are
    # never removed, but our archive has a bounded 30-day file lifetime.
    archive=ROOT/"media"
    for entry in archive.iterdir():
        if not entry.is_dir():
            continue
        try:old=dt.date.fromisoformat(entry.name)
        except ValueError:continue
        if (today-old).days>RETENTION:
            for file in entry.iterdir():
                if file.is_file() and not file.is_symlink():
                    file.unlink()
            entry.rmdir()
    records=[]
    for folder in sorted((e for e in archive.iterdir() if e.is_dir()),
                         reverse=True)[:16]:
        meta=folder/"captions.json"
        if not meta.is_file():continue
        info=json.loads(meta.read_text(encoding="utf-8"))
        records.append((info["date"],info["language"],info["topic"],
                        info["images"]["feed"]["url"]))
    cards="".join(
      '<article><img src="'+html.escape(url)+'" alt="GIA original '
      +html.escape(topic)+' educational promo in '+html.escape(lang)
      +'" loading="lazy" width="360" height="450">'
      +'<p>'+html.escape(date)+' · '+html.escape(lang)
      +' · '+html.escape(topic)+'</p></article>'
      for date,lang,topic,url in records)
    page="""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>GIA · Original Media Studio</title>
<meta name="description" content="Original illustrative campaign graphics in English, Ukrainian and Polish for GIA digital services.">
<meta name="robots" content="index,follow">
<style>
body{background:#0d1628;color:#ebf4fb;font-family:system-ui,sans-serif;
max-width:1180px;margin:auto;padding:35px 22px;line-height:1.65}
a{color:#6edce0}a:focus-visible{outline:3px solid #6edce0}
h1{font-size:clamp(2rem,5vw,3.2rem)}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:22px}
article{border-radius:14px;border:1px solid #30415d;padding:14px}
img{width:100%;height:auto;border-radius:8px}
small,p{color:#bac9db}</style></head><body>
<header><a href="../">GIA / Work samples</a></header>
<h1>Original media studio</h1>
<p>Programmatically generated illustrations for small digital tasks.
No previous clients, orders, results or customer testimonials are implied.</p>
<p><a href="https://gia-2p2.pages.dev/">Discuss a project on GIA</a></p>
<div class="grid">"""+cards+"""</div>
<p><small>Illustrative designs only · © GIA original work</small></p>
</body></html>
"""
    _write_if_changed(archive/"index.html",page.encode("utf-8"))
    print(json.dumps({"date":date,"language":lang,"topic":topic,
                      "media_assets":len(details["images"]),
                      "historical_days":len(records),
                      "social_posts_sent":0}))

if __name__=="__main__":
    build()
