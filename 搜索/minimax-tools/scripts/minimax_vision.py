#!/usr/bin/env python3
"""MiniMax Image Understanding Tool"""

import os
import sys
import json
import base64
import urllib.request
import urllib.error

def get_api_key():
    """Get MiniMax API key from config or environment."""
    key = os.environ.get('MINIMAX_API_KEY')
    if key:
        return key
    
    config_path = os.path.expanduser('~/.openclaw/agents/main/agent/models.json')
    if os.path.exists(config_path):
        with open(config_path) as f:
            config = json.load(f)
            providers = config.get('providers', {})
            if 'minimax-portal' in providers:
                key = providers['minimax-portal'].get('apiKey', '')
                if key and not key.startswith('minimax-oauth'):
                    return key
            if 'minimax' in providers:
                return providers['minimax'].get('apiKey', '')
    return None

def understand_image(image_source: str, prompt: str) -> dict:
    """Understand image using MiniMax Vision API."""
    api_key = get_api_key()
    if not api_key:
        return {"error": "MiniMax API key not found"}
    
    # Prepare image data
    if image_source.startswith(('http://', 'https://')):
        # URL - fetch the image first
        try:
            req = urllib.request.Request(image_source)
            proxy = os.environ.get('https_proxy') or os.environ.get('HTTPS_PROXY')
            if proxy:
                from urllib.parse import urlparse
                proxy_parsed = urlparse(proxy)
                req.set_proxy((proxy_parsed.hostname, proxy_parsed.port), 'https')
            with urllib.request.urlopen(req, timeout=30) as resp:
                image_data = resp.read()
            image_base64 = base64.b64encode(image_data).decode('utf-8')
            image_url = f"data:image/jpeg;base64,{image_base64}"
        except Exception as e:
            return {"error": f"Failed to fetch image: {e}"}
    elif os.path.exists(image_source):
        # Local file
        with open(image_source, 'rb') as f:
            image_data = f.read()
        image_base64 = base64.b64encode(image_data).decode('utf-8')
        image_url = f"data:image/jpeg;base64,{image_base64}"
    else:
        return {"error": f"Image source not found: {image_source}"}
    
    # Call MiniMax VLM API (Token Plan)
    url = "https://api.minimaxi.com/v1/coding_plan/vlm"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "prompt": prompt,
        "image_url": image_url
    }
    
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers=headers)
    
    proxy = os.environ.get('https_proxy') or os.environ.get('HTTPS_PROXY')
    if proxy:
        from urllib.parse import urlparse
        proxy_parsed = urlparse(proxy)
        req.set_proxy((proxy_parsed.hostname, proxy_parsed.port), 'https')
    
    try:
        with urllib.request.urlopen(req, timeout=60) as response:
            return json.loads(response.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        return {"error": f"HTTP {e.code}: {e.read().decode('utf-8')}"}
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: minimax_vision.py <image_url_or_path> <prompt>")
        sys.exit(1)
    
    image_source = sys.argv[1]
    prompt = " ".join(sys.argv[2:])
    result = understand_image(image_source, prompt)
    print(json.dumps(result, indent=2, ensure_ascii=False))
