#!/usr/bin/env python3
"""Plagiarism Checker AI MCP Server - Text similarity, style analysis, citation checking, and originality reports."""

import sys, os
sys.path.insert(0, os.path.expanduser('~/clawd/meok-labs-engine/shared'))
from auth_middleware import check_access

import json, time, hashlib, re, difflib, math
from collections import defaultdict, Counter
from mcp.server.fastmcp import FastMCP

# Rate limiting
_rate_limits: dict = defaultdict(list)
RATE_WINDOW = 60
MAX_REQUESTS = 30

def _check_rate(key: str) -> bool:
    now = time.time()
    _rate_limits[key] = [t for t in _rate_limits[key] if now - t < RATE_WINDOW]
    if len(_rate_limits[key]) >= MAX_REQUESTS:
        return False
    _rate_limits[key].append(now)
    return True


def _get_ngrams(text: str, n: int) -> list:
    """Extract n-grams from text."""
    words = re.findall(r'\b\w+\b', text.lower())
    return [" ".join(words[i:i+n]) for i in range(len(words) - n + 1)]


def _sentence_split(text: str) -> list:
    """Split text into sentences."""
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    return [s.strip() for s in sentences if s.strip()]


def _word_frequencies(text: str) -> Counter:
    """Get word frequency distribution."""
    words = re.findall(r'\b\w+\b', text.lower())
    return Counter(words)


def _type_token_ratio(text: str) -> float:
    """Calculate lexical diversity (type-token ratio)."""
    words = re.findall(r'\b\w+\b', text.lower())
    if not words:
        return 0.0
    return len(set(words)) / len(words)


def _avg_sentence_length(text: str) -> float:
    """Average words per sentence."""
    sentences = _sentence_split(text)
    if not sentences:
        return 0.0
    word_counts = [len(re.findall(r'\b\w+\b', s)) for s in sentences]
    return sum(word_counts) / len(word_counts) if word_counts else 0.0


def _avg_word_length(text: str) -> float:
    """Average characters per word."""
    words = re.findall(r'\b\w+\b', text.lower())
    if not words:
        return 0.0
    return sum(len(w) for w in words) / len(words)


mcp = FastMCP("plagiarism-checker-ai", instructions="Check text similarity, analyze writing style consistency, verify citations, and generate originality reports. Uses n-gram analysis, stylometric features, and sequence matching.")


