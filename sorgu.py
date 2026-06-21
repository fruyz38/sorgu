import discord
from discord.ext import commands
import aiohttp
import os
from flask import Flask
from threading import Thread

# 1. Port çakışmaması için 8081 yaptık
app = Flask('')
@app.route('/')
def home(): return "Sorgu botu aktif!"
def run(): app.run(host='0.0.0.0', port=8081)
Thread(target=run).start()

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f'Sorgu botu {bot.user} olarak giriş yaptı!')

@bot.command()
async def sorgula(ctx, username: str):
    # Senin verdiğin API adresi
    api_url = f"https://cc-3t5u.onrender.com/inslookup.php?username={username}"
    
    mesaj = await ctx.send(f"🔍 `{username}` aranıyor...")

    async with aiohttp.ClientSession() as session:
        async with session.get(api_url) as response:
            if response.status == 200:
                data = await response.json()
                
                # API'den gelen veriyi Embed'e döküyoruz
                embed = discord.Embed(title=f"📸 Instagram Sorgu: {username}", color=discord.Color.purple())
                embed.add_field(name="Ad Soyad", value=data.get("full_name", "Bilgi yok"), inline=False)
                embed.add_field(name="Takipçi", value=data.get("followers", "0"), inline=True)
                embed.add_field(name="Takip Edilen", value=data.get("following", "0"), inline=True)
                embed.add_field(name="Biyografi", value=data.get("biography", "Yok"), inline=False)
                
                await mesaj.edit(content=None, embed=embed)
            else:
                await mesaj.edit(content="❌ API hatası veya kullanıcı bulunamadı.")

# 2. Token değişkeni farklı olsun ki karışmasın
bot.run(os.environ['SORGU_BOT_TOKEN'])