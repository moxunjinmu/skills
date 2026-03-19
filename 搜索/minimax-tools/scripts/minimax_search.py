#!/usr/bin/env python3
"""MiniMax Web Search Tool"""

import os
import sys
import json
import urllib.request
import urllib.error

def get_api_key():
    """Get MiniMax API key from config or environment."""
    # Try environment first
    key = os.environ.get('MINIMAX_API_KEY')
    if key:
        return key
    
    # Try OpenClaw config
    config_path = os.path.expanduser('~/.openclaw/agents/main/agent/models.json')
    if os.path.exists(config_path):
        with open(config_path) as f:
            config = json.load(f)
            providers = config.get('providers', {})
            # Try minimax-portal first (newer API)
            if 'minimax-portal' in providers:
                key = providers['minimax-portal'].get('apiKey', '')
                if key and not key.startswith('minimax-oauth'):
                    return key
            # Fallback to minimax
            if 'minimax' in providers:
                return providers['minimax'].get('apiKey', '')
    
    return None

def web_search(query: str) -> dict:
    """Search the web using MiniMax API."""
    api_key = get_api_key()
    if not api_key:
        return {"error": "MiniMax API key not found"}
    
    url = "https://api.minimaxi.com/v1/coding_plan/search"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    data = json.dumps({"q": query}).encode('utf-8')
    
    req = urllib.request.Request(url, data=data, headers=headers)
    
    proxy = os.environ.get('https_proxy') or os.environ.get('HTTPS_PROXY')
    if proxy:
        # Use ProxyHandler for proper proxy support
        proxy_handler = urllib.request.ProxyHandler({'https': proxy})
        opener = urllib.request.build_opener(proxy_handler)
        urllib.request.install_opener(opener)
    
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            return json.loads(response.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        return {"error": f"HTTP {e.code}: {e.read().decode('utf-8')}"}
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: minimax_search.py <query>")
        sys.exit(1)
    
    query = " ".join(sys.argv[1:])
    result = web_search(query)
    print(json.dumps(result, indent=2, ensure_ascii=False))
