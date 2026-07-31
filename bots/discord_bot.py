from discord.ext import commands
import discord
import os
import requests
from dotenv import load_dotenv

load_dotenv()
BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN')
SITE_URL = os.getenv('SITE_URL', 'http://localhost:5000')
BOT_SECRET = os.getenv('BOT_SHARED_SECRET', 'change-me')

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents, description='Site-57 Bot')


def is_admin():
    allowed_roles = [r.strip() for r in os.getenv('ADMIN_ROLE_IDS', '').split(',') if r.strip()]
    allowed_users = [u.strip() for u in os.getenv('ADMIN_USER_IDS', '').split(',') if u.strip()]
    def predicate(ctx):
        # Allow if the user id is explicitly allowed
        if str(ctx.author.id) in allowed_users:
            return True
        # Allow if any role id matches
        try:
            for role in ctx.author.roles:
                if str(role.id) in allowed_roles:
                    return True
        except Exception:
            pass
        return False
    return commands.check(predicate)


@bot.event
async def on_ready():
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')


@bot.command(name='alerte')
@is_admin()
async def alerte(ctx, level: str, *, message: str):
    """Envoyer une alerte au site via l'API interne.
    Usage: !alerte <niveau> <message>
    Exemple: !alerte "Code Rouge" "Brèche de confinement secteur 3"
    """
    payload = {'level': level, 'message': message, 'author': str(ctx.author)}
    headers = {'X-BOT-SECRET': BOT_SECRET, 'Content-Type': 'application/json'}
    try:
        r = requests.post(f'{SITE_URL}/api/bot/alert', json=payload, headers=headers, timeout=5)
        if r.status_code == 200:
            await ctx.send(f'Alerte envoyée: **{level}** — {message}')
        else:
            await ctx.send(f'Erreur envoi alerte: {r.status_code} — {r.text}')
    except Exception as e:
        await ctx.send(f'Exception lors de l\'envoi de l\'alerte: {e}')


if __name__ == '__main__':
    if not BOT_TOKEN:
        print('DISCORD_BOT_TOKEN manquant dans les variables d\'environnement')
        exit(1)
    bot.run(BOT_TOKEN)
