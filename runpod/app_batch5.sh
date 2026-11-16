#!/usr/bin/env bash
# Startfotos: neue Outfits + neue Übungen + Lipsync-Porträt. Ergebnis: /workspace/ai/app/cands5.txt (name url)
A=/workspace/ai/app; mkdir -p $A; : > $A/cands5.txt
G="modern premium gym with dark charcoal walls, warm accent lighting and black rubber floor, uncluttered, only one person in the photo"
OA="wearing a matching sage green seamless sports bra and sage green high-waisted seamless leggings, clean white training shoes, small gold hoop earrings, hair in a sleek braided high ponytail"
OB="wearing a white racerback sports bra, white high-waisted leggings, white training shoes, small silver hoop earrings, hair in a sleek high bun"
OC="wearing an oversized cropped heather grey hoodie, black high-waisted joggers, chunky white sneakers, thin gold necklace, hair in a high ponytail"
declare -A S N
S[front_squat]="standing upright holding a loaded olympic barbell with round plates in the front rack position resting on the front of her shoulders, fingertips under the bar, elbows pointing forward and high, feet shoulder-width apart, chest up, side view from a 45 degree angle, her whole body and the whole barbell in frame, $OA, $G, correct gym technique"
S[deadlift]="conventional barbell deadlift starting position: standing behind an olympic barbell with round plates resting on the floor, the bar over her mid-foot touching her shins, hips hinged back and knees bent, back flat, arms straight gripping the bar just outside her knees, head neutral, strict side view, whole body and the whole barbell in frame, $OA, $G, correct gym technique"
S[incline_db_press]="lying on an incline bench set at about 30 degrees, her back and head resting on the bench, feet flat on the floor, holding one dumbbell in each hand pressed straight up above her upper chest with arms extended, side view at 45 degrees, her whole body and the whole bench in frame, $OB, $G, correct gym technique"
S[face_pull]="standing upright facing a cable machine, holding a rope attachment with both hands, the cable pulley set at face height directly in front of her, arms extended forward at shoulder height, feet hip-width apart, side view, her whole body and the cable machine in frame, $OB, $G, correct gym technique"
S[talk_portrait]="sitting on a flat bench, facing the camera directly and looking into the camera with a warm confident smile, mouth closed, relaxed upright posture, hands resting on her thighs, framed from the waist up, eye-level camera, soft warm lighting, shallow depth of field, $OC, $G"
for n in talk_portrait front_squat deadlift incline_db_press face_pull; do
  c=4; [ $n = talk_portrait ] && c=6
  body=$(python3 -c 'import json,sys;print(json.dumps({"scene":sys.argv[1],"count":int(sys.argv[2]),"format":"portrait"}))' "${S[$n]}" $c)
  curl -s -m 1800 -X POST 127.0.0.1:8030/create_photos -H 'Content-Type: application/json' -d "$body" \
   | python3 -c 'import json,sys;[print(sys.argv[1],u) for u in json.load(sys.stdin)["images"]]' $n >> $A/cands5.txt
  echo "done $n"
done
echo ALL_DONE
