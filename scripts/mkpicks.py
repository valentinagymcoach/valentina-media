"""Erzeugt runpod/night_picks.json aus der Auswahl P (Gruppe -> Fotonamen)."""
import json, sys
P = json.loads(sys.argv[1])  # z.B. {"t_cafe":["t_cafe_2"], ...}
CROP = json.loads(sys.argv[2]) if len(sys.argv) > 2 else {}  # Fotoname -> [x,y,w]
LP = {"t_cafe": "A young woman sitting in a cafe talking naturally to the camera with lively facial expressions, natural head movements and small hand gestures, realistic, static camera",
      "t_run": "A young woman in a park after a run talking naturally to the camera, slightly out of breath, lively facial expressions, natural head movements and hand gestures, realistic, static camera",
      "t_ego": "A young woman in a gym talking confidently to the camera with a teasing smile, lively facial expressions, natural head movements and hand gestures, realistic, static camera",
      "t_morning": "A young woman on a balcony holding a coffee mug talking warmly to the camera, lively facial expressions, natural head movements, realistic, static camera"}
M = {
 "d_lake": ("life", "Static camera on a tripod. She jogs towards the camera along the lakeside promenade with a natural relaxed running stride, ponytail bouncing, arms swinging naturally, calm lake and mountains behind her."),
 "d_coffee": ("life", "Static camera. She slowly lifts the coffee mug, takes a sip, lowers it and smiles while looking out over the rooftops, a gentle breeze moves loose strands of hair."),
 "d_sunset": ("life", "Static camera on a tripod. Starting with both arms raised overhead and hands together, she slowly leans her upper body into a gentle side stretch to one side, holds it while breathing calmly, then returns to the center and stretches to the other side, feet stay planted on the mat, golden sunset light."),
 "d_walk": ("life", "Static camera on a tripod. She walks towards the camera along the cobblestone street with a relaxed confident stride, holding the iced coffee, smiling, hair moving naturally."),
 "x_hip_thrust": ("gym", "She performs slow controlled barbell hip thrusts: she lowers her hips toward the floor while her upper back stays on the bench, then drives through her heels and lifts her hips until her torso and thighs form a straight line, squeezes at the top, chin tucked, the barbell stays on her hips, feet stay flat on the floor, smooth repetitions."),
 "x_bulgarian_split_squat": ("gym", "She performs slow controlled Bulgarian split squats: her rear foot stays on the bench behind her, she bends her front knee and lowers her back knee straight down toward the floor, torso slightly forward, front foot flat on the floor, then pushes back up through her front heel, the dumbbells hang at her sides, smooth repetitions."),
 "x_one_arm_db_row": ("gym", "She performs slow controlled single-arm dumbbell rows: her back stays flat and parallel to the floor, she pulls the dumbbell up towards her hip with her elbow close to her body, squeezes her shoulder blade, then lowers it until her arm is straight, her knee and hand stay on the bench, smooth repetitions."),
 "x_leg_press": ("gym", "She performs slow controlled leg presses: she bends her knees and lowers the footplate toward her chest, her lower back stays against the backrest, then presses the footplate back up until her legs are almost straight without locking the knees, feet stay flat on the footplate, smooth repetitions."),
 "x_hammer_curl": ("gym", "She performs slow controlled dumbbell hammer curls: palms face each other the whole time with a neutral grip and thumbs pointing up, her wrists never rotate, she curls both dumbbells up towards her shoulders keeping her elbows pinned at her sides, then lowers them until her arms are straight, upper arms stay still, smooth repetitions."),
 "x_standing_calf_raise": ("gym", "She performs slow controlled standing calf raises: standing on the low step platform holding a dumbbell in each hand at her sides, both feet stay side by side, both legs stay straight, she rises high onto the balls of both feet, pauses at the top, then slowly lowers her heels back down, her feet never leave the step, no swinging, smooth repetitions."),
 "x_overhead_triceps_extension": ("gym", "She performs slow controlled overhead triceps extensions: holding a dumbbell in each hand above her head, her upper arms stay vertical next to her ears and do not move, she bends only her elbows to lower both dumbbells behind her head, then extends her arms straight up again, torso upright, smooth repetitions."),
 "x_reverse_fly": ("gym", "She performs slow controlled bent-over dumbbell reverse flyes: torso hinged forward with a flat back, slight bend in the elbows, she raises both dumbbells out to the sides up to shoulder height squeezing her shoulder blades together, then lowers them slowly, her torso stays still, smooth repetitions."),
 "x_side_plank": ("gym", "She holds a steady forearm side plank: her body stays in one straight line from head to feet, hips lifted, supporting elbow directly under her shoulder, top hand on her hip, she breathes calmly with only small natural breathing movements, no other movement."),
 "x_russian_twist": ("gym", "She performs controlled russian twists: sitting with her torso leaning back at about 45 degrees with a straight back, knees bent and heels on the floor, holding a weight plate with both hands, she rotates her torso from side to side bringing the plate beside each hip, smooth repetitions."),
}
jobs = []
for g in ("t_cafe", "t_run", "t_ego", "t_morning"):
    if P.get(g): jobs.append({"type": "lip", "name": f"lip_{g[2:]}", "photo": P[g][0], "audio": g, "prompt": LP[g], "seed": 7, "crop": CROP.get(P[g][0])})
for g in ("d_lake", "d_coffee", "d_sunset", "d_walk"):
    if P.get(g): jobs.append({"type": "wan", "name": f"{g}_a", "photo": P[g][0], "kind": M[g][0], "motion": M[g][1], "seed": 101})
ex = [g for g in M if g.startswith("x_")]
for g in ex:
    if P.get(g): jobs.append({"type": "wan", "name": f"{g[2:]}_a", "photo": P[g][0], "kind": "gym", "motion": M[g][1], "seed": 202})
for g in ex:  # zweite Variante (anderes Foto, falls vorhanden)
    if P.get(g): jobs.append({"type": "wan", "name": f"{g[2:]}_b", "photo": P[g][-1], "kind": "gym", "motion": M[g][1], "seed": 303})
for g in ("t_cafe", "t_run", "t_ego", "t_morning"):
    if P.get(g): jobs.append({"type": "lip", "name": f"lip_{g[2:]}_b", "photo": P[g][-1], "audio": g, "prompt": LP[g], "seed": 21, "crop": CROP.get(P[g][-1])})
for g in ("d_lake", "d_coffee", "d_sunset", "d_walk"):
    if P.get(g): jobs.append({"type": "wan", "name": f"{g}_b", "photo": P[g][-1], "kind": M[g][0], "motion": M[g][1], "seed": 404})
json.dump({"jobs": jobs}, open("/home/claude/valentina-media/runpod/night_picks.json", "w"), indent=1)
print(len(jobs), "jobs:", [j["name"] for j in jobs])
