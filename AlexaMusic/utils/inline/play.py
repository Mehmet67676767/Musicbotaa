
# Copyright (C) 2025 by Alexa_Help @ Github, < https://github.com/TheTeamAlexa >
# Subscribe On YT < Jankari Ki Duniya >. All rights reserved. © Alexa © Yukki.

from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import SUPPORT_GROUP, SUPPORT_CHANNEL
import random

# Ultra havalı bar stilleri
bars = [
    "⣿⣷⣯⣟⡿⢿⠿⠻⠋", "⠋⠻⠿⠿⠿⢿⡿⣟⣯⣷⣿", "▓▒░░▒▓█", "▁▃▅▇▆▇▅▃▁", "█▓▒░▒▓█", "◉—◉—◉"
]

selections = [
    "✦◉◉◉▣◉◉◉✦", "☰☲☱▤▥▧▦▩", "✶✸✹✺✻✼✽✾✿❀", "▣▤▥▦▧▨▩◈◉◍◎", "☀☁☂☃★☆✪✫", "⚡⚙⚔⚒⚠⚜", "◉▣▤▥▦▧▨▩◈"
]

def stream_markup_timer(_, videoid, chat_id, played, dur):
    bar = random.choice(bars)
    buttons = [
        [
            InlineKeyboardButton(
                text="🚀 Kumsal Music Galaxy 🚀",
                url="https://t.me/the_team_kumsal"
            )
        ],
        [
            InlineKeyboardButton(
                text=f"{played} ⏳ {bar} ⏳ {dur}",
                callback_data="GetTimer"
            )
        ],
        [
            InlineKeyboardButton("▶️ Devam Et", callback_data=f"ADMIN Resume|{chat_id}"),
            InlineKeyboardButton("⏸ Dondur", callback_data=f"ADMIN Pause|{chat_id}"),
            InlineKeyboardButton("⏭ Atla", callback_data=f"ADMIN Skip|{chat_id}"),
            InlineKeyboardButton("⏹ Bitir", callback_data=f"ADMIN Stop|{chat_id}"),
        ],
        [
            InlineKeyboardButton("➕ Listeye Ekle", callback_data=f"add_playlist {videoid}"),
            InlineKeyboardButton("⚙ Kontrol Paneli", callback_data=f"PanelMarkup {videoid}|{chat_id}"),
        ],
    ]
    return buttons

def telegram_markup_timer(_, videoid, chat_id, played, dur):
    bar = random.choice(selections)
    buttons = [
        [
            InlineKeyboardButton(text="❌ Kapat", callback_data="close"),
            InlineKeyboardButton(
                text=f"{played} ✧{bar}✧ {dur}",
                callback_data="GetTimer",
            )
        ],
        [
            InlineKeyboardButton(
                text="➕ Listeye Ekle",
                callback_data=f"add_playlist {videoid}",
            ),
            InlineKeyboardButton(text="👑 Sahip", url="https://t.me/Jankari_Ki_Duniya"),
        ],
        [
            InlineKeyboardButton(
                text="⚙ Ayarlar",
                callback_data=f"PanelMarkup None|{chat_id}",
            ),
            InlineKeyboardButton(text="💬 Yardım Grubu", url=SUPPORT_GROUP),
        ],
    ]
    return buttons
