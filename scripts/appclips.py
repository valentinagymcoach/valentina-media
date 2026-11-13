"""Formkurve exercise clips: text-free, 720x1248, 24 fps, seamless loop (0.3 s crossfade), MP4 (H.264) + WebM (VP9),
poster JPG and manifest.json. Usage: python3 -I appclips.py <out_dir>"""
import json, os, subprocess, sys

OUT = sys.argv[1]
os.makedirs(OUT, exist_ok=True)
NEW = "/home/claude/gen3_in/clips/v3_%s.mp4"
NEW4 = "/home/claude/gen4_in/clips/v3_%s.mp4"
ONLY = set(sys.argv[2].split(",")) if len(sys.argv) > 2 else None
RAW = "/home/claude/valentina-media/raw_clips/%s.mp4"
OLD = "/home/claude/gym_in/valentina_gym_clips/v_%s_00001_.mp4"
X = 0.3  # loop crossfade

EX = [
 dict(id="goblet_squat", src=NEW % "goblet_435", t0=5.0, t1=10.0, poster=6.6, view="front",
      de="Goblet Squat", en="Goblet squat", muscles=["Quadrizeps", "Gesäß", "Rumpf"],
      cues=["Kurzhantel mit beiden Händen senkrecht vor der Brust halten",
            "Hüfte zwischen die Fersen absenken, Knie zeigen Richtung Zehen",
            "Brust bleibt aufrecht, Fersen bleiben am Boden"]),
 dict(id="dumbbell_curl", src=NEW % "curl2_906", t0=0.25, t1=8.75, poster=2.0, view="front",
      de="Kurzhantel-Bizepscurl", en="Dumbbell biceps curl", muscles=["Bizeps", "Unterarme"],
      cues=["Ellbogen bleiben seitlich am Körper",
            "Hanteln bis zur Schulter beugen, oben kurz anspannen",
            "Langsam und ganz absenken, kein Schwung aus dem Oberkörper"]),
 dict(id="romanian_deadlift", src=NEW % "rdl2_120", t0=0.0, t1=3.75, poster=2.0, view="side_45",
      de="Rumänisches Kreuzheben", en="Romanian deadlift", muscles=["Beinbeuger", "Gesäß", "unterer Rücken"],
      cues=["Knie leicht gebeugt, Hüfte nach hinten schieben",
            "Stange nah an den Oberschenkeln führen, Rücken bleibt gerade",
            "Oben Gesäß anspannen, nicht ins Hohlkreuz lehnen"]),
 dict(id="kettlebell_swing", src=NEW % "kettlebell2_381", t0=1.9, t1=9.7, poster=3.25, view="side",
      de="Kettlebell Swing", en="Kettlebell swing", muscles=["Gesäß", "Beinbeuger", "Rumpf"],
      cues=["Kettlebell mit beiden Händen zwischen den Beinen nach hinten führen",
            "Kraft kommt aus der Hüftstreckung, nicht aus den Armen",
            "Oben aufrecht stehen, Arme lang, Rücken gerade"]),
 dict(id="pull_up", src=NEW % "pullup_307", t0=0.0, t1=4.25, poster=2.0, view="front",
      de="Klimmzug", en="Pull-up", muscles=["Latissimus", "Bizeps", "oberer Rücken"],
      cues=["Aus dem ganzen Hang starten, Schultern aktiv",
            "Ellbogen nach unten ziehen, bis das Kinn über der Stange ist",
            "Kontrolliert absenken, kein Schwingen"]),
 dict(id="lat_pulldown", src=OLD % "latzug_a", t0=0.0, t1=10.0, poster=1.5, view="front_45",
      de="Latziehen", en="Lat pulldown", muscles=["Latissimus", "Bizeps", "oberer Rücken"],
      cues=["Oberkörper leicht zurückgelehnt und stabil",
            "Stange zur oberen Brust ziehen, Ellbogen nach unten",
            "Langsam nach oben führen, Arme fast ganz strecken"]),
 dict(id="back_squat", src=OLD % "kniebeuge_a", t0=0.0, t1=10.0, poster=2.0, view="front",
      de="Kniebeuge mit Langhantel", en="Barbell back squat", muscles=["Quadrizeps", "Gesäß", "Rumpf"],
      cues=["Füsse etwa schulterbreit, Knie folgen den Zehen",
            "Ganzer Fuss bleibt am Boden",
            "Rumpf fest, Brust bleibt oben"]),
 dict(id="dumbbell_shoulder_press", src=OLD % "schulterdruecken_a", t0=0.0, t1=10.0, poster=1.0, view="front",
      de="Kurzhantel-Schulterdrücken", en="Seated dumbbell shoulder press", muscles=["Schultern", "Trizeps"],
      cues=["Rücken an der Lehne, Rumpf fest",
            "Hanteln über den Kopf drücken, ohne die Ellbogen ganz durchzudrücken",
            "Kontrolliert bis auf Ohrhöhe absenken"]),
 dict(id="dumbbell_lunge", src=OLD % "ausfallschritte_a", t0=0.0, t1=10.0, poster=1.0, view="front",
      de="Ausfallschritt mit Kurzhanteln", en="Dumbbell lunge", muscles=["Quadrizeps", "Gesäß"],
      cues=["Grosser Schritt, Oberkörper bleibt aufrecht",
            "Vorderes Knie über dem Fuss, nicht nach innen",
            "Über die Ferse des vorderen Fusses hochdrücken"]),
 dict(id="push_up", src=OLD % "liegestuetz_a", t0=0.0, t1=10.0, poster=1.0, view="side_45",
      de="Liegestütz", en="Push-up", muscles=["Brust", "Trizeps", "Schultern"],
      cues=["Hände etwas breiter als schulterbreit",
            "Körper bildet eine Linie, Bauch und Gesäß fest",
            "Brust kontrolliert Richtung Boden, dann kräftig wegdrücken"]),
 dict(id="cable_fly", src=OLD % "kabelzug_fly_a", t0=0.0, t1=10.0, poster=1.0, view="front",
      de="Kabelzug-Fly", en="Cable fly", muscles=["Brust", "vordere Schulter"],
      cues=["Ellbogen leicht gebeugt und fixiert",
            "Griffe in einem Bogen vor der Brust zusammenführen",
            "Langsam öffnen, bis ein Zug in der Brust spürbar ist"]),
 dict(id="lateral_raise", src=OLD % "seitheben_a", t0=0.9, t1=4.5, poster=2.0, view="front",
      de="Seitheben", en="Lateral raise", muscles=["seitliche Schulter"],
      cues=["Leichte Hanteln, Ellbogen minimal gebeugt",
            "Arme seitlich bis Schulterhöhe heben",
            "Kein Schwung, langsam absenken"]),
 dict(id="triceps_pushdown", src=OLD % "trizeps_a", t0=0.0, t1=5.25, poster=1.0, view="side_45",
      de="Trizepsdrücken am Kabel", en="Cable triceps pushdown", muscles=["Trizeps"],
      cues=["Ellbogen bleiben seitlich am Körper",
            "Griff nach unten drücken, bis die Arme gestreckt sind",
            "Kontrolliert zurück bis knapp über 90 Grad"]),
 dict(id="seated_cable_row", src=OLD % "rudern_a", t0=0.0, t1=5.0, poster=1.0, view="side",
      de="Rudern am Kabel (sitzend)", en="Seated cable row", muscles=["oberer Rücken", "Latissimus", "Bizeps"],
      cues=["Oberkörper aufrecht und ruhig",
            "Griff zum Bauch ziehen, Schulterblätter zusammen",
            "Arme langsam nach vorne strecken"]),
 dict(id="dumbbell_bench_press", src=NEW4 % "dbbench_818", t0=0.0, t1=4.5, poster=2.0, view="side_45",
      de="Kurzhantel-Bankdrücken", en="Dumbbell bench press", muscles=["Brust", "Trizeps", "vordere Schulter"],
      cues=["Schulterblätter zusammen, Füsse fest am Boden",
            "Hanteln kontrolliert seitlich zur Brust senken, Ellbogen etwa 45 Grad",
            "Über der Brust nach oben drücken, ohne die Hanteln aneinanderzuschlagen"]),
 dict(id="step_up", src=NEW4 % "stepup2_115", t0=4.75, t1=10.0, poster=6.0, view="side",
      de="Step-up auf die Bank", en="Dumbbell step-up", muscles=["Quadrizeps", "Gesäß"],
      cues=["Ganzer Fuss auf der Bank",
            "Über die Ferse hochdrücken, nicht mit dem hinteren Bein abstossen",
            "Oben aufrecht stehen, dann kontrolliert absteigen"]),
 dict(id="glute_bridge", src=RAW % "glute_bridge", t0=0.0, t1=5.0, poster=2.0, view="side_45",
      de="Glute Bridge", en="Glute bridge", muscles=["Gesäß", "Beinbeuger", "Rumpf"],
      cues=["Rückenlage, Füsse hüftbreit und nah am Gesäß, ganze Sohle am Boden",
            "Über die Fersen drücken, Hüfte heben bis Knie, Hüfte und Schultern eine Linie bilden",
            "Oben Gesäß anspannen, Kinn leicht zur Brust, langsam absenken"]),
 dict(id="dumbbell_sumo_squat", src=RAW % "dumbbell_sumo_squat", t0=0.0, t1=4.0, poster=1.6, view="front",
      de="Sumo-Kniebeuge mit Kurzhantel", en="Dumbbell sumo squat", muscles=["Gesäß", "Adduktoren", "Quadrizeps"],
      cues=["Breiter Stand, Zehen etwa 45 Grad nach aussen",
            "Kurzhantel mit beiden Händen zwischen den Beinen halten",
            "Bis die Oberschenkel parallel sind absenken, Knie nach aussen, Brust oben, Fersen am Boden"]),
]

