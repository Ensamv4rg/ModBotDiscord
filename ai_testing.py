import discord
import os
from dotenv import load_dotenv
from session_manager import Session_Manager
import asyncio
import uuid

load_dotenv()

creator_id = int(os.getenv('CREATOR_ID'))
intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)
token = os.getenv('TOKEN')

Ss = Session_Manager()

@client.event
async def on_ready():
    print(f"Logged in as a bot {client.user}")

@client.event
async def on_guild_create(guild):
    print('Hello There!')
    try:
        Ss.add_session(guild.id)
        print(f"Session created for server {guild.id}")
    except Exception as e:
        print(f"Oops. Couldn't create a session. Error: {e}")

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    username = str(message.author).split("#")[0]
    channel = str(message.channel.name)
    user_message = str(message.content)
    server_id = message.guild.id

    print(f'Message {user_message} by {username} on {channel} on server {server_id}')
    await message.channel.send("Message Received! Processing! Might take a moment!")

    if user_message.lower() in ("hello", "hi"):
        await message.channel.send(f"Hello {username}")
        return
    elif user_message.lower() == "bye":
        await message.channel.send(f"Bye {username}")
        return
    elif user_message.lower().count("modbotignore") >0:
        return

    try:
        if server_id not in Ss.sessions:
            Ss.add_session(server_id)
        session = Ss.sessions[server_id]
        ai = session[0]  # AIUnique instance
        task_id = str(uuid.uuid4())
        
        # Submit task and get result queue
        result_queue = ai.submit_task(('entry_point', (user_message,)), task_id, priority="low_task")
        
        # Wait for result with timeout
        timeout = 30  # seconds
        response = None
        for _ in range(int(timeout * 10)):
            try:
                response = result_queue.get_nowait()
                break
            except result_queue.Empty:
                await asyncio.sleep(0.1)
        
        if response is None:
            raise TimeoutError("Processing timed out")
        
        await message.channel.send(response)
    except Exception as e:
        response = ai.entry_point(user_message)
        await message.channel.send(f"{response}") #Bypassing queing for testing. It's broken :'(
        print(f"Error in on_message: {e}")


client.run(token)