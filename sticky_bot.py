import discord

class StickyBot:
    def __init__(self, bot, channel, title, description, color=discord.Color.blue(), image_url=None, footer=None):
        self.bot = bot
        self.channel = channel
        self.title = title
        self.description = description
        self.color = color
        self.image_url = image_url
        self.footer = footer
        self.sticky_message = None

    def create_embed(self):
        embed = discord.Embed(
            title=self.title,
            description=self.description,
            color=self.color
        )
        if self.image_url:
            embed.set_image(url=self.image_url)
        if self.footer:
            embed.set_footer(text=self.footer)
        return embed

    async def send_or_update_sticky(self):
        embed = self.create_embed()
        if self.sticky_message:
            await self.sticky_message.delete()  # Delete the old sticky message
        self.sticky_message = await self.channel.send(embed=embed)

    async def handle_new_message(self, message):
        if message.channel == self.channel and message.id != self.sticky_message.id:
            await self.send_or_update_sticky()