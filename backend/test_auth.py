#!/usr/bin/env python3
"""Test authentication flow locally"""
import asyncio
import httpx
from config import settings

BASE_URL = "http://localhost:8000"
EMAIL = "hospital@lifelink.ai"
PASSWORD = "Hospital@123"

async def test_auth_flow():
    # Use a single client to maintain cookie state
    async with httpx.AsyncClient() as client:
        # 1. Get CSRF token
        print("1️⃣ Getting CSRF token...")
        csrf_response = await client.get(f"{BASE_URL}/auth/csrf-token")
        print(f"   Status: {csrf_response.status_code}")
        csrf_data = csrf_response.json()
        csrf_token = csrf_data.get("csrf_token")
        print(f"   CSRF Token: {csrf_token[:20]}...")

        # 2. Login
        print("\n2️⃣ Logging in...")
        login_response = await client.post(
            f"{BASE_URL}/auth/login",
            data={"username": EMAIL, "password": PASSWORD},
            headers={"X-CSRF-Token": csrf_token},
        )
        print(f"   Status: {login_response.status_code}")
        if login_response.status_code != 200:
            print(f"   Response: {login_response.text}")
            return
        login_data = login_response.json()
        print(f"   Response: {login_data}")
        
        # Check for Set-Cookie header
        cookies = login_response.cookies
        print(f"   Cookies: {dict(cookies)}")
        
        access_token = login_data.get("access_token")
        print(f"   Access Token: {access_token[:20]}...")

        # 3. Refresh token
        print("\n3️⃣ Refreshing token...")
        print(f"   Client cookies before refresh: {dict(client.cookies)}")
        refresh_response = await client.post(
            f"{BASE_URL}/auth/refresh",
            headers={"X-CSRF-Token": csrf_token},
        )
        print(f"   Status: {refresh_response.status_code}")
        refresh_data = refresh_response.json()
        print(f"   Response: {refresh_data}")

        # 4. Get user info
        print("\n4️⃣ Getting user info...")
        me_response = await client.get(
            f"{BASE_URL}/auth/me",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        print(f"   Status: {me_response.status_code}")
        me_data = me_response.json()
        print(f"   User: {me_data.get('email')}")

asyncio.run(test_auth_flow())
