import discord
import os
from dotenv import load_dotenv
from session_manager import Session_Manager
import classifier



load_dotenv()

creator_id = int(os.getenv('CREATOR_ID'))

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)
token = os.getenv('TOKEN')

@client.event
async def on_ready():
    print("Logged in as a bot {0.user}".format(client))

@client.event
async def on_message(message):
    username = str(message.author).split("#")[0]
    channel = str(message.channel.name)
    user_message = str(message.content)

    print(f'Message {user_message} by {username} on {channel} on server {message.guild.id}')

    if message.author == client.user:
        return
    else:
        await message.channel.send("Message Recieved! Processing! Might take a hot minute! DON'T SPAM!")
        if user_message.lower() == "hello" or user_message.lower() == "hi":
            await message.channel.send(f'Hello {username}')
            return
        elif user_message.lower() == "bye":
            await message.channel.send(f'Bye {username}')
        else:
            verdict = classifier.check(user_message.lower())
            if verdict == "ABOUT":
                await message.channel.send(f"""Wow, you really want to know about me. Aww shucks.
        Right, I'm bascially a hobby project created by <@{creator_id}>. My primary purpose is to read messages and classify them under labels YOU choose(still in development)
        During my final stage, I'd basically be able to perform mod actions on users if they speak about topics that are banned.
        However, right now, I'm just a terrible piece of code. Sitting on <@{creator_id}>'s local machine, held together by hopes and dreams and would lowkey fail at any moment.
        However, I trust the process.
        Also, when I'm active, please do NOT spam or send too many messages. Else you'd blow up <@{creator_id}>'s computer....I'm still being hosted locally. And <@{creator_id}> owns a potato for a PC.
        Anyway, I'm glad to be here. Multiple improvements coming soon.
        And ye, that's basically everything about me.
        If you'd like a specific feature just give a shout out to the hottest member on this server (it's <@{creator_id}>)
        Tschuss!
        """)
            elif verdict == "PROG":
                await message.channel.send(f"""I'm still in my very basic state. Although I have a database set up waiting for me. I currently have no access. The only thing I can do right now\nis..........\n\n\nto classify messages (based of static labels atm) and give a guess on what the message's about. \n\nMy secondary purpose is glazing the shit out of <@{creator_id}>....it's basically hardcoded into me..I literally do not have a choice.
                """)
            elif verdict == "ZILCH":
                await message.channel.send("Woah, that's a new one. I have no clue whatsoever what that's about.")
            elif verdict == "BS":
                await message.channel.send(f"Lol, you see that piece of crap you just wrote? It makes more sense than your entire life. Quit wasting Daddy's (<@{creator_id}>) computer resources ")
            elif verdict == "SPAM":
                await message.channel.send(f"Nigger I will send a fucking fork bomb to your IP address. Processing these queries are resource intensive. Bloody eejit.")
            else:
                await message.channel.send(f"""Here's my verdict on the message: \n'{user_message}'\n\n sent by '<@{message.author.id}>': \n{verdict}""")


@client.event 
async def on_guild_join(guild):
    #user = client.user
    await guild.text_channels[0].send(f"I was joined to {guild.name}!")
    await guild.text_channels[0].send("Hi there, :)")
    Session_Manager.add_session(server_id=guild.id)


client.run(token)