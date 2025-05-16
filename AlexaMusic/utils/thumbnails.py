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

