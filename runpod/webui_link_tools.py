"""Verknüpft Qwen in Open WebUI fest mit den Valentina-Werkzeugen (ohne Login, direkt in der DB).
Danach Open WebUI neu starten."""
import json, sqlite3, sys, time, uuid

MODEL = sys.argv[1] if len(sys.argv) > 1 else "qwen3.8:27b"
NAME = sys.argv[2] if len(sys.argv) > 2 else "Qwen 3.8 · Valentina"
SYSTEM = ("Du bist die Produktionszentrale für Valentina (@valentina_gymcoach), eine offen KI-generierte Fitness-Coachin. "
          "Du hast Werkzeuge: create_photos (Fotos mit Valentinas LoRA), create_video (Bild animieren, läuft im Hintergrund, "
          "Status mit get_job), speak (Valentinas Stimme), browse (Web-Recherche). Nutze sie direkt, statt zu sagen, dass du es nicht kannst. "
          "Zeige Bilder als Markdown ![](url), Videos und Audio als Link. Inhalte bleiben Instagram-tauglich (sportlich, nicht sexualisiert). "
          "Antworte auf Deutsch, kurz.")

db = sqlite3.connect("/workspace/ai/open-webui/webui.db")
cols = {r[1]: (r[2], r[3]) for r in db.execute("pragma table_info(model)")}
print("cols", cols)
admin = db.execute("select id from user where role='admin' limit 1").fetchone()[0]
now = int(time.time())
meta = {"profile_image_url": "/static/favicon.png", "description": "Valentina-Steuerzentrale (Fotos, Video, Stimme, Browser)",
        "capabilities": {"vision": True, "file_upload": True, "citations": True},
        "toolIds": ["server:valentina"]}
params = {"function_calling": "native", "system": SYSTEM}
row = {"id": MODEL, "user_id": admin, "base_model_id": None, "name": NAME,
       "params": json.dumps(params, ensure_ascii=False), "meta": json.dumps(meta, ensure_ascii=False),
       "updated_at": now, "created_at": now, "is_active": 1}
if "version_id" in cols:
    row["version_id"] = None if not cols["version_id"][1] else str(uuid.uuid4())
db.execute("delete from model where id=?", (MODEL,))
db.execute(f"insert into model ({','.join(row)}) values ({','.join('?' * len(row))})", list(row.values()))
db.commit()
print("OK", db.execute("select id, name from model").fetchall())
