import discord
from discord.ext import commands
import aiohttp
import os
from flask import Flask
from threading import Thread

# 1. Web Sunucusu (Render üzerinde botun 7/24 aktif kalmasını sağlar)
app = Flask('')
@app.route('/')
def home(): 
    return "Sorgu botu aktif!"

def run(): 
    app.run(host='0.0.0.0', port=8081)

Thread(target=run).start()

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

# 2. Sorgu Bilgisi Giriş Ekranı (Modal/Pencere)
class SorguModal(discord.ui.Modal):
    def __init__(self, sorgu_tipi):
        super().__init__(title=f'{sorgu_tipi} Sorgu Paneli')
        self.sorgu_tipi = sorgu_tipi
        self.input = discord.ui.TextInput(
            label='Sorgulanacak Değer', 
            placeholder='Değeri buraya girin...', 
            required=True
        )
        self.add_item(self.input)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.send_message(f"🔍 `{self.input.value}` aranıyor...", ephemeral=True)
        val = self.input.value
        
        urls = {
            "Instagram": f"https://cc-3t5u.onrender.com/inslookup.php?username={val}",
            "Email": f"https://cc-3t5u.onrender.com/emailspam.php?email={val}",
            "Domain": f"https://cc-3t5u.onrender.com/whoisapi.php?domain={val}"
        }
        url = urls.get(self.sorgu_tipi)

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=15) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        embed = discord.Embed(title=f"📋 {self.sorgu_tipi} Sonucu", color=discord.Color.green())
                        
                        if self.sorgu_tipi == "Instagram":
                            embed.add_field(name="Ad Soyad", value=data.get("full_name", "Bilgi yok"), inline=False)
                            embed.add_field(name="Takipçi", value=str(data.get("followers", "0")), inline=True)
                            embed.add_field(name="Takip Edilen", value=str(data.get("following", "0")), inline=True)
                        else:
                            # Hatalı olan kırık link satırı tamamen temizlendi
                            embed.description = f"
http://googleusercontent.com/immersive_entry_chip/0
