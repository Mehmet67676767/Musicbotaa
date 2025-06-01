import os
import re
import json
import asyncio
import glob
import random
import logging
from typing import Union

import yt_dlp
import aiohttp # Küçük resimleri indirmek için eklendi
from pyrogram import filters
from pyrogram.enums import ChatAction
from pyrogram.types import (InlineKeyboardButton,
                            InlineKeyboardMarkup, InputMediaAudio,
                            Message)
from youtubesearchpython.__future__ import VideosSearch
# MessageNotModified artık gerekli değil, çünkü CallbackQuery'leri kaldırdık
# from pyrogram.errors.exceptions.bad_request_400 import MessageNotModified

# Kendi yapılandırma dosyanızdan import edin
from config import (BANNED_USERS, SONG_DOWNLOAD_DURATION,
                    SONG_DOWNLOAD_DURATION_LIMIT)
from AlexaMusic import app
# convert_bytes ve song_markup_no_lang artık kullanılmadığı için kaldırıldı.
# from AlexaMusic.utils.formatters import convert_bytes
# from AlexaMusic.utils.inline.song import song_markup_no_lang

# --- LOGLAMA AYARLARI ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- ÇEREZ YÖNETİMİ ---
def get_cookie_file_path() -> str:
    """
    'cookies' klasöründen rastgele bir .txt çerez dosyası seçer.
    """
    cookies_folder = os.path.join(os.getcwd(), "cookies")
    
    if not os.path.isdir(cookies_folder):
        logger.error(f"Çerezler klasörü bulunamadı: {cookies_folder}")
        raise FileNotFoundError(f"Çerezler klasörü bulunamadı: '{cookies_folder}'. Lütfen bu klasörü oluşturun ve içine geçerli çerez dosyaları koyun.")

    txt_files = glob.glob(os.path.join(cookies_folder, '*.txt'))
    if not txt_files:
        logger.error(f"'{cookies_folder}' içinde .txt çerez dosyası bulunamadı.")
        raise FileNotFoundError(f"'{cookies_folder}' içinde .txt çerez dosyası bulunamadı. Lütfen klasöre geçerli çerez dosyası ekleyin.")
    
    chosen_cookie_file = random.choice(txt_files)
    abs_path = os.path.abspath(chosen_cookie_file)
    logger.info(f"Seçilen Çerez Dosyası: {abs_path}")
    return abs_path

# --- YARDIMCI YOUTUBE FONKSİYONLARI ---

