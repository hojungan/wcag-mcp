# WCAG 2.2 MCP Server

This is only a proof of concept creatd using Claude. Anyone is welcome to fix errors, expand, and improve from this.
An MCP (Model Context Protocol) server that gives AI deep knowledge of **WCAG 2.2 Level A and AA** — covering all 56 success criteria.  

## Tools Available

| Tool | Description |
|------|-------------|
| `lookup_criterion` | Look up any criterion by ID (e.g. `1.4.3`) — full description, how to meet, common failures |
| `list_criteria` | List criteria filtered by level (A/AA) or principle (POUR) |
| `check_color_contrast` | Check hex color pairs against AA/AAA contrast requirements |
| `audit_html` | Paste HTML and get a list of WCAG violations with fixes |
| `generate_accessible_component` | Get accessible HTML for: button, modal, form, navigation, table, alert, tabs |
| `suggest_fix` | Describe an issue in plain English, get matched criteria + fix guidance |
| `get_audit_checklist` | Get a manual testing checklist by category |

---

## Setup

### 1. Install dependencies

```bash
pip install fastmcp
```

Or with `uv`:
```bash
uv init wcag-mcp
cd wcag-mcp
uv add fastmcp
# Copy server.py here
```

### 2. Test with MCP Inspector

```bash
npx @modelcontextprotocol/inspector python server.py
```

### 3. Connect

```json
{
  "mcpServers": {
    "wcag": {
      "command": "python",
      "args": ["/absolute/path/to/server.py"]
    }
  }
}
```

---

## Example Prompts

Once connected, you can ask:

- *"Check if #767676 on #ffffff passes WCAG AA contrast"*
- *"Look up WCAG criterion 1.4.3"*
- *"Audit this HTML for accessibility issues: `<img src='logo.png'>`"*
- *"Generate an accessible modal dialog"*
- *"My button has no keyboard support — how do I fix it?"*
- *"Give me the keyboard testing checklist"*
- *"List all Level AA criteria for the Operable principle"*

---

## Coverage

- **56 criteria** total (32 Level A + 24 Level AA)
- Based on **WCAG 2.2** (October 2023), including all 9 new criteria
- Criterion 4.1.1 (Parsing) excluded — removed in WCAG 2.2

---

## Limitations

- HTML auditing covers ~30-40% of possible issues (same as all automated tools)
- Always supplement with manual keyboard testing and screen reader testing
- Color contrast check requires hex colors — doesn't parse CSS files
