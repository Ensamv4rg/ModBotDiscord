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
    server_id = message.guild.id if message.guild else "DM"

    if "modbotignore" in user_message.lower():
        return

    

    print(f'Message {user_message} by {username} on {channel} on server {server_id}')
    await message.channel.send("Message Received! Processing! Might take a moment!")



    if user_message.lower() in ("hello", "hi"):
        await message.channel.send(f"Hello {username}")
        return
    elif user_message.lower() == "bye":
        await message.channel.send(f"Bye {username}")
        return
    

    try:
        if server_id not in Ss.sessions:
            Ss.add_session(server_id)
        session = Ss.sessions[server_id]
        ai = session[0]  
        task_id = str(uuid.uuid4())
        
        if user_message == "clear history":
            ai.create_thread(('clear_server_history',(server_id,task_id)),priority="high_task")

            while ai.results[task_id] == "unfinished":
                await asyncio.sleep(0.1)

            await message.channel.send("Server History Cleared")
        else:
            ai.create_thread(('entry_point', (server_id,username,user_message, task_id)),priority="low_task")

            while ai.results[task_id] == "unfinished":
                await asyncio.sleep(0.1)
            
            
            response = ai.results[task_id]
            with ai.results_lock:
                ai.results.pop(task_id)
            
            await message.channel.send(response)
        
        

    except Exception as e:
        response = session[0].entry_point(server_id, username, user_message)
        await message.channel.send(f"{response}")
        print(f"Error in on_message: {e}")


client.run(token)