import os
import re
import json
import asyncio
import glob
import random
import logging
import time 
import shutil # shutil modülünü ekledik
from typing import Union

import yt_dlp
from pykeyboard import InlineKeyboard
from pyrogram import filters
from pyrogram.enums import ChatAction
from pyrogram.types import (InlineKeyboardButton,
                            InlineKeyboardMarkup, InputMediaAudio,
                            InputMediaVideo, Message)
from youtubesearchpython.__future__ import VideosSearch
from pyrogram.errors.exceptions.bad_request_400 import MessageNotModified

# Kendi yapılandırma dosyanızdan import edin
from config import (BANNED_USERS, SONG_DOWNLOAD_DURATION,
                    SONG_DOWNLOAD_DURATION_LIMIT)
from ArchMusic import app
from ArchMusic.utils.formatters import convert_bytes
from ArchMusic.utils.inline.song import song_markup_no_lang

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
        target_link = f"https://www.youtube.com/watch?v={query}" 
    elif re.match(r"https?://(?:www\.)?(?:youtube\.com|youtu\.be)/(?:watch\?v=|embed/|v/|)([a-zA-Z0-9_-]{11})(?:\S+)?", query):
        target_link = query
    else:
        try:
            results = VideosSearch(query, limit=1)
            search_result = (await results.next())["result"]
            if not search_result:
                raise ValueError("YouTube'da video bulunamadı.")
            target_link = search_result[0]["link"] 
        except Exception as e:
            logger.error(f"Video araması sırasında hata: {e}")
            raise ValueError("YouTube'da video aranırken bir sorun oluştu.")

    if not target_link:
        raise ValueError("Geçerli bir YouTube URL'si veya arama sorgusu sağlanamadı.")

    ydl_opts = {
        "quiet": True,
        "nocheckcertificate": True,
        "skip_download": True, 
        "cookiefile": cookie_path,
        "youtube_include_dash_manifest": False,
        "extractor_args": {'youtube': {'skip': ['dash_manifest']}},
        "log_config": {"enable": True, "level": "DEBUG"}
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(target_link, download=False)
            
        title = info.get("title")
        duration_sec = info.get("duration")
        duration_min = f"{duration_sec // 60}:{duration_sec % 60:02d}" if duration_sec is not None else "None"
        thumbnail = info.get("thumbnail")
        vidid = info.get("id") 

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


async def download_youtube_file(link: str, mystic_message, songaudio: bool = False, songvideo: bool = False, format_id: str = None, title: str = None, vidid: str = None) -> str:
    """
    Belirtilen YouTube linkinden ses veya video dosyasını indirir.
    Dosya adını yt-dlp'nin belirlediği bir geçici klasöre indirir, ardından yeniden adlandırır ve taşır.
    """
    loop = asyncio.get_running_loop()
    cookie_path = get_cookie_file_path()

    def _download_task():
        base_downloads_dir = "downloads"
        os.makedirs(base_downloads_dir, exist_ok=True)

        # İndirme için benzersiz bir geçici klasör oluştur
        temp_download_dir = os.path.join(base_downloads_dir, f"temp_{vidid}_{int(time.time())}")
        os.makedirs(temp_download_dir, exist_ok=True)
        logger.info(f"Geçici indirme klasörü oluşturuldu: {temp_download_dir}")

        # Dosya sisteminde güvenli başlık oluşturma (yeniden adlandırma için)
        sanitized_title = re.sub(r'[\\/:*?"<>|]', '', title).strip()
        
        # Beklenen nihai dosya uzantısını belirle (yeniden adlandırma için)
        expected_target_ext = ".mp3" if songaudio else ".mp4" 
        
        # yt-dlp seçenekleri
        ydl_opts = {
            "geo_bypass": True,
            "nocheckcertificate": True,
            "quiet": True, 
            "no_warnings": True,
            "cookiefile": cookie_path,
            "log_config": {"enable": True, "level": "DEBUG"},
            "paths": {"home": temp_download_dir}, # İndirmeleri geçici klasöre yönlendir
            "postprocessors": [], 
            "retries": 5, # Ağ hataları için yeniden denemeler
            "fragment_retries": 5,
        }

        if songaudio:
            ydl_opts.update({
                "format": format_id or "bestaudio/best",
                "postprocessors": [
                    {
                        "key": "FFmpegExtractAudio",
                        "preferredcodec": "mp3",
                        "preferredquality": "192",
                    },
                    {'key': 'FFmpegMetadata'},
                ],
            })
        elif songvideo:
            ydl_opts.update({
                "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]", 
                "merge_output_format": "mp4", 
                "postprocessors": [
                    {
                        "key": "FFmpegVideoConvertor",
                        "preferedformat": "mp4"
                    },
                    {
                        "key": "FFmpegMerger"
                    },
                    {'key': 'FFmpegMetadata'},
                ],
                "postprocessor_args": {
                    "Merger": [
                        "-loglevel", "error",
                        "-hide_banner",
                        "-map", "0:v", "-map", "0:a?",
                        "-c:v", "copy",
                        "-c:a", "aac"
                    ]
                }
            })
        
        found_filepath_in_temp_dir = None 

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                logger.info(f"yt-dlp indirme başlatılıyor: {link} into {temp_download_dir}")
                info = ydl.extract_info(link, download=True)
                logger.info(f"yt-dlp indirme tamamlandı.")
                
                # yt-dlp'nin döndürdüğü 'filepath'i kontrol et
                # Bu yol temp_download_dir içinde olmalı
                if 'filepath' in info and os.path.exists(info['filepath']) and \
                   os.path.dirname(info['filepath']) == temp_download_dir:
                    found_filepath_in_temp_dir = info['filepath']
                    logger.info(f"YT-DLP tarafından bildirilen dosya yolu: {found_filepath_in_temp_dir}")
                else:
                    logger.warning(f"YT-DLP 'filepath' bilgisi eksik, geçersiz veya geçici klasörde değil. Manuel dosya arama denemesi yapılacak.")
                    
                    # Eğer yt-dlp'den geçerli bir yol alınamadıysa, geçici klasör içinde arama yap
                    max_retries = 20 # Deneme sayısını biraz artırdık
                    retry_delay = 1.0 # Her deneme arası bekleme süresini artırdık
                    
                    for attempt in range(max_retries):
                        # Geçici klasördeki tüm .mp4 veya .mp3 dosyalarını ara
                        search_pattern = os.path.join(temp_download_dir, f"*.{expected_target_ext}")
                        potential_files = glob.glob(search_pattern)
                        
                        if potential_files:
                            # En yeni ve en büyük dosyayı seç (nihai çıktı olma ihtimali yüksek)
                            potential_files.sort(key=lambda f: os.path.getmtime(f) + os.path.getsize(f), reverse=True)
                            
                            # ID'li geçici dosyaları hala arıyoruz, bu sefer filtrelemiyoruz.
                            # Çünkü yt-dlp'nin son bıraktığı ne ise onu alacağız.
                            # Buradaki amacımız sadece "dosya var mı" ve "hangisi" kontrolü.
                            # Yeniden adlandırma adımında ID'yi temizleyeceğiz.
                            
                            found_filepath_in_temp_dir = potential_files[0]
                            logger.info(f"Deneme {attempt+1}: Geçici klasörde dosya bulundu: {found_filepath_in_temp_dir}")
                            break # Dosya bulundu, döngüden çık
                        
                        logger.debug(f"Deneme {attempt+1}: Geçici klasörde dosya henüz bulunamadı. {retry_delay} saniye bekleniyor...")
                        time.sleep(retry_delay)
                        
                    if not found_filepath_in_temp_dir or not os.path.exists(found_filepath_in_temp_dir):
                        logger.error(f"Maksimum deneme {max_retries} sonrası geçici klasörde dosyaya hala ulaşılamadı. Aranan desen: {search_pattern}")
                        raise ValueError(f"İndirilen dosya geçici klasörde bulunamadı: '{temp_download_dir}'")

            # Buraya kadar, yt-dlp'nin indirdiği veya bulduğumuz, geçici klasördeki gerçek dosya yolu elimizde.
            # Şimdi bu dosyayı BASE downloads klasörüne taşıyacak ve temizlenmiş isimle yeniden adlandıracağız.
            
            # Yeni, temiz dosya adı ve yolu (ana downloads klasöründe)
            new_filename = f"{sanitized_title}{expected_target_ext}"
            final_target_filepath = os.path.join(base_downloads_dir, new_filename)

            # Eğer hedef dosya zaten varsa (önceki bir denemeden kalmış olabilir), sil.
            if os.path.exists(final_target_filepath):
                os.remove(final_target_filepath)
                logger.info(f"Mevcut hedef dosya silindi (yeniden adlandırma öncesi): {final_target_filepath}")

            try:
                # Dosyayı geçici klasörden ana downloads klasörüne taşı ve yeniden adlandır
                shutil.move(found_filepath_in_temp_dir, final_target_filepath)
                logger.info(f"Dosya taşındı ve yeniden adlandırıldı: '{found_filepath_in_temp_dir}' -> '{final_target_filepath}'")
            except OSError as e:
                logger.error(f"Dosya taşıma veya yeniden adlandırma hatası '{found_filepath_in_temp_dir}' -> '{final_target_filepath}': {e}")
                raise ValueError(f"Dosya taşıma/yeniden adlandırma başarısız: {e}")
            
            # Nihai dosyanın varlığını teyit et
            if not os.path.exists(final_target_filepath):
                logger.error(f"Nihai dosya belirlendi ancak mevcut değil: {final_target_filepath}")
                raise ValueError(f"İndirilen dosya diske kaydedilemedi veya yeniden adlandırma sonrası bulunamadı: {final_target_filepath}")

            return final_target_filepath

        except yt_dlp.utils.DownloadError as e:
            logger.error(f"İndirme sırasında yt-dlp hatası: {e}")
            if "confirm you’re not a bot" in str(e).lower() or "Sign in" in str(e).lower() or "unavailable videos are hidden" in str(e).lower():
                raise ValueError("YouTube doğrulama istiyor veya video kısıtlı. Lütfen geçerli, güncel çerezler kullandığınızdan emin olun.")
            raise ValueError(f"Dosya indirilirken bilinmeyen bir hata oluştu: {e}")
        except Exception as e:
            logger.error(f"İndirme sırasında genel hata: {e}")
            raise ValueError(f"Dosya indirilirken bir hata oluştu: {e}")
        finally:
            # İşlem bitince geçici klasörü ve içindeki her şeyi sil
            if os.path.exists(temp_download_dir):
                try:
                    shutil.rmtree(temp_download_dir)
                    logger.info(f"Geçici indirme klasörü silindi: {temp_download_dir}")
                except OSError as e:
                    logger.error(f"Geçici klasör silinirken hata: {temp_download_dir}: {e}")

    downloaded_file = await loop.run_in_executor(None, _download_task)
    return downloaded_file

# --- ANA SCRIPT KODU (download_youtube_file çağrısını güncelledik) ---

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
    await message.delete() 

    url = None
    query = None
    
    if message.reply_to_message and message.reply_to_message.text:
        url_match = re.search(r"https?://(?:www\.)?(?:youtube\.com|youtu\.be)/(?:watch\?v=|embed/|v/|)([a-zA-Z0-9_-]{11})(?:\S+)?", message.reply_to_message.text)
        if url_match:
            url = url_match.group(0)
    
    if not url and len(message.command) >= 2:
        query_or_url = message.text.split(None, 1)[1]
        url_match = re.search(r"https?://(?:www\.)?(?:youtube\.com|youtu\.be)/(?:watch\?v=|embed/|v/|)([a-zA-Z0-9_-]{11})(?:\S+)?", query_or_url)
        if url_match:
            url = url_match.group(0)
        else:
            query = query_or_url

    mystic = await message.reply_text("🔎 İşleniyor...")

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
        return await mystic.edit_text("Video süresi bilinmiyor.")
    
    if int(duration_sec) > SONG_DOWNLOAD_DURATION_LIMIT:
        return await mystic.edit_text(
            f"Video çok uzun! Sadece {SONG_DOWNLOAD_DURATION} dakikadan kısa videoları indirebilirsiniz. Bu videonun süresi: {duration_min}"
        )
        
    buttons = song_markup_no_lang(vidid)
    await mystic.delete()
    return await message.reply_photo(
        thumbnail,
        caption=f"🎵 **Başlık:** {title}\n\nLütfen bir indirme türü seçin:",
        reply_markup=InlineKeyboardMarkup(buttons),
    )

@app.on_callback_query(
    filters.regex(pattern=r"song_back") & ~BANNED_USERS
)
async def songs_back_helper(client, CallbackQuery):
    callback_data = CallbackQuery.data.strip()
    callback_request = callback_data.split(None, 1)[1]
    stype, vidid = callback_request.split("|")
    buttons = song_markup_no_lang(vidid)
    
    try:
        return await CallbackQuery.edit_message_reply_markup(
            reply_markup=InlineKeyboardMarkup(buttons)
        )
    except MessageNotModified:
        logger.info("Klavye zaten aynıydı, 'song_back' için düzenleme yapılmadı.")
        pass

@app.on_callback_query(
    filters.regex(pattern=r"song_helper") & ~BANNED_USERS
)
async def song_helper_cb(client, CallbackQuery):
    callback_data = CallbackQuery.data.strip()
    callback_request = callback_data.split(None, 1)[1]
    stype, vidid = callback_request.split("|")
    try:
        await CallbackQuery.answer("Formatlar yükleniyor...", show_alert=True)
    except:
        pass
    
    yturl_for_details = f"https://www.youtube.com/watch?v={vidid}"

    keyboard = InlineKeyboard()
    
    if stype == "audio":
        keyboard.row(
            InlineKeyboardButton(
                text="🎵 Yüksek Kalite MP3",
                callback_data=f"song_download {stype}|bestaudio|{vidid}",
            ),
        )
    else: 
        keyboard.row(
            InlineKeyboardButton(
                text="🎬 En İyi Kalite Video (MP4)",
                callback_data=f"song_download {stype}|bestvideo|{vidid}",
            )
        )
        
    keyboard.row(
        InlineKeyboardButton(
            text="⬅️ Geri",
            callback_data=f"song_back {stype}|{vidid}",
        ),
        InlineKeyboardButton(
            text="✖️ Kapat", callback_data=f"close"
        ),
    )
    
    try:
        return await CallbackQuery.edit_message_reply_markup(
            reply_markup=keyboard
        )
    except MessageNotModified:
        logger.info("Klavye zaten aynıydı, 'song_helper' için düzenleme yapılmadı.")
        pass

@app.on_callback_query(
    filters.regex(pattern=r"song_download") & ~BANNED_USERS
)
async def song_download_cb(client, CallbackQuery):
    try:
        await CallbackQuery.answer("İndirme başlatılıyor...", show_alert=False)
    except:
        pass
    
    callback_data = CallbackQuery.data.strip()
    callback_request = callback_data.split(None, 1)[1]
    stype, format_id, vidid = callback_request.split("|")
    mystic = await CallbackQuery.edit_message_text("⏳ İndiriliyor...")

    yturl_to_download = f"https://www.youtube.com/watch?v={vidid}"
    
    try:
        title, duration_min, duration_sec, thumbnail, _ = await get_youtube_details(vidid, is_videoid=True)
    except ValueError as e:
        await mystic.edit_text(f"Video detayları alınamadı: {e}")
        logger.error(f"İndirme öncesi detaylar alınamadı: {e}")
        return
    except Exception as e:
        await mystic.edit_text(f"Video detayları alınırken beklenmedik bir hata oluştu: {e}")
        logger.error(f"İndirme öncesi beklenmedik detay çekme hatası: {e}")
        return

    clean_title = re.sub(r"[^\w\s-]", "", title).strip() 
    
    thumb_image_path = None
    if CallbackQuery.message.photo:
        try:
            thumb_image_path = await client.download_media(CallbackQuery.message.photo.file_id, file_name=f"downloads/thumb_{vidid}.jpg")
            logger.info(f"Küçük resim indirildi: {thumb_image_path}")
        except Exception as e:
            logger.warning(f"Küçük resim indirilemedi, URL kullanılacak: {e}")
            thumb_image_path = thumbnail 
    elif thumbnail: 
        thumb_image_path = thumbnail
        
    try:
        # download_youtube_file çağrısına 'vidid' parametresini ekledik
        file_path = await download_youtube_file(
            yturl_to_download,
            mystic,
            songvideo=(stype == "video"),
            songaudio=(stype == "audio"),
            format_id=format_id,
            title=clean_title,
            vidid=vidid, # Buraya vidid'yi ekledik
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
    
    if stype == "video":
        width = CallbackQuery.message.photo.width if CallbackQuery.message.photo else 1280 
        height = CallbackQuery.message.photo.height if CallbackQuery.message.photo else 720 
        
        med = InputMediaVideo(
            media=file_path, 
            duration=duration_sec,
            width=width,
            height=height,
            thumb=thumb_image_path,
            caption=title,
            supports_streaming=True,
        )
        
        await app.send_chat_action(
            chat_id=CallbackQuery.message.chat.id,
            action=ChatAction.UPLOAD_VIDEO,
        )
        
        try:
            await CallbackQuery.edit_message_media(media=med)
            logger.info(f"Video başarıyla kullanıcıya gönderildi: {file_path}")
        except Exception as e:
            logger.error(f"Video medya gönderilirken hata: {e}")
            await mystic.edit_text(f"Video gönderilirken hata oluştu: {e}")
            return
        
    elif stype == "audio":
        res = (
            f"👤 Talep Eden : {CallbackQuery.from_user.mention}\n"
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
            thumb=thumb_image_path,
            performer="@HatiraMusicBot",
            duration=duration_sec
        )
        
        await app.send_chat_action(
            chat_id=CallbackQuery.message.chat.id,
            action=ChatAction.UPLOAD_AUDIO,
        )
        
        try:
            await CallbackQuery.edit_message_media(media=med, reply_markup=visit_markup)
            logger.info(f"Ses başarıyla kullanıcıya gönderildi: {file_path}")
        except Exception as e:
            logger.error(f"Ses medya gönderilirken hata: {e}")
            await mystic.edit_text(f"Ses gönderilirken hata oluştu: {e}")
            return
        
        channel_id = -1002260799344 
        
        rep = (
            f"👤 Talep Eden : {CallbackQuery.from_user.mention}\n"
            f"🔮 Başlık : [{title[:23]}]({yturl_to_download})\n" 
            f"⌛️ Süre : `{duration_min}`"
        )
        
        try:
            await app.send_audio(
                chat_id=channel_id,
                audio=file_path, 
                caption=rep,
                performer="@HatiraMusicBot",
                thumb=thumb_image_path,
                duration=duration_sec
            )
            logger.info(f"Ses başarıyla kanala ({channel_id}) gönderildi.")
        except Exception as e:
            logger.error(f"Kanala ses gönderilirken hata: {e}")

    # İndirilen dosyaları temizle (artık sadece ana klasördeki nihai dosyayı siliyoruz)
    if os.path.exists(file_path):
        os.remove(file_path)
        logger.info(f"Nihai indirilen dosya silindi: {file_path}")
    
    if thumb_image_path and os.path.exists(thumb_image_path) and "thumb_" in os.path.basename(thumb_image_path):
        os.remove(thumb_image_path)
        logger.info(f"İndirilen küçük resim silindi: {thumb_image_path}")