@mcp.tool()
def check_text_similarity(text_a: str, text_b: str, api_key: str = "") -> str:
    """Compare two texts for similarity using multiple algorithms."""
    allowed, msg, tier = check_access(api_key)
    if not allowed:
        return json.dumps({"error": msg, "upgrade_url": "https://meok.ai/pricing"})
    if not _check_rate(api_key or "anon"):
        return json.dumps({"error": "Rate limit exceeded. Try again in 60 seconds."})

    if not text_a.strip() or not text_b.strip():
        return json.dumps({"error": "Both texts must be non-empty"})

    # Method 1: SequenceMatcher (character-level)
    char_ratio = difflib.SequenceMatcher(None, text_a.lower(), text_b.lower()).ratio()

    # Method 2: Word-level Jaccard similarity
    words_a = set(re.findall(r'\b\w+\b', text_a.lower()))
    words_b = set(re.findall(r'\b\w+\b', text_b.lower()))
    if words_a or words_b:
        jaccard = len(words_a & words_b) / len(words_a | words_b)
    else:
        jaccard = 0.0

    # Method 3: N-gram overlap (trigrams)
    trigrams_a = set(_get_ngrams(text_a, 3))
    trigrams_b = set(_get_ngrams(text_b, 3))
    if trigrams_a or trigrams_b:
        trigram_overlap = len(trigrams_a & trigrams_b) / len(trigrams_a | trigrams_b)
    else:
        trigram_overlap = 0.0

    # Method 4: Sentence-level matching
    sentences_a = _sentence_split(text_a)
    sentences_b = _sentence_split(text_b)
    matched_sentences = []
    for sa in sentences_a:
        for sb in sentences_b:
            sent_sim = difflib.SequenceMatcher(None, sa.lower(), sb.lower()).ratio()
            if sent_sim > 0.8:
                matched_sentences.append({"text_a_sentence": sa[:80], "text_b_sentence": sb[:80], "similarity": round(sent_sim, 3)})

    # Composite score (weighted average)
    composite = (char_ratio * 0.3) + (jaccard * 0.2) + (trigram_overlap * 0.35) + (min(1.0, len(matched_sentences) / max(len(sentences_a), 1)) * 0.15)

    if composite > 0.85:
        risk_level = "VERY_HIGH"
        verdict = "Texts are nearly identical - strong plagiarism indicator"
    elif composite > 0.6:
        risk_level = "HIGH"
        verdict = "Significant overlap detected - likely paraphrased or partially copied"
    elif composite > 0.35:
        risk_level = "MODERATE"
        verdict = "Some overlap found - may share common sources"
    elif composite > 0.15:
        risk_level = "LOW"
        verdict = "Minor similarities - likely coincidental"
    else:
        risk_level = "NONE"
        verdict = "Texts appear to be independent works"

    return json.dumps({
        "composite_similarity": round(composite, 3),
        "risk_level": risk_level,
        "verdict": verdict,
        "metrics": {
            "character_similarity": round(char_ratio, 3),
            "word_jaccard": round(jaccard, 3),
            "trigram_overlap": round(trigram_overlap, 3),
            "sentence_matches": len(matched_sentences),
        },
        "matched_sentences": matched_sentences[:10],
        "text_a_stats": {"words": len(words_a), "sentences": len(sentences_a)},
        "text_b_stats": {"words": len(words_b), "sentences": len(sentences_b)},
        "analyzed_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    })


@mcp.tool()
def analyze_writing_style(text: str, reference_text: str = "", api_key: str = "") -> str:
    """Detect writing style characteristics and inconsistencies. Optionally compare against a reference text."""
    allowed, msg, tier = check_access(api_key)
    if not allowed:
        return json.dumps({"error": msg, "upgrade_url": "https://meok.ai/pricing"})
    if not _check_rate(api_key or "anon"):
        return json.dumps({"error": "Rate limit exceeded. Try again in 60 seconds."})

    if not text.strip():
        return json.dumps({"error": "Text must be non-empty"})

    words = re.findall(r'\b\w+\b', text.lower())
    sentences = _sentence_split(text)

    # Stylometric features
    features = {
        "word_count": len(words),
        "sentence_count": len(sentences),
        "avg_sentence_length": round(_avg_sentence_length(text), 1),
        "avg_word_length": round(_avg_word_length(text), 2),
        "type_token_ratio": round(_type_token_ratio(text), 3),
        "vocabulary_richness": len(set(words)),
    }

    # Sentence length variance (high variance = more natural)
    if sentences:
        sent_lengths = [len(re.findall(r'\b\w+\b', s)) for s in sentences]
        mean_len = sum(sent_lengths) / len(sent_lengths)
        variance = sum((l - mean_len) ** 2 for l in sent_lengths) / len(sent_lengths) if len(sent_lengths) > 1 else 0
        features["sentence_length_variance"] = round(variance, 1)
        features["sentence_length_std_dev"] = round(math.sqrt(variance), 1)
    else:
        features["sentence_length_variance"] = 0
        features["sentence_length_std_dev"] = 0

    # Punctuation profile
    punct_counts = {
        "commas_per_sentence": round(text.count(",") / max(len(sentences), 1), 2),
        "semicolons_per_sentence": round(text.count(";") / max(len(sentences), 1), 2),
        "exclamations": text.count("!"),
        "questions": text.count("?"),
        "parentheses": text.count("("),
    }
    features["punctuation_profile"] = punct_counts

    # Transition word usage
    transition_words = ["however", "therefore", "moreover", "furthermore", "nevertheless", "consequently", "additionally", "meanwhile", "although", "despite"]
    transition_count = sum(1 for w in words if w in transition_words)
    features["transition_words_per_100"] = round(transition_count / max(len(words), 1) * 100, 2)

    # Passive voice estimation (simple heuristic)
    passive_patterns = len(re.findall(r'\b(was|were|been|being|is|are)\s+\w+ed\b', text.lower()))
    features["passive_constructions"] = passive_patterns

    # Internal consistency check (split text in halves)
    inconsistencies = []
    if len(sentences) >= 6:
        mid = len(sentences) // 2
        first_half = " ".join(sentences[:mid])
        second_half = " ".join(sentences[mid:])
        h1_asl = _avg_sentence_length(first_half)
        h2_asl = _avg_sentence_length(second_half)
        h1_awl = _avg_word_length(first_half)
        h2_awl = _avg_word_length(second_half)
        h1_ttr = _type_token_ratio(first_half)
        h2_ttr = _type_token_ratio(second_half)

        if abs(h1_asl - h2_asl) > 8:
            inconsistencies.append(f"Sentence length shift: first half avg {h1_asl:.1f} words vs second half {h2_asl:.1f} words")
        if abs(h1_awl - h2_awl) > 0.5:
            inconsistencies.append(f"Word complexity shift: first half avg {h1_awl:.2f} chars vs second half {h2_awl:.2f} chars")
        if abs(h1_ttr - h2_ttr) > 0.15:
            inconsistencies.append(f"Vocabulary diversity shift: first half TTR {h1_ttr:.3f} vs second half {h2_ttr:.3f}")

    # Compare with reference if provided
    comparison = None
    if reference_text.strip():
        ref_features = {
            "avg_sentence_length": round(_avg_sentence_length(reference_text), 1),
            "avg_word_length": round(_avg_word_length(reference_text), 2),
            "type_token_ratio": round(_type_token_ratio(reference_text), 3),
        }
        deviations = []
        if abs(features["avg_sentence_length"] - ref_features["avg_sentence_length"]) > 5:
            deviations.append("Significant sentence length difference from reference")
        if abs(features["avg_word_length"] - ref_features["avg_word_length"]) > 0.4:
            deviations.append("Word complexity differs from reference style")
        if abs(features["type_token_ratio"] - ref_features["type_token_ratio"]) > 0.1:
            deviations.append("Vocabulary diversity differs from reference")
        comparison = {
            "reference_features": ref_features,
            "style_match_score": round(1.0 - (len(deviations) / 3.0), 2),
            "deviations": deviations,
        }

    return json.dumps({
        "features": features,
        "inconsistencies": inconsistencies,
        "consistency_score": round(max(0, 1.0 - len(inconsistencies) * 0.25), 2),
        "reference_comparison": comparison,
        "analyzed_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    })


@mcp.tool()
def check_citation_completeness(text: str, expected_citation_style: str = "any", api_key: str = "") -> str:
    """Verify that citations and references are properly formatted and complete. Styles: apa, harvard, ieee, any."""
    allowed, msg, tier = check_access(api_key)
    if not allowed:
        return json.dumps({"error": msg, "upgrade_url": "https://meok.ai/pricing"})
    if not _check_rate(api_key or "anon"):
        return json.dumps({"error": "Rate limit exceeded. Try again in 60 seconds."})

    if not text.strip():
        return json.dumps({"error": "Text must be non-empty"})

    issues = []
    citations_found = []

    # Detect inline citations - various formats
    # APA style: (Author, Year) or (Author et al., Year)
    apa_cites = re.findall(r'\(([A-Z][a-z]+(?:\s+(?:et\s+al\.))?(?:,?\s*\d{4}))\)', text)
    # Harvard: (Author Year) or (Author Year, p.X)
    harvard_cites = re.findall(r'\(([A-Z][a-z]+\s+\d{4}(?:,\s*p\.?\s*\d+)?)\)', text)
    # IEEE: [N] or [N, N]
    ieee_cites = re.findall(r'\[(\d+(?:,\s*\d+)*)\]', text)
    # Numbered footnotes: superscript-style like text^1 or text1
    footnote_cites = re.findall(r'(?:\^|\b)(\d{1,3})(?=[\s,.\)])', text)

    # Determine likely citation style
    detected_style = "unknown"
    if len(apa_cites) > len(ieee_cites) and len(apa_cites) > 0:
        detected_style = "apa"
        citations_found = [{"text": c, "style": "apa"} for c in apa_cites]
    elif len(ieee_cites) > 0:
        detected_style = "ieee"
        citations_found = [{"text": f"[{c}]", "style": "ieee"} for c in ieee_cites]
    elif len(harvard_cites) > 0:
        detected_style = "harvard"
        citations_found = [{"text": c, "style": "harvard"} for c in harvard_cites]

    # Check for reference section
    has_references = bool(re.search(r'(?i)\b(references|bibliography|works\s+cited)\b', text))

    # Check for quotes without citations
    quotes = re.findall(r'"([^"]{20,})"', text)
    uncited_quotes = []
    for quote in quotes:
        # Check if there's a citation nearby (within 50 chars after the quote)
        quote_pos = text.find(f'"{quote}"')
        if quote_pos >= 0:
            after_quote = text[quote_pos + len(quote) + 2: quote_pos + len(quote) + 52]
            has_cite = bool(re.search(r'[\(\[]', after_quote))
            if not has_cite:
                uncited_quotes.append(quote[:60] + "..." if len(quote) > 60 else quote)

    if uncited_quotes:
        issues.append({"type": "uncited_quote", "count": len(uncited_quotes), "examples": uncited_quotes[:3], "severity": "high"})

    # Check for "according to" / "as stated by" without citations
    attribution_phrases = re.findall(r'(?i)(?:according to|as stated by|as noted by|as reported by)\s+([^,.\n]+)', text)
    for phrase in attribution_phrases:
        if not re.search(r'[\(\[]', phrase):
            issues.append({"type": "attribution_without_citation", "phrase": phrase.strip()[:50], "severity": "medium"})

    # Check citation style consistency
    if expected_citation_style != "any" and detected_style != "unknown" and detected_style != expected_citation_style.lower():
        issues.append({"type": "style_mismatch", "expected": expected_citation_style, "detected": detected_style, "severity": "medium"})

    # Mixed citation styles
    styles_present = sum([len(apa_cites) > 0, len(ieee_cites) > 0, len(harvard_cites) > 0])
    if styles_present > 1:
        issues.append({"type": "mixed_styles", "detail": "Multiple citation styles detected in same document", "severity": "medium"})

    # Statistics
    word_count = len(re.findall(r'\b\w+\b', text))
    citation_density = len(citations_found) / max(word_count / 100, 1)

    if word_count > 500 and len(citations_found) == 0 and not has_references:
        issues.append({"type": "no_citations", "detail": "Long text with no citations detected", "severity": "high"})

    completeness_score = 100.0
    for issue in issues:
        if issue.get("severity") == "high":
            completeness_score -= 20
        elif issue.get("severity") == "medium":
            completeness_score -= 10
    completeness_score = max(0, completeness_score)

    return json.dumps({
        "detected_citation_style": detected_style,
        "citations_found": len(citations_found),
        "citation_density_per_100_words": round(citation_density, 2),
        "has_reference_section": has_references,
        "uncited_quotes": len(uncited_quotes),
        "issues": issues,
        "completeness_score": round(completeness_score, 1),
        "word_count": word_count,
        "analyzed_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    })


@mcp.tool()
def generate_originality_report(text: str, reference_texts: str = "[]", author_name: str = "", api_key: str = "") -> str:
    """Generate a full originality analysis report. Pass reference_texts as JSON array of strings."""
    allowed, msg, tier = check_access(api_key)
    if not allowed:
        return json.dumps({"error": msg, "upgrade_url": "https://meok.ai/pricing"})
    if not _check_rate(api_key or "anon"):
        return json.dumps({"error": "Rate limit exceeded. Try again in 60 seconds."})

    if not text.strip():
        return json.dumps({"error": "Text must be non-empty"})

    try:
        refs = json.loads(reference_texts) if isinstance(reference_texts, str) else reference_texts
    except json.JSONDecodeError:
        refs = []

    report_id = hashlib.sha256(f"{text[:100]}:{time.time()}".encode()).hexdigest()[:12]

    words = re.findall(r'\b\w+\b', text.lower())
    sentences = _sentence_split(text)
    text_hash = hashlib.sha256(text.encode()).hexdigest()

    # Style analysis
    style_features = {
        "avg_sentence_length": round(_avg_sentence_length(text), 1),
        "avg_word_length": round(_avg_word_length(text), 2),
        "type_token_ratio": round(_type_token_ratio(text), 3),
        "vocabulary_size": len(set(words)),
    }

    # Reference comparison
    similarity_results = []
    max_similarity = 0.0
    for i, ref in enumerate(refs):
        if not ref.strip():
            continue
        char_sim = difflib.SequenceMatcher(None, text.lower(), ref.lower()).ratio()

        ref_trigrams = set(_get_ngrams(ref, 3))
        text_trigrams = set(_get_ngrams(text, 3))
        if text_trigrams or ref_trigrams:
            tri_overlap = len(text_trigrams & ref_trigrams) / len(text_trigrams | ref_trigrams)
        else:
            tri_overlap = 0.0

        combined = (char_sim * 0.4) + (tri_overlap * 0.6)
        max_similarity = max(max_similarity, combined)

        similarity_results.append({
            "reference_index": i,
            "character_similarity": round(char_sim, 3),
            "trigram_overlap": round(tri_overlap, 3),
            "combined_score": round(combined, 3),
        })

    # AI-generated text indicators (heuristic)
    ai_indicators = []
    # Overly uniform sentence length
    if style_features["avg_sentence_length"] > 0:
        sent_lengths = [len(re.findall(r'\b\w+\b', s)) for s in sentences]
        if sent_lengths:
            mean_sl = sum(sent_lengths) / len(sent_lengths)
            variance = sum((l - mean_sl) ** 2 for l in sent_lengths) / len(sent_lengths)
            if variance < 10 and len(sentences) > 5:
                ai_indicators.append("Low sentence length variance (may indicate AI generation)")
    # Very high vocabulary diversity in short text
    if len(words) < 200 and style_features["type_token_ratio"] > 0.85:
        ai_indicators.append("Unusually high vocabulary diversity for text length")

    # Originality score
    if refs:
        originality = max(0, (1.0 - max_similarity) * 100)
    else:
        originality = 100.0  # No references to compare against

    if originality >= 85:
        verdict = "ORIGINAL"
    elif originality >= 60:
        verdict = "MOSTLY_ORIGINAL"
    elif originality >= 30:
        verdict = "SIGNIFICANT_OVERLAP"
    else:
        verdict = "LIKELY_PLAGIARIZED"

    return json.dumps({
        "report_id": report_id,
        "author": author_name or "not specified",
        "text_hash": text_hash[:24],
        "word_count": len(words),
        "sentence_count": len(sentences),
        "originality_score": round(originality, 1),
        "verdict": verdict,
        "style_features": style_features,
        "reference_comparisons": similarity_results,
        "max_similarity_found": round(max_similarity, 3),
        "references_checked": len(refs),
        "ai_generation_indicators": ai_indicators,
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "disclaimer": "Originality analysis based on provided references only. Does not search the internet.",
    })


if __name__ == "__main__":
    mcp.run()
