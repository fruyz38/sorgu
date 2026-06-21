import discord
from discord import app_commands
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

# MODAL: Sadece sorgulayan kişiye özel cevap verecek
class SorguModal(discord.ui.Modal, title='Instagram Sorgu Paneli'):
    username = discord.ui.TextInput(label='Kullanıcı Adı', placeholder='Örn: rte', required=True)

    async def on_submit(self, interaction: discord.Interaction):
        # İlk cevap gizli
        await interaction.response.send_message(f"🔍 `{self.username.value}` aranıyor...", ephemeral=True)
        
        api_url = f"https://cc-3t5u.onrender.com/inslookup.php?username={self.username.value}"
        async with aiohttp.ClientSession() as session:
            async with session.get(api_url) as response:
                if response.status == 200:
                    data = await response.json()
                    embed = discord.Embed(title=f"📸 Sonuç: {self.username.value}", color=discord.Color.purple())
                    embed.add_field(name="Ad Soyad", value=data.get("full_name", "Bilgi yok"), inline=False)
                    embed.add_field(name="Takipçi", value=data.get("followers", "0"), inline=True)
                    embed.add_field(name="Takip Edilen", value=data.get("following", "0"), inline=True)
                    
                    # Sonuçlar sadece sorgulayana özel (ephemeral=True)
                    await interaction.followup.send(embed=embed, ephemeral=True)
                else:
                    await interaction.followup.send("❌ API hatası veya kullanıcı bulunamadı.", ephemeral=True)

# KOMUT: Slash komut ile tetikleme
@bot.tree.command(name="sorgula", description="Sorgu menüsünü açar")
async def sorgula(interaction: discord.Interaction):
    view = discord.ui.View()
    button = discord.ui.Button(label="Sorgu Başlat", style=discord.ButtonStyle.primary)
    
    async def button_callback(interaction: discord.Interaction):
        await interaction.response.send_modal(SorguModal())
    
    button.callback = button_callback
    view.add_item(button)
    # Menü çağrısı sadece kullanıcıya özel
    await interaction.response.send_message("Aşağıdaki butona basarak sorgu panelini aç:", view=view, ephemeral=True)

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f'{bot.user} aktif!')

bot.run(os.environ['SORGU_BOT_TOKEN'])
