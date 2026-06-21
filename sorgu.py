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
                    await interaction.followup.send(f"📸 **{self.username.value}** için Instagram Sonucu:\n
http://googleusercontent.com/immersive_entry_chip/0
http://googleusercontent.com/immersive_entry_chip/1
http://googleusercontent.com/immersive_entry_chip/2
