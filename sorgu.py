import os
import threading
import asyncio
import aiohttp
import json
import discord
from discord import app_commands
from discord.ext import commands, tasks
from flask import Flask

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
def format_api_response(title, raw_text):
    ucl_tirnak = "```"
    try:
        data = json.loads(raw_text)
        if isinstance(data, dict):
            data.pop("raw_response", None)
            data.pop("cipher", None)
            
            pretty_json = json.dumps(data, indent=4, ensure_ascii=False)
            return f"✅ **{title} Sonucu:**\n{ucl_tirnak}json\n{pretty_json[:1900]}\n{ucl_tirnak}"
    except Exception:
        pass
    return f"✅ **{title} Sonucu:**\n{ucl_tirnak}\n{raw_text[:1900]}\n{ucl_tirnak}"

# --- 4. KEEP-ALIVE ---
@tasks.loop(minutes=10)
async def keep_alive_ping():
    self_url = os.environ.get("RENDER_EXTERNAL_URL")
    if not self_url:
        return
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(self_url, timeout=10) as resp:
                print(f"[Keep-Alive] Ping başarılı: {resp.status}")
        except Exception as e:
            print(f"[Keep-Alive] Ping hatası: {e}")

@keep_alive_ping.before_loop
async def before_keep_alive_ping():
    await bot.wait_until_ready()

# ====================== MODALLAR ======================

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
        if self.il.value: url += f"&il={self.il.value}"
        if self.ilce.value: url += f"&ilce={self.ilce.value}"
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

# Diğer butonlar için placeholder (istediğin zaman doldururuz)
class BosModal(discord.ui.Modal, title="Yakında"):
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.send_message("Bu özellik yakında aktif olacak!", ephemeral=True)

# ====================== ORTAK SORGULAMA FONKSİYONU ======================
async def sorgu_yap(interaction: discord.Interaction, title: str, url: str):
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, timeout=20) as resp:
                sonuc = await resp.text()
                mesaj = format_api_response(title, sonuc)
                await interaction.followup.send(mesaj, ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ API Hatası: {str(e)}", ephemeral=True)

# ====================== BUTON PANELİ ======================
class SorguPaneli(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    # 1. Satır
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

    # 2. Satır
    @discord.ui.button(label="Adres", style=discord.ButtonStyle.primary, emoji="🏠", row=1)
    async def adres_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(AdresModal())

    @discord.ui.button(label="Öğretmen", style=discord.ButtonStyle.primary, emoji="👨‍🏫", row=1)
    async def ogretmen_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(BosModal())

    @discord.ui.button(label="Aşı Sorgu", style=discord.ButtonStyle.primary, emoji="💉", row=1)
    async def asi_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(BosModal())

    @discord.ui.button(label="E-Okul Free", style=discord.ButtonStyle.primary, emoji="📚", row=1)
    async def eokul_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(BosModal())

    # Daha fazla buton ekleyebiliriz (Instagram vs.)

# ====================== BOT ETKİNLİKLERİ ======================
@bot.event
async def on_ready():
    print(f"[{bot.user.name}] Başarıyla giriş yaptı.")
    if not keep_alive_ping.is_running():
        keep_alive_ping.start()
    try:
        await bot.tree.sync()
        print("Slash komutları senkronize edildi!")
    except Exception as e:
        print(f"Komut senkronizasyon hatası: {e}")

@bot.tree.command(name="sorgula", description="Sorgu panelini açar.")
async def sorgula(interaction: discord.Interaction):
    view = SorguPaneli()
    embed = discord.Embed(
        title="🪪 Zynex Sorgu Paneli",
        description="Aşağıdan istediğin sorguyu seç ve bilgileri gir.",
        color=discord.Color.from_rgb(155, 29, 32)
    )
    embed.set_footer(text="arastir.vip API Entegrasyonu")
    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

# ====================== ANA ÇALIŞTIRICI ======================
if __name__ == "__main__":
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()

    TOKEN = os.environ.get("DISCORD_TOKEN")
    if TOKEN:
        bot.run(TOKEN)
    else:
        print("HATA: DISCORD_TOKEN bulunamadı!")
