from pathlib import Path

p = Path("core/execution/llm_fix_engine.py")
text = p.read_text(encoding="utf-8")

# === 1. INSERT FORBIDDEN BLOCK ===

insert_block = '''

# === 🔒 ANTI-SHADOW CORE ===
FORBIDDEN_STUB_MODULES = {
    "os","sys","re","difflib","json","math","typing","pathlib",
    "subprocess","datetime","collections","shutil","asyncio",
    "functools","itertools","traceback","tokenize","linecache",
    "urllib","argparse"
}

FORBIDDEN_IMPORT_PREFIXES = tuple(m + "." for m in FORBIDDEN_STUB_MODULES)

def is_forbidden_module(module: str) -> bool:
    module = str(module or "").strip()
    if not module:
        return True
    if module in FORBIDDEN_STUB_MODULES:
        return True
    return module.startswith(FORBIDDEN_IMPORT_PREFIXES)

def is_alias_import(line: str) -> bool:
    return " as " in line
'''

if "ANTI-SHADOW CORE" not in text:
    text = text.replace(
        "REPO_ROOT = Path(\".\")",
        "REPO_ROOT = Path(\".\")\n" + insert_block
    )

# === 2. PATCH create_stub_module ===

text = text.replace(
    "def create_stub_module(module: str, class_name: str | None = None) -> str | None:",
    "def create_stub_module(module: str, class_name: str | None = None) -> str | None:\n    module = str(module or \"\").strip().strip(\".\")\n    if not module or is_forbidden_module(module):\n        return None"
)

# === 3. PATCH find_repo_module ===

text = text.replace(
    "def find_repo_module(module: str, current_file_path: str = \"\", file_content: str = \"\") -> Optional[str]:",
    "def find_repo_module(module: str, current_file_path: str = \"\", file_content: str = \"\") -> Optional[str]:\n    module = str(module).strip()\n    if not module or is_forbidden_module(module):\n        return None"
)

# === 4. PATCH try_fix_from_import ===

text = text.replace(
    "stripped = line.strip()",
    "stripped = line.strip()\n    if is_alias_import(line):\n        return line, None"
)

text = text.replace(
    "module = parts[1]",
    "module = parts[1]\n    if is_forbidden_module(module):\n        return line, None"
)

# === 5. PATCH try_fix_plain_import ===

text = text.replace(
    "if not stripped.startswith(\"import \"):",
    "if is_alias_import(line):\n        return line, None\n\n    if not stripped.startswith(\"import \"):"
)

text = text.replace(
    "module = stripped.replace(\"import \", \"\", 1).strip()",
    "module = stripped.replace(\"import \", \"\", 1).strip()\n    if is_forbidden_module(module):\n        return line, None"
)

# === 6. FIX repo_shutil → shutil ===

text = text.replace("import repo_shutil", "import shutil")
text = text.replace("repo_shutil.copy2", "shutil.copy2")

p.write_text(text, encoding="utf-8")
print("PATCH APPLIED")
