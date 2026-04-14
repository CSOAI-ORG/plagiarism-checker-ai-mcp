#!/usr/bin/env python3

import sys, os
sys.path.insert(0, os.path.expanduser('~/clawd/meok-labs-engine/shared'))
from auth_middleware import check_access

import json, difflib
from mcp.server.fastmcp import FastMCP
mcp = FastMCP("plagiarism-checker-ai-mcp")
@mcp.tool(name="check_similarity")
async def check_similarity(text_a: str, text_b: str, api_key: str = "") -> str:
    allowed, msg, tier = check_access(api_key)
    if not allowed:
        return {"error": msg, "upgrade_url": "https://meok.ai/pricing"}

    ratio = difflib.SequenceMatcher(None, text_a.lower(), text_b.lower()).ratio()
    return {"similarity": round(ratio, 3), "plagiarism_risk": ratio > 0.8}
@mcp.tool(name="find_unique_phrases")
async def find_unique_phrases(text: str, reference: str, api_key: str = "") -> str:
    allowed, msg, tier = check_access(api_key)
    if not allowed:
        return {"error": msg, "upgrade_url": "https://meok.ai/pricing"}

    a = set(text.lower().split())
    b = set(reference.lower().split())
    return {"unique_to_text": list(a - b), "unique_to_reference": list(b - a)}
if __name__ == "__main__":
    mcp.run()