async def get_youtube_details(query: str, is_videoid: bool = False) -> tuple:
    """
    Verilen sorgu, YouTube URL'si veya video ID'si için YouTube video detaylarını çeker.
    """
    cookie_path = get_cookie_file_path()
    
    target_link = None 

    if is_videoid:
        # Eğer doğrudan video ID verilmişse, standart YouTube izleme URL'si oluştur
        target_link = f"https://www.youtube.com/watch?v={query}" # ID'den doğrudan link
    elif re.match(r"https?://(?:www\.)?(?:youtube\.com|youtu\.be)/(?:watch\?v=|embed/|v/|)([a-zA-Z0-9_-]{11})(?:\S+)?", query):
        # Eğer sorgu zaten geçerli bir YouTube URL'si ise, olduğu gibi kullan
        target_link = query
    else:
        # Eğer sorgu bir URL veya ID değilse, arama yap
        try:
            results = VideosSearch(query, limit=1)
            search_result = (await results.next())["result"]
            if not search_result:
                raise ValueError("YouTube'da video bulunamadı.")
            target_link = search_result[0]["link"] # Arama sonucundan gelen linki kullan
        except Exception as e:
            logger.error(f"Video araması sırasında hata: {e}")
            raise ValueError("YouTube'da video aranırken bir sorun oluştu.")

    if not target_link:
        raise ValueError("Geçerli bir YouTube URL'si veya arama sorgusu sağlanamadı.")

    ydl_opts = {
        "quiet": True,
        "nocheckcertificate": True,
        "skip_download": True, # Sadece bilgi çek, indirme yapma
        "cookiefile": cookie_path,
        "youtube_include_dash_manifest": False,
        "extractor_args": {'youtube': {'skip': ['dash_manifest']}},
        "log_config": {"enable": True, "level": "DEBUG"}
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # yt-dlp'ye doğrudan geçerli YouTube linkini veriyoruz
            info = ydl.extract_info(target_link, download=False)
            
        title = info.get("title")
        duration_sec = info.get("duration")
        duration_min = f"{duration_sec // 60}:{duration_sec % 60:02d}" if duration_sec is not None else "None"
        thumbnail = info.get("thumbnail")
        vidid = info.get("id") # Bu, yt-dlp'nin kendisinin doğru ID'yi almasını sağlar

        if not all([title, duration_sec is not None, thumbnail, vidid]):
            logger.warning(f"Bazı YouTube detayları eksik: Title={title}, Duration={duration_sec}, Thumbnail={thumbnail}, VidID={vidid}")
            raise ValueError("Video detayları tam olarak alınamadı.")

        return title, duration_min, duration_sec, thumbnail, vidid
    except yt_dlp.utils.DownloadError as e:
        logger.error(f"YouTube detayları çekilirken yt-dlp hatası: {e}")
        if "confirm you’re not a bot" in str(e).lower() or "Sign in" in str(e).lower() or "unavailable videos are hidden" in str(e).lower():
            raise ValueError("YouTube doğrulama istiyor veya video kısıtlı. Lütfen geçerli, güncel çerezler kullandığınızdan emin olun.")
        raise ValueError(f"Video detayları çekilirken bilinmeyen bir hata oluştu: {e}")
    except Exception as e:
        logger.error(f"YouTube detayları çekilirken genel hata: {e}")
        raise ValueError(f"Video detayları çekilirken bir hata oluştu: {e}")


async def download_youtube_file(link: str, mystic_message, title: str = None) -> str:
    """
    Belirtilen YouTube linkinden ses dosyasını indirir.
    Dosya adını temizleyerek ve ID eklemeden kaydeder, ayrıca indirileni bulur ve yeniden adlandırır.
    """
    loop = asyncio.get_running_loop()
    cookie_path = get_cookie_file_path()

    def _download_task():
        downloads_dir = "downloads"
        os.makedirs(downloads_dir, exist_ok=True)

        # Dosya sisteminde güvenli başlık oluşturma
        sanitized_title = re.sub(r'[\\/:*?"<>|]', '', title).strip()
        
        # yt-dlp'nin dosya adına ID eklemesini engellemek için kesin şablon
        initial_output_template = os.path.join(downloads_dir, f"{sanitized_title}.%(ext)s")
        
        ydl_opts = {
            "geo_bypass": True,
            "nocheckcertificate": True,
            "quiet": True, 
            "no_warnings": True,
            "cookiefile": cookie_path,
            "log_config": {"enable": True, "level": "DEBUG"},
            "outtmpl": initial_output_template, 
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                },
                {'key': 'FFmpegMetadata'},
            ],
        }
        
        final_downloaded_file = None 

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(link, download=True)
                
                # --- GÜNCEL VE KESİN DOSYA YOLU TESPİTİ VE YENİDEN ADLANDIRMA MANTIĞI ---
                
                # 1. yt-dlp'nin döndürdüğü 'filepath'i alıyoruz. Bu, gerçek indirilen dosya yoludur.
                actual_downloaded_filepath = info.get('filepath')
                
                if not actual_downloaded_filepath or not os.path.exists(actual_downloaded_filepath):
                    logger.warning(f"YT-DLP 'filepath' döndürmedi veya dosya orada mevcut değil: {actual_downloaded_filepath}. Glob ile arama yapılıyor...")
                    
                    expected_ext_pattern = ".mp3" 
                    
                    search_pattern_strict = os.path.join(downloads_dir, f"{sanitized_title}{expected_ext_pattern}")
                    search_pattern_loose = os.path.join(downloads_dir, f"{sanitized_title}*{expected_ext_pattern}")
                    
                    potential_files = glob.glob(search_pattern_strict)
                    if not potential_files: 
                        potential_files = glob.glob(search_pattern_loose)
                    
                    if potential_files:
                        potential_files.sort(key=os.path.getmtime, reverse=True)
                        actual_downloaded_filepath = potential_files[0]
                        logger.info(f"Glob ile dosya bulundu: {actual_downloaded_filepath}")
                    else:
                        raise ValueError(f"İndirilen dosya yolu hala bulunamadı. Beklenen dosyalar: '{search_pattern_strict}' veya '{search_pattern_loose}'.")
                
                if not actual_downloaded_filepath or not os.path.exists(actual_downloaded_filepath):
                    logger.error(f"Son indirilen dosya yolu belirlenemedi veya dosya mevcut değil: {actual_downloaded_filepath}")
                    raise ValueError(f"İndirilen dosya yolu hala bulunamadı: {sanitized_title}")

                _, original_ext = os.path.splitext(actual_downloaded_filepath)
                
                new_filename = f"{sanitized_title}{original_ext}"
                new_filepath = os.path.join(downloads_dir, new_filename)

                if actual_downloaded_filepath != new_filepath:
                    try:
                        os.rename(actual_downloaded_filepath, new_filepath)
                        logger.info(f"Dosya yeniden adlandırıldı: '{actual_downloaded_filepath}' -> '{new_filepath}'")
                        final_downloaded_file = new_filepath
                    except OSError as e:
                        logger.error(f"Dosya yeniden adlandırılamadı '{actual_downloaded_filepath}' -> '{new_filepath}': {e}")
                        final_downloaded_file = actual_downloaded_filepath
                else:
                    final_downloaded_file = actual_downloaded_filepath
                    logger.info(f"Dosya zaten beklenen temiz isimde: {final_downloaded_file}")

                return final_downloaded_file

        except yt_dlp.utils.DownloadError as e:
            logger.error(f"İndirme sırasında yt-dlp hatası: {e}")
            if "confirm you’re not a bot" in str(e).lower() or "Sign in" in str(e).lower() or "unavailable videos are hidden" in str(e).lower():
                raise ValueError("YouTube doğrulama istiyor veya video kısıtlı. Lütfen geçerli, güncel çerezler kullandığınızdan emin olun.")
            raise ValueError(f"Dosya indirilirken bilinmeyen bir hata oluştu: {e}")
        except Exception as e:
            logger.error(f"İndirme sırasında genel hata: {e}")
            raise ValueError(f"Dosya indirilirken bir hata oluştu: {e}")

    downloaded_file = await loop.run_in_executor(None, _download_task)
    return downloaded_file

