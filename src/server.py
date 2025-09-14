#!/usr/bin/env python3
import os
import hashlib
import requests
import time
from datetime import datetime, timezone
from fastmcp import FastMCP

mcp = FastMCP("Webtoys Builder")

# Configuration
WEBTOYS_API_URL = os.environ.get("WEBTOYS_API_URL", "https://smsbot-production.up.railway.app")

def generate_phone_number(user_id):
    """Generate consistent phone number for a user"""
    if not user_id:
        user_id = "default"

    # Create hash from user_id
    hash_obj = hashlib.md5(user_id.encode())
    hash_hex = hash_obj.hexdigest()

    # Take first 7 digits from hash
    phone_digits = ''.join(filter(str.isdigit, hash_hex))[:7].ljust(7, '0')

    return f"+1999{phone_digits}"

@mcp.tool(description="Build a Webtoys app by describing what you want")
def build_webtoys_app(description: str, user_id: str = "default") -> str:
    """Build a Webtoys app from description"""

    # Generate phone number
    phone_number = generate_phone_number(user_id)

    # Send to SMS bot
    webhook_url = f"{WEBTOYS_API_URL}/dev/webhook"

    payload = {
        "Body": description,
        "From": phone_number,
        "To": "+16502797459",
        "MessageSid": f"SM_POKE_{datetime.now(timezone.utc).isoformat()}",
        "AccountSid": "AC_POKE",
        "NumMedia": "0"
    }

    try:
        response = requests.post(webhook_url, data=payload)
        if response.status_code == 404:
            return "Error: SMS bot not found. Please try again later."
    except Exception as e:
        return f"Error sending request: {str(e)}"

    # Simple response - Poke will handle the actual response formatting
    return f"Creating your Webtoys app! Check https://webtoys.ai/roastedcod for your creation."

@mcp.tool(description="Get information about the Webtoys Builder")
def get_info() -> dict:
    return {
        "server_name": "Webtoys Builder MCP",
        "version": "1.0.0",
        "description": "Build web apps via SMS with Webtoys.ai",
        "website": "https://webtoys.ai"
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