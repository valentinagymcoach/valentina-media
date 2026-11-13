#!/usr/bin/env bash
# Zweite Runde Startfotos (stehende Kurzhantel-Übungen). Ergebnis an /workspace/ai/app/cands.txt angehängt.
A=/workspace/ai/app; mkdir -p $A
O="wearing a black sports bra and black high-waisted leggings and black training shoes, long black hair tied in a high ponytail, focused expression, modern well-lit gym with uncluttered floor, only one person in the photo, correct gym technique"
declare -A S
S[bent_over_dumbbell_row]="standing and hinged forward at the hips, torso at a 45 degree angle to the floor, back flat and straight, knees slightly bent, feet hip-width apart, holding one dumbbell in each hand with arms hanging straight down below her shoulders, palms facing each other, head neutral, no bench, strict side view, full body in frame, $O"
S[dumbbell_sumo_squat]="standing upright with a wide stance, feet wider than shoulder-width and toes turned out 45 degrees, holding one heavy dumbbell vertically with both hands by its top end hanging between her legs at arm's length, chest up, strict front view, full body in frame, $O"
S[overhead_triceps_extension]="standing upright, feet hip-width apart, holding one dumbbell with both hands directly overhead with arms fully extended straight up, elbows close to her head, core tight, strict side view, full body in frame, $O"
S[hammer_curl]="standing upright, feet hip-width apart, holding one dumbbell in each hand with arms fully extended down at her sides, palms facing her thighs in a neutral grip, elbows close to her torso, strict front view, full body in frame, $O"
S[standing_calf_raise]="standing upright on the edge of a low step platform with only the balls of her feet on the edge and her heels hanging off, holding one dumbbell in each hand at her sides, legs straight, strict side view, full body and her feet clearly visible in frame, $O"
for n in bent_over_dumbbell_row dumbbell_sumo_squat overhead_triceps_extension hammer_curl standing_calf_raise; do
  body=$(python3 -c 'import json,sys;print(json.dumps({"scene":sys.argv[1],"count":3,"format":"portrait"}))' "${S[$n]}")
  curl -s -m 1800 -X POST 127.0.0.1:8030/create_photos -H 'Content-Type: application/json' -d "$body" \
   | python3 -c 'import json,sys;[print(sys.argv[1],u) for u in json.load(sys.stdin)["images"]]' $n >> $A/cands.txt
  echo "done $n"
done
echo ALL_DONE
