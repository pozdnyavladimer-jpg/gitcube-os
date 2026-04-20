import importlib

CRITICAL = {
    "re",
    "difflib",
    "json",
    "os",
    "sys",
    "typing",
}

def check_stdlib_shadow():
    bad = []
    for name in CRITICAL:
        mod = importlib.import_module(name)
        path = getattr(mod, "__file__", "")
        if path and "/usr" not in path:
            bad.append((name, path))
    return bad

if __name__ == "__main__":
    issues = check_stdlib_shadow()
    if issues:
        print("SHADOW DETECTED:")
        for name, path in issues:
            print(name, "->", path)
    else:
        print("OK: stdlib clean")
