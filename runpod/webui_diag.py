import json, sqlite3, glob, re, os
db = sqlite3.connect("/workspace/ai/open-webui/webui.db")
cfg = json.loads(db.execute("select data from config order by id desc limit 1").fetchone()[0] or "{}")
print("TOOL_SERVER:", json.dumps(cfg.get("tool_server"), ensure_ascii=False)[:600])
print("MODEL cols:", [r[1] for r in db.execute("pragma table_info(model)")])
for r in db.execute("select id, base_model_id, meta, params from model"):
    print("MODEL:", r[0], r[1], (r[2] or "")[:300], (r[3] or "")[:200])
print("USERS:", db.execute("select role, count(*) from user group by role").fetchall())
sp = glob.glob("/workspace/ai/venvs/webui/lib/python*/site-packages/open_webui")[0]
print("VERSION:", open(os.path.join(sp, "../open_webui-*")) if False else glob.glob(sp + "/../open_webui-*.dist-info"))
for f in ["utils/tools.py", "utils/middleware.py"]:
    s = open(os.path.join(sp, f)).read()
    for m in re.finditer(r'.{0,80}startswith\("server:.{0,160}', s):
        print(f, "::", m.group(0).replace("\n", " ")[:240])