async def download_thumbnail_to_local(thumbnail_url: str, video_id: str) -> Union[str, None]:
    """
    Verilen URL'den küçük resmi indirir ve yerel bir dosya yolu döndürür.
    """
    downloads_dir = "downloads"
    os.makedirs(downloads_dir, exist_ok=True)
    thumb_path = os.path.join(downloads_dir, f"thumb_{video_id}.jpg")
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(thumbnail_url) as resp:
                resp.raise_for_status()
                with open(thumb_path, 'wb') as f:
                    while True:
                        chunk = await resp.content.read(1024)
                        if not chunk:
                            break
                        f.write(chunk)
        logger.info(f"Küçük resim yerel olarak indirildi: {thumb_path}")
        return thumb_path
    except aiohttp.ClientError as e:
        logger.error(f"Küçük resim indirilirken HTTP hatası: {e}")
        return None
    except Exception as e:
        logger.error(f"Küçük resim indirilirken genel hata: {e}")
        return None

# --- ANA SCRIPT KODU ---

SONG_COMMAND = ["song", "bul", "indir"]

@app.on_message(
    filters.command(SONG_COMMAND)
    & filters.group
    & ~BANNED_USERS
)
@app.on_message(
    filters.command(SONG_COMMAND)
    & filters.private
    & ~BANNED_USERS
)
async def song_command_handler(client, message: Message):
    await message.delete() # Komut mesajını sil

    url = None
    query = None
    
    # Yanıtlanan mesajda URL arama
    if message.reply_to_message and message.reply_to_message.text:
        url_match = re.search(r"https?://(?:www\.)?(?:youtube\.com|youtu\.be)/(?:watch\?v=|embed/|v/|)([a-zA-Z0-9_-]{11})(?:\S+)?", message.reply_to_message.text)
        if url_match:
            url = url_match.group(0)
    
    # Komut argümanlarında URL veya sorgu arama
    if not url and len(message.command) >= 2:
        query_or_url = message.text.split(None, 1)[1]
        url_match = re.search(r"https?://(?:www\.)?(?:youtube\.com|youtu\.be)/(?:watch\?v=|embed/|v/|)([a-zA-Z0-9_-]{11})(?:\S+)?", query_or_url)
        if url_match:
            url = url_match.group(0)
        else:
            query = query_or_url

    # İlk başta gönderilecek mesajı alıyoruz.
    mystic = await message.reply_text("🔎 İşleniyor...")

    title, duration_min, duration_sec, thumbnail, vidid = (None,)*5 # Başlangıç değerleri atandı

    if url:
        try:
            title, duration_min, duration_sec, thumbnail, vidid = await get_youtube_details(url)
        except ValueError as e:
            await mystic.edit_text(f"Video detayları alınamadı: {e}")
            logger.error(f"URL ile detay çekme hatası: {e}")
            return
        except Exception as e:
            await mystic.edit_text(f"Video detayları alınırken beklenmedik bir hata oluştu: {e}")
            logger.error(f"URL ile beklenmedik detay çekme hatası: {e}")
            return
    else:
        if len(message.command) < 2:
            await mystic.edit_text("Lütfen bir URL veya arama sorgusu girin.")
            return
        if not query: 
            query = message.text.split(None, 1)[1]
        
        try:
            title, duration_min, duration_sec, thumbnail, vidid = await get_youtube_details(query)
        except ValueError as e:
            await mystic.edit_text(f"Video detayları alınamadı: {e}")
            logger.error(f"Sorgu ile detay çekme hatası: {e}")
            return
        except Exception as e:
            await mystic.edit_text(f"Video detayları alınırken beklenmedik bir hata oluştu: {e}")
            logger.error(f"Sorgu ile beklenmedik detay çekme hatası: {e}")
            return
            
    if str(duration_min) == "None" or duration_sec is None:
        await mystic.edit_text("Video süresi bilinmiyor.")
        return
    
    if int(duration_sec) > SONG_DOWNLOAD_DURATION_LIMIT:
        await mystic.edit_text(
            f"Video çok uzun! Sadece {SONG_DOWNLOAD_DURATION} dakikadan kısa videoları indirebilirsiniz. Bu videonun süresi: {duration_min}"
        )
        return
        
    await mystic.edit_text("⏳ İndiriliyor...")

    yturl_to_download = f"https://www.youtube.com/watch?v={vidid}" # Detaylardan alınan ID ile doğru URL'yi oluşturduk
    
    clean_title = re.sub(r"[^\w\s-]", "", title).strip() 
    
    local_thumb_path = None
    # Küçük resim URL'sini yerel bir dosyaya indiriyoruz
    if thumbnail:
        local_thumb_path = await download_thumbnail_to_local(thumbnail, vidid)
        if not local_thumb_path:
            logger.warning(f"YouTube küçük resmi indirilemedi, şarkı küçük resimsiz gönderilecek: {thumbnail}")

    try:
        file_path = await download_youtube_file(
            yturl_to_download, 
            mystic, # mystic mesaj objesi, hata loglama için
            title=clean_title,
        )
    except ValueError as e:
        await mystic.edit_text(f"Dosya indirme hatası: {e}")
        logger.error(f"Dosya indirme hatası: {e}")
        return
    except Exception as e:
        await mystic.edit_text(f"Dosya indirilirken beklenmedik bir hata oluştu: {e}")
        logger.error(f"Beklenmedik dosya indirme hatası: {e}")
        return

    if not file_path or not os.path.exists(file_path):
        await mystic.edit_text("İndirilen dosya bulunamadı veya indirme başarısız oldu. Lütfen tekrar deneyin veya farklı bir video deneyin.")
        logger.error(f"İndirilen dosya yolu geçersiz veya bulunamadı: {file_path}")
        return

    await mystic.edit_text("📤 Yükleniyor...")
    
    res = (
        f"👤 Talep Eden : {message.from_user.mention}\n"
        f"🔮 Başlık : [{title[:23]}]({yturl_to_download})\n" 
        f"⌛️ Süre : `{duration_min}`"
    )

    visit_button = InlineKeyboardButton(
        text="Duyuru",
        url=f"https://t.me/HatiraDuyuru"
    )

    visit_markup = InlineKeyboardMarkup(
        [[visit_button]]
    )
    
    med = InputMediaAudio(
        media=file_path,
        caption=res,
        # thumb olarak yerel dosya yolunu kullanıyoruz
        thumb=local_thumb_path if local_thumb_path and os.path.exists(local_thumb_path) else None, 
        performer="@HatiraMusicBot",
        duration=duration_sec
    )
    
    await app.send_chat_action(
        chat_id=message.chat.id,
        action=ChatAction.UPLOAD_AUDIO,
    )
    
    try:
        await client.edit_message_media(
            chat_id=mystic.chat.id,
            message_id=mystic.id,
            media=med,
            reply_markup=visit_markup
        )
        logger.info(f"Ses başarıyla kullanıcıya gönderildi: {file_path}")
    except Exception as e:
        logger.error(f"Ses medya gönderilirken hata: {e}")
        await mystic.edit_text(f"Ses gönderilirken hata oluştu: {e}")
        return
    
    # --- KANAL ID'SİNİ KENDİ KANALINIZIN ID'Sİ İLE DEĞİŞTİRİN! ---
    channel_id = -1002541546021 
    
    rep = (
        f"👤 Talep Eden : {message.from_user.mention}\n"
        f"🔮 Başlık : [{title[:23]}]({yturl_to_download})\n" 
        f"⌛️ Süre : `{duration_min}`"
    )
    
    try:
        await app.send_audio(
            chat_id=channel_id,
            audio=file_path,
            caption=rep,
            performer="@HatiraMusicBot",
            # thumb olarak yerel dosya yolunu kullanıyoruz
            thumb=local_thumb_path if local_thumb_path and os.path.exists(local_thumb_path) else None, 
            duration=duration_sec
        )
        logger.info(f"Ses başarıyla kanala ({channel_id}) gönderildi.")
    except Exception as e:
        logger.error(f"Kanala ses gönderilirken hata: {e}")

    # İndirilen dosyaları temizle
    if os.path.exists(file_path):
        os.remove(file_path)
        logger.info(f"İndirilen dosya silindi: {file_path}")
    
    # Küçük resim dosyasını temizle (eğer yerel olarak indirildiyse)
    if local_thumb_path and os.path.exists(local_thumb_path):
        os.remove(local_thumb_path)
        logger.info(f"İndirilen küçük resim silindi: {local_thumb_path}")
