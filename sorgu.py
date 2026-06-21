import discord
from discord.ext import commands
import aiohttp
import os
from flask import Flask
from threading import Thread

# Web sunucusu
app = Flask('')
@app.route('/')
def home(): return "Sorgu botu aktif!"
def run(): app.run(host='0.0.0.0', port=8081)
Thread(target=run).start()

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

# MODAL: Bilgi girişi
class SorguModal(discord.ui.Modal):
    def __init__(self, sorgu_tipi, api_url_format):
        super().__init__(title=f'{sorgu_tipi} Paneli')
        self.sorgu_tipi = sorgu_tipi
        self.api_url_format = api_url_format
        self.input_field = discord.ui.TextInput(label='Sorgulanacak Değer', placeholder='Değeri buraya gir...', required=True)
        self.add_item(self.input_field)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.send_message(f"🔍 `{self.input_field.value}` aranıyor...", ephemeral=True)
        
        # Linkteki {value} kısmını kullanıcının girdiği değerle değiştiriyoruz
        url = self.api_url_format.replace("EXXEN.COM", self.input_field.value).replace("ORNEK@MAIL.COM", self.input_field.value).replace("RTE", self.input_field.value)
        # Not: Eğer API linklerin tam olarak ?domain=... şeklinde bitmiyorsa burayı biraz özelleştirebiliriz.
        # Senin verdiğin linklere göre linki dinamik hale getirdim:
        if "domain" in self.api_url_format: url = f"https://cc-3t5u.onrender.com/whoisapi.php?domain={self.input_field.value}"
        elif "email" in self.api_url_format: url = f"https://cc-3t5u.onrender.com/emailspam.php?email={self.input_field.value}"
        else: url = f"https://cc-3t5u.onrender.com/inslookup.php?username={self.input_field.value}"

        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    embed = discord.Embed(title=f"📋 Sonuç: {self.sorgu_tipi}", color=discord.Color.green())
                    embed.description = f"```json\n{data}\n```" # Veriyi temiz göstermek için
                    await interaction.followup.send(embed=embed, ephemeral=True)
                else:
                    await interaction.followup.send("❌ API hatası veya sonuç bulunamadı.", ephemeral=True)

# SEÇİM MENÜSÜ
class SorguSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Instagram Sorgu", value="insta", emoji="📸"),
            discord.SelectOption(label="Domain Sorgu", value="domain", emoji="🌐"),
            discord.SelectOption(label="Email Sorgu", value="email", emoji="📧"),
        ]
        super().__init__(placeholder="Bir sorgu türü seç...", options=options)

    async def callback(self, interaction: discord.Interaction):
        # Seçime göre modalı tetikle
        urls = {"insta": "...", "domain": "...", "email": "..."}
        await interaction.response.send_modal(SorguModal(self.values[0].upper(), urls[self.values[0]]))

@bot.tree.command(name="sorgula", description="Sorgu menüsünü açar")
async def sorgula(interaction: discord.Interaction):
    view = discord.ui.View()
    view.add_item(SorguSelect())
    await interaction.response.send_message("Lütfen bir sorgu tipi seçin:", view=view, ephemeral=True)

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f'{bot.user} aktif!')

bot.run(os.environ['SORGU_BOT_TOKEN'])
