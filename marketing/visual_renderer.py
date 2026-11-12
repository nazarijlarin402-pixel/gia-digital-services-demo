"""GIA autonomous, zero-cost ORIGINAL visual campaign builder.

Generates actual JPEG assets locally, without uploading client data or using
third-party services. Media stays private until a verified publishing adapter
with explicit account permission exists. No synthetic testimonials/results.
"""
from __future__ import annotations
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import time

TOPICS=("site","data","localization")
LANGUAGES=("uk","pl","en")
COPY={
"uk":{
"site":("ВАШ САЙТ.","ЧІТКИЙ ПЛАН.","Статична сторінка для твого проєкту.","Обговоримо обсяг та вимоги."),
"data":("CSV / JSON","БЕЗ ХАОСУ.","Очищення та форматування даних.","Вхідні файли й результат узгоджуємо."),
"localization":("ТЕКСТИ","ТРЬОМА МОВАМИ.","Українська · Polski · English","Вичитка та точні вимоги."),
"cta":"Опиши своє завдання","disclosure":"Оригінальний зразок. Робота з підтримкою ШІ."
},
"pl":{
"site":("TWOJA STRONA.","JASNY PLAN.","Prosta witryna dla Twojego projektu.","Uzgodnijmy zakres i wymagania."),
"data":("CSV / JSON","BEZ CHAOSU.","Porządkowanie danych i plików.","Ustalamy zakres i rezultat."),
"localization":("TEKSTY","W TRZECH JĘZYKACH.","Polski · Українська · English","Weryfikacja i jasne wymagania."),
"cta":"Opisz swoje zadanie","disclosure":"Oryginalny przykład. Praca wspierana przez AI."
},
"en":{
"site":("YOUR WEBSITE.","CLEAR SCOPE.","Simple static pages for your project.","Agree on deliverables first."),
"data":("CSV / JSON","MADE CLEAR.","Clean up and format structured data.","Specific inputs, verifiable outputs."),
"localization":("CONTENT.","THREE LANGUAGES.","English · Polski · Українська","Review and precise requirements."),
"cta":"Describe a small task","disclosure":"Original illustrative material. AI-assisted work."
}}
SIZES={"feed":(1080,1350),"square":(1080,1080),"story":(1080,1920)}
RETAIN_DAYS=21
SITE="gia-2p2.pages.dev"

def schema(c):
    c.execute("""CREATE TABLE IF NOT EXISTS gia_visual_assets(
      day TEXT NOT NULL, format TEXT NOT NULL, language TEXT NOT NULL,
      topic TEXT NOT NULL, path TEXT NOT NULL, sha256 TEXT NOT NULL,
      caption TEXT NOT NULL, state TEXT NOT NULL,
      bytes INTEGER NOT NULL, created REAL NOT NULL,
      PRIMARY KEY(day,format,language)
    )""")
    c.commit()

def _font(sz,bold=True):
    from PIL import ImageFont
    dirs=["/usr/share/fonts/dejavu-sans-fonts","/usr/share/fonts/truetype/dejavu",
          "/usr/share/fonts/dejavu",
          "/usr/share/fonts/truetype/liberation2"]
    names=(["DejaVuSans-Bold.ttf","LiberationSans-Bold.ttf"] if bold
           else ["DejaVuSans.ttf","LiberationSans-Regular.ttf"])
    for folder in dirs:
        for name in names:
            p=Path(folder)/name
            if p.is_file():
                return ImageFont.truetype(str(p),sz)
    return ImageFont.load_default()

def draw_card(day,format,lang,topic):
    from PIL import Image,ImageDraw,ImageFilter
    w,h=SIZES[format]
    a,b,desc,sub=COPY[lang][topic]
    # Deliberately graphic, rather than implying a photorealistic AI photo.
    image=Image.new("RGB",(w,h),(12,18,34))
    d=ImageDraw.Draw(image)
    for y in range(h):
        t=y/max(1,h-1)
        d.line((0,y,w,y),fill=(int(11+14*t),int(20+4*t),int(36+17*t)))
    halo=Image.new("RGBA",(w,h))
    glow=ImageDraw.Draw(halo)
    glow.ellipse((w*.37,-h*.14,w*1.27,h*.50),fill=(30,195,209,116))
    glow.ellipse((-w*.41,h*.30,w*.55,h*.97),fill=(103,83,225,100))
    halo=halo.filter(ImageFilter.GaussianBlur(110))
    image=Image.alpha_composite(image.convert("RGBA"),halo)
    d=ImageDraw.Draw(image)
    margin=77
    d.rounded_rectangle((margin,72,margin+15,136),radius=7,fill=(42,233,215,255))
    d.text((margin+31,75),"GiA  /  DIGITAL SERVICES",
           font=_font(30),fill=(233,244,248,255))
    top=int(h*.31 if format=="story" else h*.28)
    def fitted(message,base_size,bold=True):
        size=base_size
        while size>24:
            font=_font(size,bold)
            if d.textbbox((0,0),message,font=font)[2]<=w-2*margin:
                return font
            size-=2
        return _font(24,bold)
    d.text((margin,top),a,font=fitted(a,68),fill=(255,255,255,255))
    d.text((margin,top+105),b,font=fitted(b,68),fill=(77,229,220,255))
    y=top+243
    for line in (desc,sub):
        if len(line)>43:
            # Avoid overflowing non-Latin languages without external fonts.
            while len(line)>43:
                cut=line.rfind(" ",0,42)
                if cut<8:cut=42
                d.text((margin,y),line[:cut],font=_font(34,False),
                       fill=(224,231,241,255))
                line=line[cut:].strip();y+=54
        d.text((margin,y),line,font=fitted(line,34,False),
               fill=(224,231,241,255))
        y+=62
    footer_y=h-(255 if format=="story" else 222)
    d.rounded_rectangle((margin,footer_y,w-margin,footer_y+94),
         radius=26,fill=(40,211,202,255))
    d.text((margin+24,footer_y+27),COPY[lang]["cta"],
           font=fitted(COPY[lang]["cta"],33),fill=(10,27,41,255))
    d.text((margin,h-105),SITE,font=_font(31),fill=(215,225,240,255))
    # Never imply customer work, certification or guaranteed sales.
    return image.convert("RGB")

