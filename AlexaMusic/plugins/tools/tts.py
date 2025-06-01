import io
from gtts import gTTS
from pyrogram import filters
from YukkiMusic import app


@app.on_message(filters.command("tts"))
async def text_to_speech(client, message):
    if len(message.command) < 2:
        return await message.reply_text(
            "Lütfen sese çevirmek için bir metin girin."
        )

    text = message.text.split(None, 1)[1]

    # Çok uzun metin olursa sınırla (örneğin 200 karakter)
    if len(text) > 200:
        return await message.reply_text("Lütfen 200 karakterden kısa bir metin girin.")

    # Kullanıcıya işlem mesajı gönderelim
    processing_msg = await message.reply_text("Metin sese dönüştürülüyor, lütfen bekleyin...")

    try:
        tts = gTTS(text, lang="tr")
        audio_data = io.BytesIO()
        tts.write_to_fp(audio_data)
        audio_data.seek(0)

        audio_file = io.BytesIO(audio_data.read())
        audio_file.name = "ses.mp3"

        await message.reply_audio(audio_file)
    except Exception as e:
        await message.reply_text(f"Bir hata oluştu: {e}")
    finally:
        await processing_msg.delete()


__HELP__ = """
**Metni sese dönüştürme komutu**

`/tts <metin>` komutunu kullanarak yazdığınız metni Türkçe sese çevirebilirsiniz.

**Örnek:**
- `/tts Merhaba, nasılsınız?`

**Not:**
Lütfen komuttan sonra seslendirilmesini istediğiniz metni yazınız. Maksimum 200 karakter olabilir.
"""

__MODULE__ = "Metni Sese Çevir"
