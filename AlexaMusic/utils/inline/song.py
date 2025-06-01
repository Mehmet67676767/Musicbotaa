from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

# Diğer inline markup fonksiyonlarınız varsa buraya eklenebilir

def song_markup_no_lang(videoid: str):
    buttons = [
        [
            InlineKeyboardButton(
                text="🎵 Sadece Ses",
                callback_data=f"song_helper audio|{videoid}",
            ),
            InlineKeyboardButton(
                text="🎬 Sadece Video",
                callback_data=f"song_helper video|{videoid}",
            ),
        ],
        [
            InlineKeyboardButton(
                text="✖️ Kapat", callback_data="close"
            ),
        ],
    ]
    return buttons # InlineKeyboardMarkup değil, sadece butonların listesini döndürmesi bekleniyor
