import os
import aiohttp
import asyncio
import re

async def monitor_discord_channel(token, channel_id):
    headers = {'Authorization': token, 'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0'}
    async with aiohttp.ClientSession() as session:
        last_message_id = None
        while True:
            url = f"https://discord.com/api/v9/channels/{channel_id}/messages?limit=10" + (f"&after={last_message_id}" if last_message_id else "")
            try:
                async with session.get(url, headers=headers) as response:
                    if response.status != 200:
                        print(f"Request failed: {response.status}")
                        await asyncio.sleep(3)
                        continue
                    messages = await response.json()
                    for message in reversed(messages):
                        content = message.get('content', '')
                        match = re.search(r'[a-f0-9]{32}', content, re.IGNORECASE)
                        if match:
                            code = match.group(0)
                            print(f"New code: {code}")
                            await send_webhook(session, code)
                        last_message_id = message['id']
            except Exception as e:
                print(f"Error: {str(e)}")
            await asyncio.sleep(0.2)

async def send_webhook(session, code):
    webhook_url = os.environ.get('WEBHOOK')
    if not webhook_url:
        print("Webhook URL not set")
        return
    payload = {
        "content": f"**HIKLOS CORPORATION**\n\nJoin Link: <https://roblox.com/share?code={code}&type=Server>\n`{code}`",
        "username": "Notifier",
        "allowed_mentions": {"parse": []}
    }
    try:
        async with session.post(webhook_url, json=payload) as response:
            if response.status != 204:
                print(f"Webhook failed: {response.status}")
    except Exception as e:
        print(f"Webhook error: {str(e)}")

async def main():
    token = os.environ.get('TOKEN')
    channel_id = 1429536067803021413
    if not token:
        print("TOKEN not set")
        return
    await monitor_discord_channel(token, channel_id)

if __name__ == "__main__":
    asyncio.run(main())
