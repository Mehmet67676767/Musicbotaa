import httpx
from pyrogram import Client, filters
from pyrogram.types import Message
from AlexaMusic import app

timeout = httpx.Timeout(40)
http = httpx.AsyncClient(http2=True, timeout=timeout)

# Api key used in weather.com's mobile app.
weather_apikey = "8de2d8b3a93542c9a2d8b3a935a2c909"

get_coords = "https://api.weather.com/v3/location/search"
url = "https://api.weather.com/v3/aggcommon/v3-wx-observations-current"

headers = {
    "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 12; M2012K11AG Build/SQ1D.211205.017)"
}

@app.on_message(filters.command("hava"))
async def weather(c: Client, m: Message):
    if len(m.command) == 1:
        return await m.reply_text(
            "<b>Kullanım:</b> <code>/hava Konum Veya Şehir</code> - Hava Durumu Hakkında Bilgi Almak İçin <i>Kullanabilirsiniz.</i>"
        )

    r = await http.get(
        get_coords,
        headers=headers,
        params=dict(
            apiKey=weather_apikey,
            format="json",
            language="tr",
            query=m.text.split(maxsplit=1)[1],
        ),
    )
    loc_json = r.json()

    if not loc_json.get("location"):
        await m.reply_text("Konum bulunamadı‌‌")
    else:
        pos = f"{loc_json['location']['latitude'][0]},{loc_json['location']['longitude'][0]}"
        r = await http.get(
            url,
            headers=headers,
            params=dict(
                apiKey=weather_apikey,
                format="json",
                language="tr",
                geocode=pos,
                units="m",
            ),
        )
        res_json = r.json()

        obs_dict = res_json["v3-wx-observations-current"]

        res = (
            "<b>{location}</b>:\n\n"
            "🌡️ **Sıcaklık: <code>{temperature} °C</code>\n**"
            "🔥 **Hissedilen: <code>{feels_like} °C</code>\n**"
            "💧 **Nem: <code>{air_humidity}%</code>\n**"
            "🌬️ **Rüzgar Hızı: <code>{wind_speed} km/h</code>\n\n**"
            "**Hava Durumu: <i>{overview}</i>**"
        ).format(
            location=loc_json["location"]["address"][0],
            temperature=obs_dict["temperature"],
            feels_like=obs_dict["temperatureFeelsLike"],
            air_humidity=obs_dict["relativeHumidity"],
            wind_speed=obs_dict["windSpeed"],
            overview=obs_dict["wxPhraseLong"],
        )

        await m.reply_text(res)