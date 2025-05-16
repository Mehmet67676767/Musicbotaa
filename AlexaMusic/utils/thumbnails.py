import os import re import textwrap

import aiofiles import aiohttp

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont, ImageOps from youtubesearchpython.future import VideosSearch

from config import YOUTUBE_IMG_URL

def change_image_size(max_width, max_height, image): ratio = min(max_width / image.width, max_height / image.height) new_size = (int(image.width * ratio), int(image.height * ratio)) return image.resize(new_size, Image.LANCZOS)

async def generate_thumbnail(videoid, status_text="YAYIN BAŞLADI", bot_name="Alya Music Bot"): cache_path = f"cache/{videoid}.png" if os.path.isfile(cache_path): return cache_path

url = f"https://www.youtube.com/watch?v={videoid}"

try:
    results = VideosSearch(url, limit=1)
    result = (await results.next())["result"][0]

    title = re.sub(r"\W+", " ", result.get("title", "Unsupported Title")).title()
    duration = result.get("duration", "Unknown")
    views = result.get("viewCount", {}).get("short", "Unknown")
    thumbnail_url = result["thumbnails"][0]["url"].split("?")[0]

    async with aiohttp.ClientSession() as session:
        async with session.get(thumbnail_url) as resp:
            if resp.status == 200:
                async with aiofiles.open(f"cache/thumb{videoid}.png", mode="wb") as f:
                    await f.write(await resp.read())

    youtube_img = Image.open(f"cache/thumb{videoid}.png")
    base_img = change_image_size(1280, 720, youtube_img).convert("RGBA")

    # Arka plan bulanık + karanlık
    blurred_bg = base_img.filter(ImageFilter.GaussianBlur(20))
    enhancer = ImageEnhance.Brightness(blurred_bg)
    background = enhancer.enhance(0.5)

    # Logo
    center_crop = youtube_img.crop((
        youtube_img.width / 2 - 250,
        youtube_img.height / 2 - 250,
        youtube_img.width / 2 + 250,
        youtube_img.height / 2 + 250,
    ))
    center_crop.thumbnail((480, 480), Image.LANCZOS)
    logo = ImageOps.expand(center_crop, border=10, fill=(255, 255, 255))
    background.paste(logo, (70, 120))

    # Yazı ayarları
    draw = ImageDraw.Draw(background)
    font_title = ImageFont.truetype("assets/font2.ttf", 42)
    font_status = ImageFont.truetype("assets/font2.ttf", 72)
    font_info = ImageFont.truetype("assets/font2.ttf", 30)
    font_bot = ImageFont.truetype("assets/font.ttf", 28)

    # Bot adı (sol üst)
    draw.text((30, 20), bot_name, font=font_bot, fill=(0, 255, 255))

    # Durum yazısı (ortada)
    draw.text((650, 140), status_text.upper(), font=font_status, fill="white", stroke_width=3, stroke_fill="black")

    # Başlık yazısı (orta alt)
    lines = textwrap.wrap(title, width=30)
    for i, line in enumerate(lines[:2]):
        y_pos = 280 + i * 60
        w, _ = draw.textsize(line, font=font_title)
        draw.text(((1280 - w) // 2 + 100, y_pos), line, font=font_title, fill="white", stroke_width=2, stroke_fill="black")

    # Bilgiler (ikon gibi)
    draw.text((650, 440), f"👁️  Görüntüleme: {views}", font=font_info, fill="white")
    draw.text((650, 490), f"⏱️  Süre: {duration}", font=font_info, fill="white")
    draw.text((650, 540), f"✪  Sahibi: Alya Albora", font=font_info, fill="white")

    try:
        os.remove(f"cache/thumb{videoid}.png")
    except Exception:
        pass

    background.save(cache_path)
    return cache_path

except Exception as e:
    print(f"Hata oluştu: {e}")
    return YOUTUBE_IMG_URL




async def gen_qthumb(videoid):
    if os.path.isfile(f"cache/{videoid}.png"):
        return f"cache/{videoid}.png"

    url = f"https://www.youtube.com/watch?v={videoid}"
    try:
        results = VideosSearch(url, limit=1)
        for result in (await results.next())["result"]:
            try:
                title = result["title"]
                title = re.sub(r"\W+", " ", title)
                title = title.title()
            except:
                title = "Unsupported Title"
            try:
                duration = result["duration"]
            except:
                duration = "Unknown Mins"
            thumbnail = result["thumbnails"][0]["url"].split("?")[0]
            try:
                views = result["viewCount"]["short"]
            except:
                views = "Unknown Views"
            try:
                channel = result["channel"]["name"]
            except:
                channel = "Unknown Channel"

        async with aiohttp.ClientSession() as session:
            async with session.get(thumbnail) as resp:
                if resp.status == 200:
                    f = await aiofiles.open(f"cache/thumb{videoid}.png", mode="wb")
                    await f.write(await resp.read())
                    await f.close()

        youtube = Image.open(f"cache/thumb{videoid}.png")
        image1 = changeImageSize(1280, 720, youtube)
        image2 = image1.convert("RGBA")
        background = image2.filter(filter=ImageFilter.GaussianBlur(15))
        enhancer = ImageEnhance.Brightness(background)
        background = enhancer.enhance(0.6)
        Xcenter = youtube.width / 2
        Ycenter = youtube.height / 2
        x1 = Xcenter - 250
        y1 = Ycenter - 250
        x2 = Xcenter + 250
        y2 = Ycenter + 250
        logo = youtube.crop((x1, y1, x2, y2))
        logo.thumbnail((520, 520), Image.LANCZOS)
        logo = ImageOps.expand(logo, border=15, fill="white")
        background.paste(logo, (50, 100))
        draw = ImageDraw.Draw(background)
        font = ImageFont.truetype("assets/font2.ttf", 40)
        font2 = ImageFont.truetype("assets/font2.ttf", 70)
        arial = ImageFont.truetype("assets/font2.ttf", 30)
        name_font = ImageFont.truetype("assets/font.ttf", 30)
        para = textwrap.wrap(title, width=30)
        j = 0
        draw.text((5, 5), f"Alexa MusicBot", fill="white", font=name_font)
        draw.text(
            (600, 150),
            "sıraya eklendi",
            fill="white",
            stroke_width=3,
            stroke_fill="black",
            font=font2,
        )
        for line in para:
            if j == 1:
                j += 1
                draw.text(
                    (600, 340),
                    f"{line}",
                    fill="white",
                    stroke_width=1,
                    stroke_fill="black",
                    font=font,
                )
            if j == 0:
                j += 1
                draw.text(
                    (600, 280),
                    f"{line}",
                    fill="white",
                    stroke_width=1,
                    stroke_fill="black",
                    font=font,
                )
        draw.text(
            (600, 450),
            f"görüntüleme: {views[:23]}",
            (255, 255, 255),
            font=arial,
        )
        draw.text(
            (600, 500),
            f"Dakika : {duration[:23]} Mins",
            (255, 255, 255),
            font=arial,
        )
        draw.text(
            (600, 550),
            f"sahibi : Alya albora",
            (255, 255, 255),
            font=arial,
        )
        try:
            os.remove(f"cache/thumb{videoid}.png")
        except:
            pass
        background.save(f"cache/{videoid}.png")
        return f"cache/{videoid}.png"
    except Exception:
        return YOUTUBE_IMG_URL