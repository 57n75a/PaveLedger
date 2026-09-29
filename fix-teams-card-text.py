import pathlib

def replace_once(path, old, new, label):
    p = pathlib.Path(path)
    text = p.read_text()
    count = text.count(old)
    if count != 1:
        print(f"SKIP ({count} matches, expected 1): {label} in {path}")
        return False
    p.write_text(text.replace(old, new, 1))
    print(f"OK: {label}")
    return True

replace_once('app/workspace.tsx',
    "<p>{count} active member{count===1?'':'s'}</p>",
    "<p>{count} active user{count===1?'':'s'}</p>",
    "workspace.tsx: Teams card text -> active user(s)")

print("\nDone. Now run:")
print("  npm run build")
