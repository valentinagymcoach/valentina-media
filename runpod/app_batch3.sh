#!/usr/bin/env bash
# Startfotos für Langhantel-/Kabel-/Körpergewichtsübungen. Ergebnis: /workspace/ai/app/cands3.txt
A=/workspace/ai/app; mkdir -p $A; : > $A/cands3.txt
O="wearing a black sports bra and black high-waisted leggings and black training shoes, long black hair tied in a high ponytail, focused expression, modern well-lit gym with uncluttered floor, only one person in the photo, correct gym technique"
declare -A S
S[barbell_bench_press]="lying on her back on a flat weight bench, head, upper back and glutes on the bench, both feet flat on the floor, holding an olympic barbell with round weight plates straight above her chest with arms fully extended, overhand grip slightly wider than shoulder-width, wrists straight, the barbell rests above her chest, strict side view, her whole body, the whole bench and the whole barbell in frame, $O"
S[barbell_overhead_press]="standing upright, feet hip-width apart, holding an olympic barbell with round weight plates in the front rack position resting on the front of her shoulders at collarbone height, overhand grip just outside her shoulders, elbows slightly in front of the bar, chest up, core tight, side view from a 45 degree angle, her whole body and the whole barbell in frame, $O"
S[barbell_bent_over_row]="standing and hinged forward at the hips holding an olympic barbell with round weight plates, torso bent forward at about 45 degrees to the floor, back flat and straight, knees slightly bent, arms hanging straight down holding the barbell below her shoulders at knee height with an overhand grip slightly wider than shoulder-width, head neutral, strict side view, her whole body and the whole barbell in frame, $O"
S[cable_biceps_curl]="standing upright facing a cable machine, holding a short straight bar attached to the low pulley cable with both hands, underhand grip shoulder-width, arms fully extended down in front of her thighs, elbows close to her sides, the cable runs from the low pulley to the bar, strict side view, her whole body and the cable machine in frame, $O"
S[hanging_leg_raise]="hanging from a horizontal pull-up bar with fully straight arms, overhand grip shoulder-width, her feet off the floor, legs straight and together hanging down, body still and vertical, strict side view, her whole body and the pull-up bar in frame, $O"
S[forearm_plank]="holding a forearm plank on a black exercise mat on the gym floor, both forearms flat on the mat with elbows directly under her shoulders, up on her toes, body forms one straight line from head to heels, hips level not sagging and not raised, head neutral looking at the floor, strict side view from floor height, her whole body in frame, $O"
for n in barbell_bench_press barbell_overhead_press barbell_bent_over_row cable_biceps_curl hanging_leg_raise forearm_plank; do
  body=$(python3 -c 'import json,sys;print(json.dumps({"scene":sys.argv[1],"count":4,"format":"portrait"}))' "${S[$n]}")
  curl -s -m 1800 -X POST 127.0.0.1:8030/create_photos -H 'Content-Type: application/json' -d "$body" \
   | python3 -c 'import json,sys;[print(sys.argv[1],u) for u in json.load(sys.stdin)["images"]]' $n >> $A/cands3.txt
  echo "done $n"
done
echo ALL_DONE
