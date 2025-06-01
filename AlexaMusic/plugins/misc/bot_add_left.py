#
# Copyright (C) 2024-2025 by TheTeamVivek@Github, < https://github.com/TheTeamVivek >.
#
# This file is part of < https://github.com/TheTeamVivek/YukkiMusic > project,
# and is released under the MIT License.
# Please see < https://github.com/TheTeamVivek/YukkiMusic/blob/master/LICENSE >
#
# All rights reserved.
#

from pyrogram import filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
from config import LOG, LOG_GROUP_ID
from AlexaMusic import app
from AlexaMusic.utils.database import delete_served_chat, get_assistant, is_on_off


@app.on_message(filters.new_chat_members | filters.left_chat_member)
async def handle_group_events(_, message: Message):
    try:
        if not await is_on_off(LOG):
            return

        chat = message.chat
        userbot = await get_assistant(chat.id)
        chat_title = chat.title
        chat_id = chat.id
        chat_username = f"@{chat.username}" if chat.username else "ᴘʀɪᴠᴀᴛᴇ ᴄʜᴀᴛ"

        # Bot gruba eklendi
        if message.new_chat_members:
            for member in message.new_chat_members:
                if member.id == app.id:
                    member_count = await app.get_chat_members_count(chat_id)
                    added_by = message.from_user.mention if message.from_user else "Unknown User"
                    added_name = message.from_user.first_name if message.from_user else "Unknown"

                    text = (
                        f"**✅ Music Bot Added to a New Group! #New_Group**\n\n"
                        f"**Chat Name:** {chat_title}\n"
                        f"**Chat ID:** `{chat_id}`\n"
                        f"**Username:** {chat_username}\n"
                        f"**Members:** `{member_count}`\n"
                        f"**Added By:** {added_by}"
                    )

                    await app.send_message(
                        LOG_GROUP_ID,
                        text=text,
                        reply_markup=InlineKeyboardMarkup([
                            [InlineKeyboardButton(f"Added by: {added_name}", user_id=message.from_user.id)]
                        ])
                    )

                    if chat.username:
                        await userbot.join_chat(chat.username)
                    return

        # Bot gruptan atıldı
        if message.left_chat_member and message.left_chat_member.id == app.id:
            removed_by = message.from_user.mention if message.from_user else "Unknown User"
            removed_name = message.from_user.first_name if message.from_user else "Unknown"

            text = (
                f"**❌ Music Bot Removed from a Group! #Left_Group**\n\n"
                f"**Chat Name:** {chat_title}\n"
                f"**Chat ID:** `{chat_id}`\n"
                f"**Username:** {chat_username}\n"
                f"**Removed By:** {removed_by}"
            )

            await app.send_message(
                LOG_GROUP_ID,
                text=text,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton(f"Removed by: {removed_name}", user_id=message.from_user.id)]
                ])
            )

            await delete_served_chat(chat_id)
            await userbot.leave_chat(chat_id)

    except Exception as e:
        # Opsiyonel: hata mesajı loglanabilir
        print(f"[Group Event Error] {e}")