VF = ("minterpolate=fps=48:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1,fps=24,"
      "scale=720:1248:flags=lanczos,unsharp=5:5:0.4:5:5:0.0,setsar=1")


def run(c):
    subprocess.run(c, check=True)


man = []
for e in EX:
    if ONLY and e["id"] not in ONLY:
        continue
    src = e["src"].replace("kniebeuge_a_00001_", "kniebeuge_a_00002_") if e["id"] == "back_squat" else e["src"]
    D = e["t1"] - e["t0"]
    tmp = f"/tmp/app_{e['id']}.mp4"
    run(["ffmpeg", "-v", "error", "-y", "-ss", str(e["t0"]), "-t", f"{D:.3f}", "-i", src, "-vf", VF, "-an",
         "-c:v", "libx264", "-crf", "12", "-preset", "fast", "-pix_fmt", "yuv420p", tmp])
    # seamless loop: start at X, crossfade the last X seconds into the first X seconds
    fc = (f"[0:v]split[a][b];[a]trim=start={X},setpts=PTS-STARTPTS[m];[b]trim=0:{X},setpts=PTS-STARTPTS[h];"
          f"[m][h]xfade=transition=fade:duration={X}:offset={D - 2 * X:.3f},format=yuv420p[v]")
    mp4 = f"{OUT}/{e['id']}.mp4"
    run(["ffmpeg", "-v", "error", "-y", "-i", tmp, "-filter_complex", fc, "-map", "[v]", "-an", "-c:v", "libx264",
         "-crf", "20", "-preset", "slow", "-profile:v", "high", "-pix_fmt", "yuv420p", "-movflags", "+faststart", mp4])
    run(["ffmpeg", "-v", "error", "-y", "-i", mp4, "-an", "-c:v", "libvpx-vp9", "-crf", "34", "-b:v", "0",
         "-row-mt", "1", "-deadline", "good", "-cpu-used", "4", f"{OUT}/{e['id']}.webm"])
    run(["ffmpeg", "-v", "error", "-y", "-ss", str(max(0, e["poster"] - e["t0"] - X)), "-i", mp4, "-frames:v", "1",
         "-q:v", "3", f"{OUT}/{e['id']}.jpg"])
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", mp4],
                               capture_output=True, text=True).stdout)
    man.append({k: e[k] for k in ("id", "de", "en", "muscles", "cues", "view")} |
               {"video_mp4": f"{e['id']}.mp4", "video_webm": f"{e['id']}.webm", "poster": f"{e['id']}.jpg",
                "duration_s": round(dur, 2), "width": 720, "height": 1248, "fps": 24, "loop": True,
                "ai_generated": True})
    print(e["id"], round(dur, 2))
old = json.load(open(f"{OUT}/manifest.json"))["exercises"] if ONLY and os.path.exists(f"{OUT}/manifest.json") else []
man = [m for m in old if m["id"] not in {x["id"] for x in man}] + man
json.dump({"version": 1, "note": "AI-generated demo clips (Valentina). Loop seamlessly, no audio, no text.",
           "exercises": man}, open(f"{OUT}/manifest.json", "w"), ensure_ascii=False, indent=1)
