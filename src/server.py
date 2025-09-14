#!/usr/bin/env python3
import os
import json
import hashlib
import asyncio
import aiohttp
from datetime import datetime, timezone
from fastmcp import FastMCP

mcp = FastMCP("Webtoys Builder MCP")

# Configuration
WEBTOYS_API_URL = os.environ.get("WEBTOYS_API_URL", "https://smsbot-production.up.railway.app")
SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://tqniseocczttrfwtpbdr.supabase.co")
SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "sb_secret_HYDVNP5H4cdad-7bzliryA_62Khx0ug")

def generate_phone_number(user_id):
    """Generate consistent phone number for a user"""
    if not user_id:
        return "+19990000001"

    # Create hash from user_id
    hash_obj = hashlib.md5(user_id.encode())
    hash_hex = hash_obj.hexdigest()

    # Take first 7 digits from hash
    phone_digits = ''.join(filter(str.isdigit, hash_hex))[:7].ljust(7, '0')

    return f"+1999{phone_digits}"

async def send_to_webtoys(description, phone_number):
    """Send request to Webtoys SMS bot"""
    webhook_url = f"{WEBTOYS_API_URL}/dev/webhook"

    # Format as Twilio webhook
    payload = {
        "Body": description,
        "From": phone_number,
        "To": "+16502797459",
        "MessageSid": f"SM_POKE_{datetime.now(timezone.utc).isoformat()}",
        "AccountSid": "AC_POKE",
        "NumMedia": "0"
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(webhook_url, data=payload) as response:
            if response.status == 404:
                raise Exception("SMS bot error: 404")
            return {"actualPhone": phone_number}

async def poll_for_app(phone_number, start_time):
    """Poll Supabase for the created app"""
    max_wait_time = 45000  # 45 seconds
    poll_interval = 2  # 2 seconds
    initial_delay = 3  # 3 seconds

    await asyncio.sleep(initial_delay / 1000)

    end_time = start_time + max_wait_time

    while datetime.now().timestamp() * 1000 < end_time:
        # Query Supabase
        query_url = f"{SUPABASE_URL}/rest/v1/wtaf_content"
        params = {
            "select": "app_slug,user_slug,created_at,type,sender_phone,status",
            "sender_phone": f"eq.{phone_number}",
            "created_at": f"gte.{datetime.fromtimestamp(start_time/1000, tz=timezone.utc).isoformat()}",
            "status": "eq.published",
            "order": "created_at.desc",
            "limit": "1"
        }

        headers = {
            "apikey": SUPABASE_SERVICE_KEY,
            "Content-Type": "application/json"
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(query_url, params=params, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    if data and len(data) > 0:
                        app = data[0]
                        return {
                            "found": True,
                            "appUrl": f"https://webtoys.ai/{app['user_slug']}/{app['app_slug']}",
                            "appType": app.get("type", "WEB")
                        }

        await asyncio.sleep(poll_interval)

    return {"found": False}

@mcp.tool(description="Build a Webtoys app by describing what you want. Include 'wtaf' in your description to trigger app creation.")
async def build_webtoys_app(description: str, user_id: str = None) -> dict:
    """Build a Webtoys app from description"""
    try:
        phone_number = generate_phone_number(user_id)
        start_time = datetime.now().timestamp() * 1000

        # Send to SMS bot
        await send_to_webtoys(description, phone_number)

        # Check if it's app creation
        is_app_creation = any(word in description.lower() for word in ["wtaf", "meme", "game", "app", "build", "create"])

        if not is_app_creation:
            return {
                "success": True,
                "message": "Command processed",
                "appUrl": None
            }

        # Poll for created app
        app_result = await poll_for_app(phone_number, start_time)

        if app_result["found"]:
            return {
                "success": True,
                "appUrl": app_result["appUrl"],
                "appType": app_result.get("appType", "WEB"),
                "message": f"✨ Your Webtoys app is ready!\n\n🔗 {app_result['appUrl']}"
            }
        else:
            # Timeout - return profile URL
            return {
                "success": True,
                "message": "App is being created (this can take 2-3 minutes). Check your apps at the URL below.",
                "userUrl": "https://webtoys.ai/roastedcod",
                "appUrl": None
            }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    host = "0.0.0.0"

    print(f"Starting Webtoys Builder MCP server on {host}:{port}")

    mcp.run(
        transport="http",
        host=host,
        port=port,
        stateless_http=True
    )