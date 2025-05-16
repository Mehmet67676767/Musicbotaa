# █████╗ ██╗     ███████╗██╗  ██╗ █████╗     ███╗   ███╗ █████╗ ██╗  ██╗
# ██╔══██╗██║     ██╔════╝██║ ██╔╝██╔══██╗    ████╗ ████║██╔══██╗██║ ██╔╝
# ███████║██║     █████╗  █████╔╝ ███████║    ██╔████╔██║███████║█████╔╝ 
# ██╔══██║██║     ██╔══╝  ██╔═██╗ ██╔══██║    ██║╚██╔╝██║██╔══██║██╔═██╗ 
# ██║  ██║███████╗███████╗██║  ██╗██║  ██║    ██║ ╚═╝ ██║██║  ██║██║  ██╗
# ╚═╝  ╚═╝╚══════╝╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝    ╚═╝     ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝

# >> ALEXA MUSIC BOT by TheTeamAlexa <<
# Github: https://github.com/TheTeamAlexa
# Youtube: Jankari Ki Duniya
# Telegram: @the_team_kumsal

"""
🔮 TheTeamAlexa Telegram Bots - Power in Simplicity!
📜 License: MIT – Freedom to Innovate
"""

from typing import Union
from pyrogram.types import InlineKeyboardButton
from config import GITHUB_REPO, SUPPORT_CHANNEL, SUPPORT_GROUP, OWNER_ID
from AlexaMusic import app

# ╔═══[ Start Panel Buttons ]══════════════════════════════════════════╗
def start_pannel(_):
    buttons = [
        [
            InlineKeyboardButton(
                text=_["S_B_1"],
                url=f"https://t.me/{app.username}?start=help",
            ),
            InlineKeyboardButton(text=_["S_B_2"], callback_data="settings_helper"),
        ],
    ]
    if SUPPORT_CHANNEL and SUPPORT_GROUP:
        buttons.append(
            [
                InlineKeyboardButton(text=_["S_B_4"], url=f"{SUPPORT_CHANNEL}"),
                InlineKeyboardButton(text=_["S_B_3"], url="https://t.me/the_team_kumsal"),
            ]
        )
    else:
        if SUPPORT_CHANNEL:
            buttons.append([InlineKeyboardButton(text=_["S_B_4"], url=SUPPORT_CHANNEL)])
        if SUPPORT_GROUP:
            buttons.append([InlineKeyboardButton(text=_["S_B_3"], url="https://t.me/the_team_kumsal")])
    return buttons
# ╚═══════════════════════════════════════════════════════════════════╝

# ╔═══[ Private Chat Panel ]══════════════════════════════════════════╗
def private_panel(_, BOT_USERNAME, OWNER: Union[bool, int] = None):
    buttons = [
        [InlineKeyboardButton(text=_["S_B_8"], callback_data="settings_back_helper")]
    ]
    if SUPPORT_CHANNEL and SUPPORT_GROUP:
        buttons.append(
            [
                InlineKeyboardButton(text=_["S_B_4"], url=SUPPORT_CHANNEL),
                InlineKeyboardButton(text=_["S_B_3"], url="https://t.me/the_team_kumsal"),
            ]
        )
    else:
        if SUPPORT_CHANNEL:
            buttons.append([InlineKeyboardButton(text=_["S_B_4"], url=SUPPORT_CHANNEL)])
        if SUPPORT_GROUP:
            buttons.append([InlineKeyboardButton(text=_["S_B_3"], url="https://t.me/the_team_kumsal")])

    buttons.append(
        [InlineKeyboardButton(text=_["S_B_5"], url=f"https://t.me/{BOT_USERNAME}?startgroup=true")]
    )

    if GITHUB_REPO and OWNER_ID:
        buttons.append(
            [
                InlineKeyboardButton(text=_["S_B_7"], user_id=OWNER_ID),
                InlineKeyboardButton(text=_["S_B_6"], url="https://t.me/the_alya_albora"),
            ]
        )
    else:
        if GITHUB_REPO:
            buttons.append([InlineKeyboardButton(text=_["S_B_6"], url="https://t.me/the_zerrin_albora")])
        if OWNER:
            buttons.append([InlineKeyboardButton(text=_["S_B_7"], user_id=OWNER_ID)])
    return buttons
# ╚═══════════════════════════════════════════════════════════════════╝