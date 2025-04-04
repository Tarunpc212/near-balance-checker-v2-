import requests
import json
import base64
import time

# NEAR RPC API Endpoint
RPC_URL = "https://rpc.mainnet.near.org"

# HOT Token Contract Address
TOKEN_CONTRACT = "game.hot.tg"

# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN = "7417471699:AAGX0GwcVLJ4GAD1pucGMG4ZHDPeIZyC2SY"
TELEGRAM_CHAT_ID = "-1002338644571"

def send_telegram_notification(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    requests.post(url, data=data)

# ✅ Testing Addresses Only
addresses = [
    "sahileditzzz123.tg",
    "7332495255.tg",
    "5055374948.tg"
]

def get_token_decimals():
    try:
        payload = {
            "jsonrpc": "2.0",
            "id": "dontcare",
            "method": "query",
            "params": {
                "request_type": "call_function",
                "finality": "final",
                "account_id": TOKEN_CONTRACT,
                "method_name": "ft_metadata",
                "args_base64": ""
            }
        }
        response = requests.post(RPC_URL, json=payload).json()
        if "result" in response and "result" in response["result"]:
            raw_metadata = "".join(map(chr, response["result"]["result"]))
            metadata = json.loads(raw_metadata)
            return int(metadata.get("decimals", 18))
    except Exception as e:
        print(f"❌ Exception fetching token decimals: {str(e)}")
    return 18

def get_token_balance(address, decimals):
    try:
        args = {"account_id": address}
        args_base64 = base64.b64encode(json.dumps(args).encode()).decode()
        payload = {
            "jsonrpc": "2.0",
            "id": "dontcare",
            "method": "query",
            "params": {
                "request_type": "call_function",
                "finality": "final",
                "account_id": TOKEN_CONTRACT,
                "method_name": "ft_balance_of",
                "args_base64": args_base64
            }
        }
        response = requests.post(RPC_URL, json=payload).json()
        if "error" in response:
            return 0.0
        if "result" in response and "result" in response["result"]:
            raw_balance = "".join(map(chr, response["result"]["result"])).strip('"')
            return int(raw_balance) / (10**decimals)
    except Exception as e:
        print(f"❌ Exception fetching balance for {address}: {str(e)}")
    return 0.0

def generate_report():
    token_decimals = get_token_decimals()
    balances = {}
    for idx, addr in enumerate(addresses, start=1):
        balance = get_token_balance(addr, token_decimals)
        balances[addr] = balance
    report_text = "\n🔹 Updated HOT Balance 🔹\n" + "\n".join(
        f"{idx}. {addr}: {balance:.6f} HOT" for idx, (addr, balance) in enumerate(balances.items(), start=1)
    )
    send_telegram_notification(report_text)

def check_single_address(address):
    token_decimals = get_token_decimals()
    balance = get_token_balance(address, token_decimals)
    message = f"🔹 {address}: {balance:.6f} HOT"
    send_telegram_notification(message)

def handle_telegram_commands():
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates"
    last_update_id = None
    send_telegram_notification("🤖 Bot is Active! Send /checkall or /check <address> to get balances.")

    while True:
        try:
            response = requests.get(url)
            data = response.json()

            if "result" in data:
                for update in data["result"]:
                    if last_update_id is None or update["update_id"] > last_update_id:
                        last_update_id = update["update_id"]

                        if "message" in update and "text" in update["message"]:
                            chat_id = str(update["message"]["chat"]["id"])
                            message_text = update["message"]["text"].strip().lower()

                            if chat_id == TELEGRAM_CHAT_ID:
                                if message_text == "/checkall":
                                    generate_report()
                                elif message_text.startswith("/check "):
                                    address = message_text.split("/check ")[1].strip()
                                    check_single_address(address)
                                elif message_text == "/start":
                                    send_telegram_notification("✅ Bot Already Running!")
                                elif message_text == "/stop":
                                    send_telegram_notification("❌ Bot Stopped by User.")
                                    return
        except Exception as e:
            print(f"Error checking Telegram messages: {str(e)}")
        time.sleep(5)

# Start handling Telegram
handle_telegram_commands()
