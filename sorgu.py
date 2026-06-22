import os
import threading
import asyncio
import json
import discord
from discord.ext import commands
from flask import Flask
from curl_cffi import requests as cf_requests

# --- 1. FLASK SERVER ---
app = Flask(__name__)
@app.route('/')
def home():
    return "Bot 7/24 Aktif!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

# --- 2. DISCORD BOT AYARLARI ---
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# --- 3. FORMATLAYICI ---
def format_api_response(title: str, raw_text: str):
    if any(x in raw_text.lower() for x in ["cloudflare", "challenge", "just a moment", "<!doctype html>", "attention required"]):
        return discord.Embed(
            title=f"❌ {title} Sonucu",
            description="**Cloudflare Koruması Aktif**\nSunucu IP'niz API tarafından kısıtlanıyor.",
            color=discord.Color.red()
        )

    try:
        data = json.loads(raw_text)
        embed = discord.Embed(title=f"✅ {title} Sonucu", color=discord.Color.green())
        for key, value in data.items():
            if not value: continue
            if isinstance(value, dict):
                field_text = "\n".join([f"**{k}:** `{v}`" for k, v in value.items() if v])
                embed.add_field(name=key.replace("_", " ").title(), value=field_text[:1024] or "-", inline=False)
            else:
                embed.add_field(name=key.replace("_", " ").title(), value=f"`{value}`", inline=len(str(value)) < 40)
        return embed
    except:
        return discord.Embed(title=f"⚠️ {title} Sonucu", description="API geçerli veri döndürmedi.", color=discord.Color.orange())

# --- 4. SORGU FONKSİYONU (PROXY EKLENDİ) ---
async def sorgu_yap(interaction: discord.Interaction, title: str, url: str):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
        "Referer": "https://arastir.vip/",
        "X-Author": "Zynex"
    }
    
    # Proxy adresini buraya ekleyebilirsin: "http://kullanici:sifre@ip:port"
    proxy = None 
    
    try:
        def fetch():
            # Eğer proxy kullanacaksan proxy=proxy parametresini aktif et
            return cf_requests.get(url, headers=headers, impersonate="chrome120", 
                                   proxies={"http": proxy, "https": proxy} if proxy else None, 
                                   timeout=20)
        
        loop = asyncio.get_event_loop()
        resp = await loop.run_in_executor(None, fetch)
        
        mesaj = format_api_response(title, resp.text)
        await interaction.followup.send(embed=mesaj, ephemeral=True)
    except Exception as e:
        await interaction.followup.send(f"❌ API Hatası: {str(e)}", ephemeral=True)

# --- 5. MODALLAR ---
class TcModal(discord.ui.Modal, title="🔍 TC Sorgula"):
    tc = discord.ui.TextInput(label="TC Kimlik No", required=True)
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        await sorgu_yap(interaction, "TC Sorgu", f"https://arastir.vip/api/tc.php?tc={self.tc.value}")

class AdSoyadModal(discord.ui.Modal, title="👤 Ad Soyad Sorgu"):
    ad = discord.ui.TextInput(label="Ad", required=True)
    soyad = discord.ui.TextInput(label="Soyad", required=True)
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        await sorgu_yap(interaction, "Ad Soyad Sorgu", f"https://arastir.vip/api/adsoyad.php?adi={self.ad.value}&soyadi={self.soyad.value}")

class GsmToTcModal(discord.ui.Modal, title="📱 GSM → TC"):
    gsm = discord.ui.TextInput(label="GSM Numara", required=True)
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        await sorgu_yap(interaction, "GSM to TC", f"https://arastir.vip/api/gsmtc.php?gsm={self.gsm.value}")

class TcToGsmModal(discord.ui.Modal, title="🔢 TC → GSM"):
    tc = discord.ui.TextInput(label="TC Kimlik No", required=True)
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        await sorgu_yap(interaction, "TC to GSM", f"https://arastir.vip/api/tcgsm.php?tc={self.tc.value}")

class AdresModal(discord.ui.Modal, title="🏠 Adres Sorgu"):
    tc = discord.ui.TextInput(label="TC Kimlik No", required=True)
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        await sorgu_yap(interaction, "Adres Sorgu", f"https://arastir.vip/api/adres.php?tc={self.tc.value}")

class SulaleModal(discord.ui.Modal, title="👨‍👩‍👧‍👦 Sülale Sorgu"):
    tc = discord.ui.TextInput(label="TC Kimlik No", required=True)
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        await sorgu_yap(interaction, "Sülale Sorgu", f"https://arastir.vip/api/sulale.php?tc={self.tc.value}")

class InstagramModal(discord.ui.Modal, title="📸 Instagram Sorgulama"):
    username = discord.ui.TextInput(label="Kullanıcı Adı", required=True)
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        await sorgu_yap(interaction, "Instagram Sorgu", f"https://cc-3t5u.onrender.com/inslookup.php?username={self.username.value}")

# --- 6. BUTON PANELİ ---
class SorguPaneli(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)
    
    @discord.ui.button(label="TC", style=discord.ButtonStyle.primary, row=0)
    async def tc_btn(self, i, b): await i.response.send_modal(TcModal())
    @discord.ui.button(label="Ad Soyad", style=discord.ButtonStyle.primary, row=0)
    async def ad_btn(self, i, b): await i.response.send_modal(AdSoyadModal())
    @discord.ui.button(label="GSM TC", style=discord.ButtonStyle.primary, row=0)
    async def gsm_btn(self, i, b): await i.response.send_modal(GsmToTcModal())
    @discord.ui.button(label="TC GSM", style=discord.ButtonStyle.primary, row=1)
    async def tcgsm_btn(self, i, b): await i.response.send_modal(TcToGsmModal())
    @discord.ui.button(label="Adres", style=discord.ButtonStyle.primary, row=1)
    async def adr_btn(self, i, b): await i.response.send_modal(AdresModal())
    @discord.ui.button(label="Sülale", style=discord.ButtonStyle.primary, row=1)
    async def sul_btn(self, i, b): await i.response.send_modal(SulaleModal())
    @discord.ui.button(label="Insta", style=discord.ButtonStyle.primary, row=2)
    async def ins_btn(self, i, b): await i.response.send_modal(InstagramModal())

# --- 7. BOT KOMUTU ---
@bot.tree.command(name="sorgula", description="Sorgu panelini açar.")
async def sorgula(interaction: discord.Interaction):
    await interaction.response.send_message("Panel:", view=SorguPaneli(), ephemeral=True)

@bot.event
async def on_ready():
    await bot.tree.sync()
    print("Bot hazır ve senkronize edildi.")

if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    TOKEN = os.environ.get("DISCORD_TOKEN")
    if TOKEN: bot.run(TOKEN)
