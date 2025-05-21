import discord
from discord.ext import commands, tasks
import feedparser
import sqlite3
from config import TOKEN

intents = discord.Intents.default()
intents.messages = True
bot = commands.Bot(command_prefix='!', intents=intents)

# URL RSS berita sepak bola
rss_feed_url = "https://www.goal.com/feeds/en/news"

# ====== DATABASE SETUP ======
conn = sqlite3.connect("subscriptions.db")
cursor = conn.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS subscriptions (
    user_id INTEGER,
    keyword TEXT
)
''')
conn.commit()

# ====== FUNGSI ======
def get_news(feed_url):
    feed = feedparser.parse(feed_url)
    return [{'title': entry.title, 'link': entry.link} for entry in feed.entries]

def get_user_subscriptions(user_id):
    cursor.execute("SELECT keyword FROM subscriptions WHERE user_id=?", (user_id,))
    return [row[0] for row in cursor.fetchall()]

def get_all_subscriptions():
    cursor.execute("SELECT DISTINCT user_id FROM subscriptions")
    return [row[0] for row in cursor.fetchall()]

def get_all_keywords(user_id):
    cursor.execute("SELECT keyword FROM subscriptions WHERE user_id=?", (user_id,))
    return [row[0] for row in cursor.fetchall()]

# ====== PERINTAH BOT ======

@bot.command()
async def news(ctx):
    news = get_news(rss_feed_url)
    if not news:
        await ctx.send("Tidak dapat mengambil berita.")
        return
    response = "\n".join([f"{entry['title']} - {entry['link']}" for entry in news[:5]])
    await ctx.send(response if response else "Tidak ada berita.")

@bot.command()
async def subscribe(ctx, *, keyword):
    user_id = ctx.author.id
    cursor.execute("SELECT * FROM subscriptions WHERE user_id=? AND keyword=?", (user_id, keyword))
    if cursor.fetchone():
        await ctx.send(f"Kamu sudah berlangganan '{keyword}'.")
    else:
        cursor.execute("INSERT INTO subscriptions (user_id, keyword) VALUES (?, ?)", (user_id, keyword))
        conn.commit()
        await ctx.send(f"Berhasil berlangganan: '{keyword}'.")

@bot.command()
async def unsubscribe(ctx, *, keyword):
    user_id = ctx.author.id
    cursor.execute("DELETE FROM subscriptions WHERE user_id=? AND keyword=?", (user_id, keyword))
    conn.commit()
    await ctx.send(f"Berhenti berlangganan: '{keyword}'.")

@bot.command()
async def notifications(ctx):
    user_id = ctx.author.id
    keywords = get_user_subscriptions(user_id)
    if keywords:
        await ctx.send("Kata kunci langganan kamu:\n" + "\n".join(keywords))
    else:
        await ctx.send("Kamu belum berlangganan apapun.")

@bot.command()
async def latest(ctx):
    user_id = ctx.author.id
    keywords = get_user_subscriptions(user_id)
    if not keywords:
        await ctx.send("Kamu belum berlangganan apapun.")
        return

    news = get_news(rss_feed_url)
    matched = []
    for entry in news:
        if any(k.lower() in entry['title'].lower() for k in keywords):
            matched.append(entry)

    if matched:
        response = "\n".join([f"{entry['title']} - {entry['link']}" for entry in matched[:5]])
        await ctx.send(response)
    else:
        await ctx.send("Tidak ada berita cocok dengan langganan kamu.")

@bot.command()
async def info(ctx):
    await ctx.send(
        "**Perintah yang tersedia:**\n"
        "`!news` - Berita terbaru sepak bola.\n"
        "`!subscribe <kata kunci>` - Langganan berita.\n"
        "`!unsubscribe <kata kunci>` - Hapus langganan.\n"
        "`!notifications` - Lihat langganan.\n"
        "`!latest` - Berita sesuai langganan.\n"
        "`!info` - Tampilkan bantuan ini."
    )

# ====== TUGAS OTOMATIS (opsional) ======
@tasks.loop(minutes=10)
async def update_news():
    # Di sini bisa kamu tambahkan logika otomatis kirim berita ke user jika mau.
    # Sekarang hanya untuk persiapan auto-broadcast.
    pass

@bot.event
async def on_ready():
    update_news.start()
    print(f'Bot aktif sebagai {bot.user}')

bot.run(TOKEN)
