import os
import asyncio
import aiohttp
import json
import discord
from discord import app_commands
from discord.ext import commands, tasks
import logging
import sys
import io
from flask import Flask
from threading import Thread

app = Flask('')

@app.route('/')
def home():
    return "Bot aktif!"

def run():
    app.run(host='0.0.0.0', port=8080)
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', write_through=True)
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', write_through=True)

logging.basicConfig(level=logging.INFO)

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

def format_api_response(title: str, raw_text: str):
    try:
        print(f"API Yanıtı: {raw_text}")
        data = json.loads(raw_text)  # <--- BU SATIRI MUTLAKA EKLEMELİSİN
        
        if not isinstance(data, dict):
            return f"✅ **{title} Sonucu:**\n

        for key in ["telegram", "Telegram", "raw_response", "cipher", "success"]:
            data.pop(key, None)

        embed = discord.Embed(title=f"✅ {title} Sonucu", color=discord.Color.green())

        for key, value in data.items():
            if not value:
                continue
            if isinstance(value, dict):
                field_text = "\n".join([f"**{k}:** `{v}`" for k, v in value.items() if v])
                embed.add_field(name=key.replace("_", " ").title(), value=field_text[:1024] or "-", inline=False)
            elif isinstance(value, list):
                embed.add_field(name=key.replace("_", " ").title(), value=f"{len(value)} adet bulundu", inline=False)
            else:
                embed.add_field(
                    name=key.replace("_", " ").title(),
                    value=f"`{value}`",
                    inline=len(str(value)) < 40
                )
        return embed

    except Exception:
        return discord.Embed(title=f"⚠️ {title} Sonucu", description="API geçerli veri döndürmedi.", color=discord.Color.orange())

async def sorgu_yap(interaction: discord.Interaction, title: str, url: str):
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, timeout=45) as resp:
                sonuc = await resp.text()
                mesaj = format_api_response(title, sonuc)
                
                if isinstance(mesaj, discord.Embed):
                    await interaction.followup.send(embed=mesaj, ephemeral=True)
                else:
                    await interaction.followup.send(mesaj, ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ API Hatası: {str(e)}", ephemeral=True)

class TcModal(discord.ui.Modal, title="🔍 TC Sorgula"):
    tc = discord.ui.TextInput(label="TC Kimlik No", placeholder="11 haneli TC", required=True)
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        url = f"https://arastir.vip/api/tc.php?tc={self.tc.value}"
        await sorgu_yap(interaction, "TC Sorgu", url)

class AdSoyadModal(discord.ui.Modal, title="👤 Ad Soyad Sorgu"):
    ad = discord.ui.TextInput(label="Ad", placeholder="Ahmet", required=True)
    soyad = discord.ui.TextInput(label="Soyad", placeholder="Yılmaz", required=True)
    il = discord.ui.TextInput(label="İl (Opsiyonel)", placeholder="İstanbul", required=False)
    ilce = discord.ui.TextInput(label="İlçe (Opsiyonel)", placeholder="Kadıköy", required=False)
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        url = f"https://arastir.vip/api/adsoyad.php?adi={self.ad.value}&soyadi={self.soyad.value}"
        if self.il.value.strip(): url += f"&il={self.il.value}"
        if self.ilce.value.strip(): url += f"&ilce={self.ilce.value}"
        await sorgu_yap(interaction, "Ad Soyad Sorgu", url)

class GsmToTcModal(discord.ui.Modal, title="📱 GSM → TC"):
    gsm = discord.ui.TextInput(label="GSM Numara", placeholder="05xxxxxxxxx", required=True)
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        url = f"https://arastir.vip/api/gsmtc.php?gsm={self.gsm.value}"
        await sorgu_yap(interaction, "GSM to TC", url)

class TcToGsmModal(discord.ui.Modal, title="🔢 TC → GSM"):
    tc = discord.ui.TextInput(label="TC Kimlik No", placeholder="11 haneli TC", required=True)
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        url = f"https://arastir.vip/api/tcgsm.php?tc={self.tc.value}"
        await sorgu_yap(interaction, "TC to GSM", url)

class AdresModal(discord.ui.Modal, title="🏠 Adres Sorgu"):
    tc = discord.ui.TextInput(label="TC Kimlik No", placeholder="11 haneli TC", required=True)
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        url = f"https://arastir.vip/api/adres.php?tc={self.tc.value}"
        await sorgu_yap(interaction, "Adres Sorgu", url)

class SulaleModal(discord.ui.Modal, title="👨‍👩‍👧‍👦 Sülale Sorgu"):
    tc = discord.ui.TextInput(label="TC Kimlik No", placeholder="11 haneli TC", required=True)
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        url = f"https://arastir.vip/api/sulale.php?tc={self.tc.value}"
        await sorgu_yap(interaction, "Sülale Sorgu", url)

class InstagramModal(discord.ui.Modal, title="📸 Instagram Sorgulama"):
    username = discord.ui.TextInput(label="Instagram Kullanıcı Adı", placeholder="Örn: rte", required=True)
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        url = f"https://cc-3t5u.onrender.com/inslookup.php?username={self.username.value}"
        await sorgu_yap(interaction, "Instagram Sorgu", url)

class SorguPaneli(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="TC Sorgula", style=discord.ButtonStyle.primary, emoji="🔍", row=0)
    async def tc_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(TcModal())

    @discord.ui.button(label="Ad Soyad", style=discord.ButtonStyle.primary, emoji="👤", row=0)
    async def adsoyad_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(AdSoyadModal())

    @discord.ui.button(label="Gsm To Tc", style=discord.ButtonStyle.primary, emoji="📱", row=0)
    async def gsmtotc_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(GsmToTcModal())

    @discord.ui.button(label="Tc To Gsm", style=discord.ButtonStyle.primary, emoji="🔢", row=0)
    async def tctogsm_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(TcToGsmModal())

    @discord.ui.button(label="Sülale", style=discord.ButtonStyle.primary, emoji="👨‍👩‍👧‍👦", row=0)
    async def sulale_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(SulaleModal())

    @discord.ui.button(label="Adres", style=discord.ButtonStyle.primary, emoji="🏠", row=1)
    async def adres_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(AdresModal())

    @discord.ui.button(label="Instagram", style=discord.ButtonStyle.primary, emoji="📸", row=1)
    async def instagram_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(InstagramModal())

@bot.event
async def on_ready():
    print(f"[{bot.user.name}] Başarıyla giriş yaptı.")
    try:
        await bot.tree.sync()
        print("✅ Komutlar senkronize edildi!")
    except Exception as e:
        print(f"Komut hatası: {e}")

@bot.tree.command(name="sorgula", description="Sorgu panelini açar.")
async def sorgula(interaction: discord.Interaction):
    view = SorguPaneli()
    embed = discord.Embed(
        title="🪪 Zynex Sorgu Paneli",
        description="Aşağıdaki butonlardan istediğini seç.",
        color=discord.Color.from_rgb(155, 29, 32)
    )
    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

if __name__ == "__main__":
    # Web sunucusunu arka planda başlat
    t = Thread(target=run)
    t.start()
    
    # Token'ı environment variable olarak al
    TOKEN = os.getenv("DISCORD_TOKEN")
    
    if TOKEN:
        print("🤖 Bot başlatılıyor, Discord'a bağlanılıyor...")
        bot.run(TOKEN)
    else:
        print("❌ HATA: 'DISCORD_TOKEN' adında bir ortam değişkeni bulunamadı!")
        print("Lütfen Render panelinden Environment Variables kısmına DISCORD_TOKEN ekleyin.")
        
