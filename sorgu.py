import os
import threading
import asyncio
import aiohttp
import discord
from discord import app_commands
from discord.ext import commands
from flask import Flask

# --- 1. RENDER İÇİN ARKA PLAN FLASK SERVER ---
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

# --- 3. MODALLAR (AÇILIR PENCERELER) ---

# Instagram Sorgu Penceresi
class InstagramModal(discord.ui.Modal, title="📸 Instagram Sorgulama"):
    username = discord.ui.TextInput(label="Instagram Kullanıcı Adı", placeholder="Örn: rte", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True) # Botun düşünme süresi
        url = f"https://cc-3t5u.onrender.com/inslookup.php?username={self.username.value}"
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, timeout=15) as resp:
                    sonuc = await resp.text()
                    # Hata almamak için güvenli üçlü tırnak (triple quotes) yapısına geçildi
                    mesaj = f"""📸 **{self.username.value}** için Instagram Sonucu:
```json
{sonuc[:1900]}
```"""
                    await interaction.followup.send(mesaj, ephemeral=True)
            except Exception as e:
                await interaction.followup.send(f"❌ API Hatası Oluştu: {str(e)}", ephemeral=True)

# Domain Sorgu Penceresi
class DomainModal(discord.ui.Modal, title="🌐 Domain Whois Sorgulama"):
    domain = discord.ui.TextInput(label="Domain Adresi", placeholder="Örn: exxen.com", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        url = f"https://cc-3t5u.onrender.com/whoisapi.php?domain={self.domain.value}"
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, timeout=15) as resp:
                    sonuc = await resp.text()
                    mesaj = f"""🌐 **{self.domain.value}** için Domain Sonucu:
```json
{sonuc[:1900]}
```"""
                    await interaction.followup.send(mesaj, ephemeral=True)
            except Exception as e:
                await interaction.followup.send(f"❌ API Hatası Oluştu: {str(e)}", ephemeral=True)

# Email Spam Penceresi
class EmailSpamModal(discord.ui.Modal, title="📧 Email Spam Gönderici"):
    email = discord.ui.TextInput(label="Hedef E-Posta Adresi", placeholder="Örn: ornek@mail.com", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        url = f"https://cc-3t5u.onrender.com/emailspam.php?email={self.email.value}"
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, timeout=15) as resp:
                    sonuc = await resp.text()
                    mesaj = f"""📧 **{self.email.value}** için Spam İsteği Durumu:
```json
{sonuc[:1900]}
```"""
                    await interaction.followup.send(mesaj, ephemeral=True)
            except Exception as e:
                await interaction.followup.send(f"❌ API Hatası Oluştu: {str(e)}", ephemeral=True)


# --- 4. GÖRSEL BUTONLAR MENÜSÜ (VIEW) ---
class SorguPaneli(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None) # Butonların süresi dolmasın, hep aktif kalsın

    @discord.ui.button(label="Instagram Sorgu", style=discord.ButtonStyle.danger, emoji="📸", row=0)
    async def instagram_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(InstagramModal())

    @discord.ui.button(label="Domain Sorgu", style=discord.ButtonStyle.primary, emoji="🌐", row=0)
    async def domain_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(DomainModal())

    @discord.ui.button(label="Email Spam", style=discord.ButtonStyle.secondary, emoji="📧", row=1)
    async def email_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(EmailSpamModal())


# --- 5. BOT ETKİNLİKLERİ VE SLASH KOMUTU ---
@bot.event
async def on_ready():
    print(f"[{bot.user.name}] Başarıyla giriş yaptı ve komutlar senkronize ediliyor...")
    try:
        synced = await bot.tree.sync()
        print(f"✅ {len(synced)} adet slash komutu başarıyla senkronize edildi!")
    except Exception as e:
        print(f"❌ Komut senkronizasyon hatası: {e}")

# /sorgula komutu
@bot.tree.command(name="sorgula", description="Sorgulama panelini ve butonları açar.")
async def sorgula(interaction: discord.Interaction):
    view = SorguPaneli()
    # ephemeral=True sayesinde mesajı SADECE komutu yazan kişi görebilir.
    await interaction.response.send_message(
        "🔮 **Sorgu ve İşlem Paneline Hoş Geldiniz!**\nLütfen yapmak istediğiniz işlemi aşağıdaki butonları kullanarak seçin:", 
        view=view, 
        ephemeral=True
    )


# --- 6. ANA ÇALIŞTIRICI ---
if __name__ == "__main__":
    # Flask web sunucusunu Render için ayrı bir kolda başlatıyoruz
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()

    # Render panelinden ekleyeceğiniz DISCORD_TOKEN ile botu çalıştırır
    TOKEN = os.environ.get("DISCORD_TOKEN")
    if TOKEN:
        bot.run(TOKEN)
    else:
        print("HATA: Render ayarlarında 'DISCORD_TOKEN' bulunamadı!")
