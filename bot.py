import discord
import logging
import json
import requests
import os
import time
from datetime import datetime
from colorama import Fore, Back,Style, init
from discord import app_commands
from discord.ext import commands
from blockcypher import simple_spend

#initializing colorama
init(autoreset=True)

#commamd for clearing the command prompt 
os.system('cls' if os.name=='nt' else 'clear')

#color variables
green = Fore.GREEN
red = Fore.RED
purple = Fore.MAGENTA
yellow = Fore.YELLOW
blue = Fore.BLUE
reset = Style.RESET_ALL
light_green = Fore.LIGHTGREEN_EX
light_red = Fore.LIGHTRED_EX
light_yellow = Fore.LIGHTYELLOW_EX
light_blue = Fore.LIGHTBLUE_EX
light_purple = Fore.LIGHTMAGENTA_EX

#———————————————————————————————————————
now = datetime.now()
current_time = now.strftime("[%H:%M:%S] | ")

#loading the config 
with open("config.json") as f:
    config = json.load(f)
headers = {
    "content-type" : "application/json"
}
#getting info from config.json
token = config["bot_token"]
owner = config["owner_ids"]
key = config["private_key"]
blockcypher_token = config["blockcypher_token"]
rate_url = "https://api.coingecko.com/api/v3/simple/price?ids=litecoin&vs_currencies=usd"
headers = {
    "content-type" : "application/json"
    }
#———————————————————————————————————————

#function to get the balance of a Ltc Address
def bal(addr):
    rate_url = "https://api.coingecko.com/api/v3/simple/price?ids=litecoin&vs_currencies=usd"
    url = f"https://api.blockcypher.com/v1/ltc/main/addrs/{addr}/balance"
    headers = {
        "content-type" : "application/json"
        }
    rate_get = requests.get(rate_url, headers=headers)
    rate_data = rate_get.json()
    rate = rate_data["litecoin"]["usd"]

    balance_get = requests.get(url, headers=headers)
    balance_data = balance_get.json()
    balance = balance_data["balance"]
    unc_bal = balance_data["unconfirmed_balance"]
    total_s = balance_data["total_sent"]
    total_r = balance_data["total_received"]
    #converting litoshis to USD and rounding it by 2
    final_bal = balance/100000000*rate
    final_balance = round(final_bal, 2)
    total_rec = total_r/100000000*rate
    total_received = round(total_rec, 2)
    total_sen = total_s/100000000*rate
    total_sent = round(total_sen, 2)
    unc_b = unc_bal/100000000*rate
    unc_balance = round(unc_b, 2)
    return final_balance, unc_balance, total_sent, total_received
    
#func to convert Usd to litoshis for transaction 
def converter(amt):
    rate_get = requests.get(url=rate_url, headers=headers)
    rate_data = rate_get.json()
    rate = rate_data["litecoin"]["usd"]
    final_amount = int((amt*100_000_000)/rate)
    return final_amount

#discord intents
intents = discord.Intents.default()
intents.message_content = True
handler = logging.FileHandler(filename='discord.log' ,encoding='UTF-8', mode='w')
bot = commands.Bot(command_prefix="!",intents=intents)
@bot.event
async def on_ready():
    print(f"{current_time}{light_green}Successfully Logged in as {bot.user.name}")
    try:
        synced = await bot.tree.sync()
        print(f"{current_time}{light_green}Slash Commands Synced: {len(synced)}")
    except Exception as e:
        print(f"{red}Slash Commands Sync Failed: {e}")

#send command to send ltc from your wallet to the address provided
@bot.tree.command(name="send", description="Sends LTC From your LTC Adress")
@app_commands.allowed_contexts(guilds=True, dms=True ,private_channels=True)
@app_commands.user_install()
@app_commands.describe(address="LTC adress of recipient",
                       amount="Amount in USD ($)")
async def send(interaction:discord.Interaction, address: str, amount: float):
    if interaction.user.id not in owner:
        await interaction.response.send_message("You Are Not Authorised!", ephemeral=True)
        return
    elif interaction.user.id in owner:
        try:
            tx_hash = simple_spend(
            from_privkey = key,
            to_address = address,
            to_satoshis = converter(amt=amount),
            coin_symbol = 'ltc',
            api_key = blockcypher_token,
            )
            print("Transaction Successful! :" , tx_hash)
            embed = discord.Embed(title="Transaction Successfull!",
                               description=f"**Amount** \n `{amount}$` \n\n **To-Address** \n `{address}` \n\n **TX-ID** \n `{tx_hash}` \n\n **Transaction Link** \n https://live.blockcypher.com/ltc/tx/{tx_hash}",
                               color=0x4EFF5A)
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            print("Transaction Failed! :" , e)
            await interaction.response.send_message(e, ephemeral=True)


#get_bal command to get the balance of the LTC address given
@bot.tree.command(name="get_bal", description="Get the balance of a LTC Adress")
@app_commands.allowed_contexts(guilds=True, dms=True ,private_channels=True)
@app_commands.user_install()
@app_commands.describe(addr="Enter LTC address")
async def get_bal(interaction:discord.Interaction, addr: str):
     try:
        balance, unc_balance, total_received, total_sent  = bal(addr=addr)
        embed = discord.Embed(title="Balance Information!",
                              description=f"**Confirmed Balance:** \n `{balance}$` \n\n **Unconfirmed Balance:** \n `{unc_balance}$` \n\n **Total Sent:** \n `{total_sent}$` \n\n **Total Received:** \n `{total_received}$`",
                              color=0x3498DB)
        await interaction.response.send_message(embed=embed)
     except Exception as f:
        await interaction.response.send_message(f)
        return
        
#ping command to check the bot's response time
@bot.tree.command(name="ping", description="Pings the bot")
@app_commands.allowed_contexts(guilds=True, dms=True ,private_channels=True)   
@app_commands.user_install()
async def ping(interaction:discord.Interaction):
    start = time.perf_counter()
    await interaction.response.send_message("Pong! 🏓")
    elapsed_ms = (time.perf_counter() - start) * 1000
    await interaction.followup.send(f"Response time: {elapsed_ms:.2f} ms")


#running the bot atlast
def run_bot():
    print(f"[1] Start The Bot")
    print(f"[2] Exit")
    choice = input("Enter your choice: ")
    if choice == '1':
        print(f"{current_time}{yellow}Starting the Bot...")
        bot.run(token, log_handler=handler, log_level=logging.DEBUG)
    elif choice == '2':
        print(f"{current_time}{light_red}Exiting...")
        exit() 
    else:
        print(f"{current_time}{light_red}Invalid Choice! Exiting...")
        exit()


run_bot()