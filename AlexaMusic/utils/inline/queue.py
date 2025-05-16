from typing import Union
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

def queue_markup(
    _,
    DURATION,
    CPLAY,
    videoid,
    played: Union[bool, int] = None,
    dur: Union[bool, int] = None,
):
    # Süresi bilinmeyen parçalar için basit kontroller
    basic_controls = [
        [
            InlineKeyboardButton(
                text=f"🎶 {_['QU_B_1']}",  # Kuyruğu göster
                callback_data=f"GetQueued {CPLAY}|{videoid}",
            ),
            InlineKeyboardButton(
                text="❌ Kapat",  # Menü kapat
                callback_data="close",
            ),
        ]
    ]

    # Süresi bilinen parçalar için gelişmiş kontroller
    advanced_controls = [
        [
            InlineKeyboardButton(
                text=f"⏱️ {_['QU_B_2'].format(played, dur)}",  # Oynatma süresi
                callback_data="GetTimer",
            )
        ],
        basic_controls[0],  # Temel kontrolleri de ekle
    ]

    return InlineKeyboardMarkup(basic_controls if DURATION == "Unknown" else advanced_controls)


def queue_back_markup(_, CPLAY):
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    text="⬅️ Geri",  # Geri butonu
                    callback_data=f"queue_back_timer {CPLAY}",
                ),
                InlineKeyboardButton(
                    text="❌ Kapat",  # Menü kapat
                    callback_data="close",
                ),
            ]
        ]
    )
