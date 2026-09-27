import pathlib, re

VERSION = "2.1.3"

p = pathlib.Path('package.json')
text = p.read_text()
new_text, count = re.subn(r'"version":\s*"[^"]*"', f'"version": "{VERSION}"', text, count=1)
if count == 1:
    p.write_text(new_text)
    print(f"OK: package.json version corrected to {VERSION}")
else:
    print("SKIP: could not find a \"version\": \"...\" field in package.json at all")
