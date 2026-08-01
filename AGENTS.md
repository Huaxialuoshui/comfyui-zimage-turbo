# AGENTS.md - comfyui-zimage-package

## Chinese File Editing Rule

When modifying any file containing Chinese characters, ALWAYS use Python. NEVER use PowerShell `Set-Content` or `>` redirection.

Reason: PowerShell `Set-Content -Encoding UTF8` adds a BOM, which corrupts Chinese characters (Mojibake). This has already damaged files in git history multiple times.

Correct:
```python
with open(path, "r", encoding="utf-8") as f:
    content = f.read()
with open(path, "w", encoding="utf-8") as f:
    f.write(content)
```

Forbidden:
- `Set-Content -Encoding UTF8`
- `Out-File -Encoding UTF8`
- `> file` / `>> file`
- `@"... "@ | Set-Content` with Chinese text in here-string
- Embedding raw Chinese in inline `python -c "..."`

Safe: Pure-ASCII `.bat` / `.json` files can use PowerShell. For Chinese text, write a `.py` script file first, then execute it.

## Post-Update Git Commands

After every substantive code/file change, always provide complete git commit + push commands at the end of your response:

```bash
cd D:\A_Study\Image\comfyui-zimage-package
git add <changed files>
git commit -m "type: short description"
git push
```

Commit format: `type: short description`. Examples:
- `docs: README update`
- `fix: Chinese encoding repair`
- `feat: new Anima workflow`

## Project Paths

- Root: `D:\A_Study\Image\comfyui-zimage-package`
- Z-Image workflows: `workflows/`
- Anima workflows: `animaWorkFlows/`
- Setup: `scripts/install.py`, `anima_setup.py`
- Prompt templates: `prompt_template_*.txt`