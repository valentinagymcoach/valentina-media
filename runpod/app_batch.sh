#!/usr/bin/env bash
# Startfoto-Kandidaten für fehlende Formkurve-Übungen. Ergebnis: /workspace/ai/app/cands.txt (name url)
A=/workspace/ai/app; mkdir -p $A; : > $A/cands.txt
O="wearing a black sports bra and black high-waisted leggings and black training shoes, long black hair tied in a high ponytail, focused expression, modern well-lit gym with uncluttered floor, only one person in the photo, correct gym technique"
declare -A S
S[glute_bridge]="lying on her back on a black exercise mat on the gym floor, knees bent at 90 degrees, both feet flat on the mat hip-width apart close to her glutes, arms flat on the mat beside her body palms down, head resting on the mat, hips resting on the mat in the starting position, strict side view from hip height, her whole body in frame, $O"
S[hip_thrust]="sitting on the gym floor with her shoulder blades resting against the long edge of a flat weight bench behind her, one heavy dumbbell resting horizontally across her hip crease held with both hands, knees bent, both feet flat on the floor hip-width apart, hips low near the floor in the starting position, strict side view, whole body and the bench in frame, $O"
S[bulgarian_split_squat]="standing in a long split stance in front of a flat weight bench, the top of her rear foot resting on the bench behind her, front foot flat on the floor far in front of the bench, torso upright, holding one dumbbell in each hand hanging at her sides, strict side view, whole body and the whole bench in frame, $O"
S[one_arm_dumbbell_row]="bent over beside a flat weight bench, her left knee and left hand resting on the bench, right foot planted on the floor, back flat and parallel to the floor, head neutral, right arm hanging straight down holding one dumbbell, strict side view, whole body and the whole bench in frame, $O"
S[leg_press]="seated in a 45 degree plate-loaded leg press machine, her back and head resting flat on the padded backrest, both feet flat on the large footplate shoulder-width apart, knees bent at 90 degrees, hands on the side handles, strict side view, her whole body and the whole machine in frame, $O"
for n in glute_bridge hip_thrust bulgarian_split_squat one_arm_dumbbell_row leg_press; do
  body=$(python3 -c 'import json,sys;print(json.dumps({"scene":sys.argv[1],"count":4,"format":"portrait"}))' "${S[$n]}")
  curl -s -m 900 -X POST 127.0.0.1:8030/create_photos -H 'Content-Type: application/json' -d "$body" \
   | python3 -c 'import json,sys;[print(sys.argv[1],u) for u in json.load(sys.stdin)["images"]]' $n >> $A/cands.txt
  echo "done $n"
done
echo ALL_DONE
