import pathlib

p = pathlib.Path('app/workspace.tsx')
text = p.read_text()

marker = "function HeroTicket("
first = text.find(marker)
second = text.find(marker, first + 1)

if first == -1 or second == -1:
    print("ABORT: could not find two occurrences of 'function HeroTicket(' as expected. No changes made.")
else:
    removed_chunk = text[first:second]
    new_text = text[:first] + text[second:]
    p.write_text(new_text)
    print(f"OK: removed the duplicate block ({len(removed_chunk)} characters). One copy of HeroTicket and EditContractDocuments remains.")
