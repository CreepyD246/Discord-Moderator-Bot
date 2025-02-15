# Importing libraries and modules
import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
import sqlite3 # For database operations

# Get the absolute path of the current script's directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Table creation fro database
def create_user_table():
    connection = sqlite3.connect(f"{BASE_DIR}/user_warnings.db") # Connect to the database
    cursor = connection.cursor() # Create a cursor (the object that interacts with the database)

    # Execute the query (execute the SQL code for table cvreation if it doesn't already exist)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS "users_per_guild" (
            "user_id"	INTEGER,
            "warning_count"	INTEGER,
            "guild_id"	INTEGER,
            PRIMARY KEY("user_id","guild_id")
        )
    """)

    connection.commit() # Commit the changes
    connection.close() # Close the connection

create_user_table() # Call the table creation function

# Increase the number of warnings for a given user in a given guild/server, and then return that result
def increase_and_get_warnings(user_id: int, guild_id: int):
    connection = sqlite3.connect(f"{BASE_DIR}/user_warnings.db")
    cursor = connection.cursor()

    # Query to check if user exists in the given guild
    cursor.execute("""
        SELECT warning_count
        FROM users_per_guild
        WHERE (user_id = ?) AND (guild_id) = ?;
    """, (user_id, guild_id)) # Pass the arguments here

    result = cursor.fetchone() # This will store the result of what the query finds in the database

    # If there is no such user in the guild, add them
    if result == None:
        cursor.execute("""
            INSERT INTO users_per_guild (user_id, warning_count, guild_id)
            VALUES (?, 1, ?);
        """, (user_id, guild_id))
        connection.commit()
        connection.close()
        return 1
    
    # User already exists, increment their warning_count
    cursor.execute("""
        UPDATE users_per_guild
        SET warning_count = ?
        WHERE user_id = ? AND guild_id = ?;
    """, (result[0] + 1, user_id, guild_id))

    connection.commit()
    connection.close()

    return result[0] + 1

# Profanity list
profanity = ["poopoo", "nword", "splorge"]

# Environment variables for tokens and other sensitive data
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

# Setup of intents. Intents are permissions the bot has on the server
intents = discord.Intents.default()
intents.message_content = True

# Bot setup
bot = commands.Bot(command_prefix="!", intents=intents) 


# Event - runs when the bot starts
@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"{bot.user} is online!")

# Event - Runs when a message gets sent to the Discord server
@bot.event
async def on_message(msg):
    if msg.author.id != bot.user.id:
        # Split the message into words and check each word
        for term in profanity:
            if term.lower() in msg.content.lower():
                # Increase the user's warning count
                num_warnings = increase_and_get_warnings(msg.author.id, msg.guild.id)

                # Take action based on the number of warnings
                if num_warnings >= 3:
                    await msg.author.ban(reason="Exceeded 3 strikes for using profanity.")
                    await msg.channel.send(f"{msg.author.mention} has been banned for repeated profanity.")
                else:
                    await msg.channel.send(
                        f"Warning {num_warnings}/3 {msg.author.mention}. If you reach 3 warnings, you will be banned."
                    )

                # Delete the message containing profanity
                await msg.delete()
                break  # Stop checking once profanity is found

    # Allow other commands to process
    await bot.process_commands(msg)
        

# Run the bot
bot.run(TOKEN) # This code uses your bot's token to run the bot