def caption(lang,topic):
    a,b,desc,sub=COPY[lang][topic]
    return (a+" "+b+"\n"+desc+" "+sub+"\n"
            +COPY[lang]["disclosure"]+"\nhttps://"+SITE+"/")

def _store_asset(directory,day,fmt,lang,topic):
    from PIL import Image
    folder=Path(directory)/"marketing-media"
    folder.mkdir(parents=True,exist_ok=True,mode=0o700)
    name="gia_"+day+"_"+lang+"_"+topic+"_"+fmt+".jpg"
    target=folder/name
    if target.is_symlink():
        raise ValueError("Refusing symlink media output")
    tmp=folder/(name+".tmp")
    image=draw_card(day,fmt,lang,topic)
    image.save(tmp,format="JPEG",quality=84,optimize=True,progressive=True)
    with Image.open(tmp) as confirmed:
        if confirmed.size!=SIZES[fmt] or confirmed.format!="JPEG":
            raise ValueError("Invalid generated media")
    size=tmp.stat().st_size
    if size>800000:
        tmp.unlink(missing_ok=True)
        raise ValueError("Media exceeds size budget")
    os.chmod(tmp,0o600)
    os.replace(tmp,target)
    digest=hashlib.sha256(target.read_bytes()).hexdigest()
    return target,digest,size

def run_once(ledger,*,now=None):
    if ledger.stopped:return {"state":"stopped"}
    if os.environ.get("GIA_PROMOTION_AGENTS_ENABLED")!="true":
        return {"state":"disabled"}
    if os.environ.get("GIA_VISUAL_GENERATOR_ENABLED","true")=="false":
        return {"state":"disabled"}
    now=time.time() if now is None else now
    day=dt.datetime.fromtimestamp(now,dt.timezone.utc).date()
    daystr=day.isoformat()
    c=ledger.conn
    schema(c)
    language=LANGUAGES[day.toordinal()%len(LANGUAGES)]
    topic=TOPICS[(day.toordinal()//2)%len(TOPICS)]
    created=0
    for fmt in SIZES:
        row=c.execute("""SELECT path,sha256 FROM gia_visual_assets
            WHERE day=? AND format=? AND language=?""",
            (daystr,fmt,language)).fetchone()
        if row and Path(row["path"]).is_file():
            continue
        target,digest,size=_store_asset(ledger.directory,daystr,fmt,language,topic)
        with c:
            c.execute("""INSERT INTO gia_visual_assets
              (day,format,language,topic,path,sha256,caption,state,bytes,created)
              VALUES (?,?,?,?,?,?,?,'ready_private',?,?)
              ON CONFLICT(day,format,language) DO UPDATE SET
              path=excluded.path,sha256=excluded.sha256,
              caption=excluded.caption,state='ready_private',
              bytes=excluded.bytes,created=excluded.created""",
              (daystr,fmt,language,topic,str(target),digest,
               caption(language,topic),size,now))
        created+=1
    cutoff=(day-dt.timedelta(days=RETAIN_DAYS)).isoformat()
    old=c.execute("""SELECT path FROM gia_visual_assets
       WHERE day<? AND state='ready_private'""",(cutoff,)).fetchall()
    with c:
        c.execute("""DELETE FROM gia_visual_assets
                     WHERE day<? AND state='ready_private'""",(cutoff,))
    folder=(Path(ledger.directory)/"marketing-media").resolve()
    for row in old:
        p=Path(row["path"])
        if p.parent.resolve()==folder and not p.is_symlink():
            p.unlink(missing_ok=True)
    count=c.execute("SELECT count(*) FROM gia_visual_assets").fetchone()[0]
    return {"state":"media_ready","generated":created,
            "assets_total":count,"language":language,"topic":topic,
            "public_uploads":0,"instagram_posts":0}
