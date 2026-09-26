import pathlib

path = 'app/api/detect/route.ts'
p = pathlib.Path(path)
text = p.read_text()

old = " const form=await req.formData();\n if(Number(form.get('revision'))!==c.row.revision)throw new AppError('Workspace changed; retry.',409);\n"
new = " const form=await req.formData();\n"

count = text.count(old)
if count != 1:
    print(f"ABORT: expected exactly 1 match, found {count}. No changes made.")
else:
    text = text.replace(old, new, 1)
    p.write_text(text)
    print("OK: removed the revision requirement from app/api/detect/route.ts")
