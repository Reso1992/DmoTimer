import os
import discord
import json
from discord.ext import commands, tasks
from datetime import datetime, timedelta

class TourTimer:
    def __init__(self, ctx, duration, image_url, custom_message=None):
        self.ctx, self.duration, self.image_url = ctx, duration, image_url
        self.end_time = datetime.utcnow() + timedelta(hours=duration)
        self.custom_message, self.timer_message, self.color = custom_message, None, discord.Color.blue()
        self.reminded = False

    def remaining_time(self):
        return max(self.end_time - datetime.utcnow(), timedelta(seconds=0))

    def progress_bar(self):
        total_seconds = self.duration * 3600
        remaining_seconds = self.remaining_time().total_seconds()
        progress = (total_seconds - remaining_seconds) / total_seconds
        return f"|{'█' * int(20 * progress)}{'-' * (20 - int(20 * progress))}| {int(progress * 100)}%"

    def create_embed(self, state_message=None):
        h, m, s = map(int, (self.remaining_time().total_seconds() // 3600, 
                            (self.remaining_time().total_seconds() % 3600) // 60, 
                            self.remaining_time().total_seconds() % 60))
        embed = discord.Embed(
            title=f"Verbleibende Zeit: {h:02}:{m:02}:{s:02}",
            color=self.color
        ).set_image(url=self.image_url).add_field(name="Fortschritt", value=self.progress_bar(), inline=False)

        if state_message:
            embed.add_field(name="Status", value=state_message, inline=False)
        embed.set_footer(text="Creator: [Reso](https://discord.gg/7PuGqQwgkE)")  # Klickbarer Link zum Creator
        embed.add_field(name="Nutzer", value=f"@{self.ctx.author.display_name}", inline=False)  # Nutzername mit '@'
        return embed

    async def start(self):
        self.timer_message = await self.ctx.send(embed=self.create_embed("Timer gestartet!"))
        self.update_loop.start()

    @tasks.loop(seconds=1)
    async def update_loop(self):
        if self.remaining_time().total_seconds() <= 600 and not self.reminded:
            self.color = discord.Color.red()
            await self.ctx.send(f"Reminder: Noch {self.remaining_time()} übrig!", delete_after=10)
            self.reminded = True
        if self.timer_message:
            await self.timer_message.edit(embed=self.create_embed())
        if self.remaining_time().total_seconds() <= 0:
            self.stop()
            await self.ctx.send(embed=self.create_embed(self.custom_message or "Der Timer ist abgelaufen!"))

    def stop(self):
        self.update_loop.cancel()

bot = commands.Bot(command_prefix='.', intents=discord.Intents.all(), help_command=None)
user_timers = {}

def save_timer_state():
    with open("timers.json", "w") as f:
        json.dump({k: [(t.duration, t.image_url, t.custom_message) for t in v] for k, v in user_timers.items()}, f)

def load_timer_state():
    try:
        with open("timers.json", "r") as f:
            global user_timers
            user_timers = {int(k): [TourTimer(None, *t) for t in v] for k, v in json.load(f).items()}
    except FileNotFoundError:
        pass

@bot.event
async def on_ready():
    load_timer_state()
    print(f'{bot.user.name} ist online!')

def manage_timers(user_id, timer=None, action="add"):
    if user_id not in user_timers:
        user_timers[user_id] = []
    if action == "add":
        user_timers[user_id].append(timer)
    elif action == "remove" and timer in user_timers[user_id]:
        user_timers[user_id].remove(timer)
    save_timer_state()

@bot.command(name='help')
async def help_command(ctx):
    await ctx.send("**Befehle für den Tour-Bot**\n1. `.tour <Dauer>` - Starte einen Timer (z.B. `1h`, `30m`).\n"
                   "2. `.tour stop` - Stoppe den Timer.\n3. `.timers` - Zeige alle aktiven Timer.\n"
                   "4. `.help` - Zeige Hilfe an.")

@bot.command(name='timers')
async def list_timers(ctx):
    timers = user_timers.get(ctx.author.id, [])
    if timers:
        await ctx.send(f"Aktive Timer:\n" + "\n".join(f"Timer {i + 1}: {t.remaining_time().total_seconds()} Sekunden übrig" for i, t in enumerate(timers)))
    else:
        await ctx.send("Keine aktiven Timer.")

@bot.command(aliases=['t'])
async def tour(ctx, duration_or_action: str, *, message: str = None):
    await ctx.message.delete()
    user_id = ctx.author.id
    if duration_or_action.lower() == "stop":
        if not user_timers.get(user_id):
            return await ctx.send("Kein Timer läuft.", delete_after=10)
        timer = user_timers[user_id].pop()
        timer.stop()
        await ctx.send(embed=timer.create_embed("Timer gestoppt!"), delete_after=10)
        return

    try:
        duration = parse_duration(duration_or_action.lower().replace("std", "h"))
    except ValueError:
        return await ctx.send("Ungültiges Zeitformat. Nutze `h`, `m` oder `s`.", delete_after=10)

    image_url = "https://github.com/Reso1992/DmoTimer/raw/main/bandicam%202024-09-25%2022-51-53-515.jpg"
    timer = TourTimer(ctx, duration, image_url, message)
    manage_timers(user_id, timer, "add")
    await timer.start()

def parse_duration(duration_str):
    if "h" in duration_str:
        return float(duration_str.replace("h", ""))
    elif "m" in duration_str:
        return float(duration_str.replace("m", "")) / 60
    elif "s" in duration_str:
        return float(duration_str.replace("s", "")) / 3600
    else:
        raise ValueError("Ungültiges Zeitformat")

bot.run(os.getenv('DISCORD_BOT_TOKEN'))
