# Plagiarism Checker Ai

> By [MEOK AI Labs](https://meok.ai) — Check text similarity, analyze writing style consistency, verify citations, and generate originality reports. Uses n-gram analysis, stylometric features, and sequence matching.

Plagiarism Checker AI MCP Server - Text similarity, style analysis, citation checking, and originality reports.

## Installation

```bash
pip install plagiarism-checker-ai-mcp
```

## Usage

```bash
# Run standalone
python server.py

# Or via MCP
mcp install plagiarism-checker-ai-mcp
```

## Tools

### `check_text_similarity`
Compare two texts for similarity using multiple algorithms.

**Parameters:**
- `text_a` (str)
- `text_b` (str)

### `analyze_writing_style`
Detect writing style characteristics and inconsistencies. Optionally compare against a reference text.

**Parameters:**
- `text` (str)
- `reference_text` (str)

### `check_citation_completeness`
Verify that citations and references are properly formatted and complete. Styles: apa, harvard, ieee, any.

**Parameters:**
- `text` (str)
- `expected_citation_style` (str)

### `generate_originality_report`
Generate a full originality analysis report. Pass reference_texts as JSON array of strings.

**Parameters:**
- `text` (str)
- `reference_texts` (str)
- `author_name` (str)


## Authentication

Free tier: 15 calls/day. Upgrade at [meok.ai/pricing](https://meok.ai/pricing) for unlimited access.

## Links

- **Website**: [meok.ai](https://meok.ai)
- **GitHub**: [CSOAI-ORG/plagiarism-checker-ai-mcp](https://github.com/CSOAI-ORG/plagiarism-checker-ai-mcp)
- **PyPI**: [pypi.org/project/plagiarism-checker-ai-mcp](https://pypi.org/project/plagiarism-checker-ai-mcp/)

## License

MIT — MEOK AI Labs
