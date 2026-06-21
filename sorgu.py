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

class SorguModal(discord.ui.Modal):
    def __init__(self, sorgu_tipi):
        super().__init__(title=f'{sorgu_tipi} Sorgu Paneli')
        self.sorgu_tipi = sorgu_tipi
        self.input = discord.ui.TextInput(label='Sorgulanacak Değer', placeholder='Değeri girin...', required=True)
        self.add_item(self.input)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.send_message(f"🔍 `{self.input.value}` aranıyor...", ephemeral=True)
        
        val = self.input.value
        if self.sorgu_tipi == "Instagram": url = f"https://cc-3t5u.onrender.com/inslookup.php?username={val}"
        elif self.sorgu_tipi == "Domain": url = f"https://cc-3t5u.onrender.com/whoisapi.php?domain={val}"
        else: url = f"https://cc-3t5u.onrender.com/emailspam.php?email={val}"

        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    embed = discord.Embed(title=f"📋 {self.sorgu_tipi} Sonucu", color=discord.Color.green())
                    
                    # Veriyi türüne göre temizleyip ekrana bas
                    if self.sorgu_tipi == "Instagram":
                        embed.add_field(name="Ad Soyad", value=data.get("full_name", "Bilgi yok"), inline=False)
                        embed.add_field(name="Takipçi", value=str(data.get("followers", "0")), inline=True)
                        embed.add_field(name="Takip Edilen", value=str(data.get("following", "0")), inline=True)
                    else:
                        # Diğerleri için veriyi daha düzenli string yap
                        embed.description = f"```yaml\n{str(data)[:3500]}\n
```"
                        
                    await interaction.followup.send(embed=embed, ephemeral=True)
                else:
                    await interaction.followup.send("❌ API hatası veya sonuç bulunamadı.", ephemeral=True)

class SorguSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Instagram Sorgu", value="Instagram", emoji="📸"),
            discord.SelectOption(label="Domain Sorgu", value="Domain", emoji="🌐"),
            discord.SelectOption(label="Email Sorgu", value="Email", emoji="📧"),
        ]
        super().__init__(placeholder="Sorgu tipi seçin...", options=options)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(SorguModal(self.values[0]))

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
