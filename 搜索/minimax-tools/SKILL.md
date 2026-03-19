# MiniMax Tools Skill

Provide web search and image understanding via MiniMax Token Plan API.

## Tools

### web_search
Search the web using MiniMax's search API.

**Usage:**
```
python3 ~/.openclaw/skills/minimax-tools/scripts/minimax_search.py "<query>"
```

**Environment:**
```
export MINIMAX_API_KEY="sk-cp-xxx"
export https_proxy="http://127.0.0.1:7897"
```

**Example:**
```bash
MINIMAX_API_KEY="sk-cp-xxx" https_proxy=http://127.0.0.1:7897 \
python3 ~/.openclaw/skills/minimax-tools/scripts/minimax_search.py "OpenClaw feishu streaming"
```

### understand_image
Analyze images using MiniMax's vision API.

**Usage:**
```
python3 ~/.openclaw/skills/minimax-tools/scripts/minimax_vision.py "<image_url_or_path>" "<prompt>"
```

**Example:**
```bash
MINIMAX_API_KEY="sk-cp-xxx" https_proxy=http://127.0.0.1:7897 \
python3 ~/.openclaw/skills/minimax-tools/scripts/minimax_vision.py "/path/to/image.jpg" "What's in this image?"
```

## Configuration

- API Key: `sk-cp-Ck3CeOGn00yzhmKmBR08J9asu3e3crdSscSijWwc-FbJlrkeonURBq-CtAaMk0onaD_QEMFYm3IqxB8kOt8QvKwZOAWDwxKzyg_p2YegSmwfWLRejUXa0Zo`
- Proxy: `http://127.0.0.1:7897`

## Notes

- Requires MiniMax Token Plan subscription
- Supports JPEG, PNG, WebP (max 20MB)
- API endpoints:
  - Search: `/v1/coding_plan/search`
  - Vision: `/v1/coding_plan/vlm`
