#!/usr/bin/env python3
"""Check text similarity and detect potential plagiarism. — MEOK AI Labs."""
import json, os, re, hashlib, uuid as _uuid, random
from datetime import datetime, timezone
from collections import defaultdict
from mcp.server.fastmcp import FastMCP

FREE_DAILY_LIMIT = 30
_usage = defaultdict(list)
def _rl(c="anon"):
    now = datetime.now(timezone.utc)
    _usage[c] = [t for t in _usage[c] if (now-t).total_seconds() < 86400]
    if len(_usage[c]) >= FREE_DAILY_LIMIT: return json.dumps({"error": "Limit/day"})
    _usage[c].append(now); return None

mcp = FastMCP("plagiarism-checker", instructions="MEOK AI Labs — Check text similarity and detect potential plagiarism.")


@mcp.tool()
def check_similarity(text_a: str, text_b: str) -> str:
    """Check similarity between two texts using Jaccard coefficient."""
    if err := _rl(): return err
    words_a = set(text_a.lower().split())
    words_b = set(text_b.lower().split())
    intersection = words_a & words_b
    union = words_a | words_b
    score = len(intersection) / max(len(union), 1)
    return json.dumps({"similarity": round(score, 3), "shared_words": len(intersection), "classification": "high_similarity" if score > 0.7 else "moderate" if score > 0.3 else "low"}, indent=2)

@mcp.tool()
def find_common_phrases(text_a: str, text_b: str, min_length: int = 3) -> str:
    """Find common phrases between two texts."""
    if err := _rl(): return err
    words_a = text_a.lower().split()
    words_b = text_b.lower().split()
    phrases = []
    for i in range(len(words_a) - min_length + 1):
        phrase = " ".join(words_a[i:i+min_length])
        if phrase in text_b.lower():
            phrases.append(phrase)
    return json.dumps({"common_phrases": list(set(phrases))[:20], "count": len(set(phrases))}, indent=2)

if __name__ == "__main__":
    mcp.run()
