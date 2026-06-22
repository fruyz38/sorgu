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

# --- 3. GELİŞMİŞ FORMATLAYICI (HTML & Hata tespiti) ---
def format_api_response(title: str, raw_text: str):
    # Cloudflare veya HTML tespiti
    if "<!DOCTYPE html>" in raw_text or "cloudflare" in raw_text.lower() or "<html" in raw_text.lower():
        return discord.Embed(
            title=f"❌ {title} Sonucu",
            description="**API şu anda Cloudflare koruması altında.**\n\nBiraz sonra tekrar deneyin.",
            color=discord.Color.red()
        )

    try:
        data = json.loads(raw_text)
        
        if not isinstance(data, dict):
            return f"✅ **{title} Sonucu:**\n```json\n{raw_text[:1900]}\n```"

        # İstenmeyen alanları temizle
        temizlenecek = ["telegram", "Telegram", "tele", "raw_response", "cipher", "success", "status_code"]
        for key in temizlenecek:
            data.pop(key, None)
            data.pop(key.lower(), None)
            data.pop(key.upper(), None)

        embed = discord.Embed(
            title=f"✅ {title} Sonucu",
            color=discord.Color.green()
        )

        for key, value in data.items():
            if value is None or value == "" or value == [] or value == {}:
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
        # JSON değilse ve HTML de değilse
        return discord.Embed(
            title=f"⚠️ {title} Sonucu",
            description="API'den beklenmeyen yanıt alındı.",
            color=discord.Color.orange()
        )

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

# ====================== ORTAK SORGU ======================
async def sorgu_yap(interaction: discord.Interaction, title: str, url: str):
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, timeout=25) as resp:
                sonuc = await resp.text()
                mesaj = format_api_response(title, sonuc)
                
                if isinstance(mesaj, discord.Embed):
                    await interaction.followup.send(embed=mesaj, ephemeral=True)
                else:
                    await interaction.followup.send(mesaj, ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ Bağlantı Hatası: {str(e)}", ephemeral=True)

# ====================== MODALLAR ======================
# (Tüm modallar aynı kaldı - yer tasarrufu için kısalttım)
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

class InstagramModal(discord.ui.Modal, title="📸 Instagram Sorgulama"):
    username = discord.ui.TextInput(label="Instagram Kullanıcı Adı", placeholder="Örn: rte", required=True)
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        url = f"https://cc-3t5u.onrender.com/inslookup.php?username={self.username.value}"
        await sorgu_yap(interaction, "Instagram Sorgu", url)

class DomainModal(discord.ui.Modal, title="🌐 Domain Whois"):
    domain = discord.ui.TextInput(label="Domain Adresi", placeholder="Örn: exxen.com", required=True)
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        url = f"https://cc-3t5u.onrender.com/whoisapi.php?domain={self.domain.value}"
        await sorgu_yap(interaction, "Domain Whois", url)

class EmailSpamModal(discord.ui.Modal, title="📧 Email Spam"):
    email = discord.ui.TextInput(label="Hedef E-Posta", placeholder="ornek@mail.com", required=True)
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        url = f"https://cc-3t5u.onrender.com/emailspam.php?email={self.email.value}"
        await sorgu_yap(interaction, "Email Spam", url)

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

    @discord.ui.button(label="Instagram", style=discord.ButtonStyle.primary, emoji="📸", row=1)
    async def instagram_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(InstagramModal())

    @discord.ui.button(label="Domain", style=discord.ButtonStyle.primary, emoji="🌐", row=1)
    async def domain_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(DomainModal())

    @discord.ui.button(label="Email Spam", style=discord.ButtonStyle.primary, emoji="📧", row=1)
    async def email_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(EmailSpamModal())

# ====================== ANA KOMUT ======================
@bot.event
async def on_ready():
    print(f"[{bot.user.name}] Başarıyla giriş yaptı.")
    if not keep_alive_ping.is_running():
        keep_alive_ping.start()
    try:
        await bot.tree.sync()
        print("✅ Slash komutları senkronize edildi!")
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

# ====================== ÇALIŞTIRICI ======================
if __name__ == "__main__":
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()

    TOKEN = os.environ.get("DISCORD_TOKEN")
    if TOKEN:
        bot.run(TOKEN)
    else:
        print("❌ DISCORD_TOKEN bulunamadı!")
