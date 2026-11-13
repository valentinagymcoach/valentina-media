import json, sqlite3, glob, re, os
db = sqlite3.connect("/workspace/ai/open-webui/webui.db")
for k, v in db.execute("select key, value from config"):
    if "tool" in k.lower() or "function_calling" in k.lower():
        print("CFG", k, "=", str(v)[:500])
print("NCFG", db.execute("select count(*) from config").fetchone())
for r in db.execute("select id, base_model_id, name, substr(meta,1,300), substr(params,1,200), is_active from model"):
    print("MODEL", r)
print("USERS", db.execute("select role, count(*) from user group by role").fetchall())
print("TOOLS", db.execute("select id, name from tool").fetchall())
sp = glob.glob("/workspace/ai/venvs/webui/lib/python*/site-packages/open_webui")[0]
seen = 0
for f in glob.glob(sp + "/**/*.py", recursive=True):
    s = open(f, errors="ignore").read()
    for m in re.finditer(r'.{0,120}"server:.{0,160}', s):
        print(os.path.relpath(f, sp), "::", m.group(0).replace("\n", " ")[:260]); seen += 1
        if seen > 12: raise SystemExit
