import discord
from discord.ext import commands
import wavelink
import os
from dotenv import load_dotenv
import asyncio

# Load environment variables or replace with actual values for testing
LAVALINK_HOST = os.getenv("LAVALINK_HOST")
LAVALINK_PORT = int(os.getenv("LAVALINK_PORT"))
LAVALINK_PASSWORD = os.getenv("LAVALINK_PASSWORD")

class PlayCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.queue = []
        self.volume = 0.5
        self.is_playing = False  # Track if a song is currently playing

    @commands.Cog.listener()
    async def on_ready(self):
        try:
            # Connect to Lavalink node without SSL
            await wavelink.NodePool.create_node(
                bot=self.bot,
                host=LAVALINK_HOST,
                port=LAVALINK_PORT,
                password=LAVALINK_PASSWORD,
            )
            print("Lavalink node connected successfully.")
        except Exception as e:
            print(f"Error connecting to Lavalink: {e}")

    @commands.command(name="play")
    async def play(self, ctx, *, search: str):
        """Play a song from YouTube."""
        await self.auto_play(ctx, search)

    async def auto_play(self, ctx, search):
        try:
            # Ensure user is in a voice channel
            voice_channel = ctx.author.voice.channel if ctx.author.voice else None
            if not voice_channel:
                return await ctx.send("You're not in a voice channel!", delete_after=5)

            # Connect to voice if not already connected
            vc: wavelink.Player = ctx.voice_client or await voice_channel.connect(cls=wavelink.Player)

            # Search for tracks on YouTube
            tracks = await wavelink.YouTubeTrack.search(query=search)
            if tracks:
                track = tracks[0]
                self.queue.append((track, ctx.author))
                await ctx.send(f'🎶 Added to queue: **{track.title}** by {track.author} (Requested by {ctx.author.mention})', delete_after=5)

                # Only play the next track if nothing is currently playing
                if not vc.is_playing() and len(self.queue) == 1:
                    await self.play_next(vc, ctx)
            else:
                await ctx.send("Could not find the track on YouTube. Please try another search.", delete_after=5)

        except Exception as e:
            print(f"Error during auto play: {e}")
            await ctx.send("An error occurred while trying to play the track.", delete_after=5)

    async def play_next(self, vc, ctx):
        if self.queue:
            track, requester = self.queue.pop(0)

            embed = discord.Embed(
                title="Now Playing",
                description=f"**{track.title}**",
                color=discord.Color.green()
            )
            embed.add_field(name="Author", value=track.author, inline=True)
            embed.add_field(name="Duration", value=f"{track.duration // 60000}:{(track.duration // 1000) % 60:02}", inline=True)
            embed.add_field(name="Requested By", value=requester.mention, inline=True)

            await ctx.send(embed=embed)

            # Set the player's volume and play the track
            await vc.set_volume(int(self.volume * 100))
            await vc.play(track)
            self.is_playing = True  # Set is_playing to True

            # Wait for the track to finish before calling play_next again
            while vc.is_playing():
                await asyncio.sleep(1)  # Check every second

            # Call play_next to play the next track after current track finishes
            await self.play_next(vc, ctx)
        else:
            self.is_playing = False  # Set is_playing to False
            await self.leave_after_delay(vc)

    async def leave_after_delay(self, vc):
        await asyncio.sleep(30)  # Wait for 30 seconds
        if not self.is_playing:  # Only disconnect if no song is playing
            await vc.disconnect()

    @commands.command(name="pause")
    async def pause(self, ctx):
        """Pause the currently playing track."""
        vc = ctx.voice_client
        if vc.is_playing():
            await vc.pause()
            await ctx.send("⏸️ Paused the track.", delete_after=5)
        else:
            await ctx.send("No track is currently playing.", delete_after=5)

    @commands.command(name="resume")
    async def resume(self, ctx):
        """Resume the currently paused track."""
        vc = ctx.voice_client
        if vc.is_paused():
            await vc.resume()
            await ctx.send("▶️ Resumed the track.", delete_after=5)
        else:
            await ctx.send("The track is not paused.", delete_after=5)

    @commands.command(name="stop")
    async def stop(self, ctx):
        """Stop the currently playing track and clear the queue."""
        vc = ctx.voice_client
        if vc.is_playing() or vc.is_paused():
            await vc.stop()
            self.queue.clear()  # Clear the queue
            await ctx.send("⏹️ Stopped the track and cleared the queue.", delete_after=5)
            await self.leave_after_delay(vc)  # Start the delay to leave the voice channel
        else:
            await ctx.send("No track is currently playing.", delete_after=5)

    @commands.command(name="skip")
    async def skip(self, ctx):
        """Skip the currently playing track."""
        vc = ctx.voice_client
        if vc.is_playing():
            await vc.stop()  # Stop the current track to trigger play_next
            await ctx.send("⏭️ Skipped the track.", delete_after=5)
        else:
            await ctx.send("No track is currently playing.", delete_after=5)

    @commands.command(name="queue")
    async def queue(self, ctx):
        """Show the current music queue."""
        if self.queue:
            queue_list = "\n".join([f"{idx + 1}. **{track.title}** - `{track.duration // 60000}:{(track.duration // 1000) % 60:02}`" 
                                    for idx, (track, _) in enumerate(self.queue)])
            await ctx.send(f"**Current Queue:**\n{queue_list}", delete_after=10)
        else:
            await ctx.send("The queue is currently empty.", delete_after=5)

    @commands.command(name="help")
    async def help(self, ctx):
        """Display a list of available commands."""
        help_embed = discord.Embed(
            title="Music Bot Help",
            description="Here are the commands you can use:",
            color=discord.Color.green()
        )
        help_embed.add_field(name=",play <song>", value="Play a song from YouTube.", inline=False)
        help_embed.add_field(name=",pause", value="Pause the currently playing track.", inline=False)
        help_embed.add_field(name=",resume", value="Resume the currently paused track.", inline=False)
        help_embed.add_field(name=",stop", value="Stop the currently playing track and clear the queue.", inline=False)
        help_embed.add_field(name=",skip", value="Skip the currently playing track.", inline=False)
        help_embed.add_field(name=",queue", value="Show the current music queue.", inline=False)
       
        # Add the author's name to the footer
        help_embed.set_footer(text="DYNASTIC OFFICIAL BOT")  # Change "JoY" to the actual author's name if needed

        await ctx.send(embed=help_embed)

async def setup(bot):
    await bot.add_cog(PlayCommand(bot))
