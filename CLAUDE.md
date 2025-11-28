# Ansys Fluent Skills

Skill for looking up Ansys Fluent and PyFluent documentation.

## Quick Start

```bash
uv sync
uv run playwright install chromium
```

## Usage: WebSearch → URL → CLI Fetch

### Step 1: WebSearch (Semantic Discovery)

WebSearch finds exact sections with semantic understanding:

```
WebSearch: "site:ansyshelp.ansys.com Fluent Theory Guide SST k-omega"
# Returns: https://ansyshelp.ansys.com/.../flu_th_sec_turb_kw_sst.html
```

### Step 2: CLI Fetch (From URL)

Extract path from URL and fetch content:

```bash
uv run fluent-doc url "corp/v252/en/flu_th/flu_th_sec_turb_kw_sst.html" -o sst.txt
```

### Browse TOC

```bash
uv run fluent-doc toc --filter turbulence
uv run fluent-doc toc --guide user --filter boundary
```

## Why This Approach?

| Tool | Strength | Weakness |
|------|----------|----------|
| WebSearch | Semantic matching, synonyms | Can't fetch protected content |
| CLI `find` | Fast cached TOC lookup | Keyword-only, no semantics |
| CLI `url` | Fetches full content | Needs exact URL path |

**Best workflow**: WebSearch discovers URL → CLI fetches content

## Cached TOC References

`.claude/skills/fluent-doc/references/`:
- `theory_toc_v252.json` - Theory Guide (1585 sections)
- `user_toc_v252.json` - User's Guide (4756 sections)

## Documentation Sources

- PyFluent: fluent.docs.pyansys.com
- Ansys Help: ansyshelp.ansys.com (via CLI)
- Examples: github.com/ansys/pyfluent
