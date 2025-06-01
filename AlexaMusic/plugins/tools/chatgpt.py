from config import BANNED_USERS
from g4f.client import AsyncClient
from pyrogram import filters
from pyrogram.enums import ParseMode
from AlexaMusic import app

client = AsyncClient()

@app.on_message(filters.command(["ai", "chatgpt", "ask", "gpt4"]) & ~BANNED_USERS)
async def chatgpt_chat(bot, message):
    # Eğer komut tek başına yazılmışsa ve mesaj yanıtı yoksa örnek mesaj gönder
    if len(message.command) < 2 and not message.reply_to_message:
        await message.reply_text(
            "Örnek:\n\n`/ai basit bir web sitesi kodu yaz html css, js kullanarak?`"
        )
        return

    # Eğer mesaj bir mesaja yanıt olarak gelmişse, yanıtın içeriğini al
    if message.reply_to_message and message.reply_to_message.text:
        user_input = message.reply_to_message.text
    else:
        # Değilse komutun geri kalanını birleştir
        user_input = " ".join(message.command[1:])

    x = await message.reply("...")  # İşlemde olduğunu belirten mesaj
    model = "gpt-4o-mini" if message.command[0] != "gpt4" else "gpt-4"
    # Yapay zeka modeline kullanıcı girdisini gönder ve yanıt al
    response = await client.chat.completions.create(
        model=model,
        messages=[
            {"role": "user", "content": user_input},
        ],
    )

    # Gelen cevaptan gereksiz bağlantıyı kaldır ve temizle
    response_text = (
        response.choices[0]
        .message.content.replace("[[Login to OpenAI ChatGPT]]()", "")
        .strip()
    )

    # Telegram mesaj uzunluğu sınırı 4096 karakter, gerekirse böl
    if len(response_text) > 4000:
        parts = [
            response_text[i : i + 4000] for i in range(0, len(response_text), 4000)
        ]
        await x.edit(parts[0], parse_mode=ParseMode.DISABLED)
        for part in parts[1:]:
            await message.reply_text(part, parse_mode=ParseMode.DISABLED)
    else:
        await x.edit(response_text, parse_mode=ParseMode.DISABLED)

    await message.stop_propagation()