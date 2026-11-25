#!/usr/bin/env bash
# Erste Serie: 6 Übungen mit vorhandenem Startfoto. Protokoll /workspace/batch1.log, am Ende BATCH_DONE.
cd /workspace
# Kopffreiheit: Startfoto oben verlängern, wenn die Bewegung über die Starthöhe hinausgeht
pad(){ ffmpeg -v error -y -i in/$1.jpg -filter_complex "[0]split[a][b];[a]crop=iw:ih*0.22:0:0,vflip,gblur=sigma=8[t];[t][b]vstack" in/$1_p.jpg && mv in/$1_p.jpg in/$1.jpg; }
[ -f in/.padded ] || { pad deadlift; pad ohp; touch in/.padded; }
for id in deadlift ohp pushdown cablerow lunge inclinedb; do bash animate_one.sh $id anim >> batch1.log 2>&1; date >> batch1.log; done
echo BATCH_DONE >> batch1.log
# Sicherheitsnetz: 3 Stunden nach Ende stoppt sich der Pod selbst, falls niemand die Ergebnisse abholt
(sleep 10800; runpodctl stop pod $RUNPOD_POD_ID) > /dev/null 2>&1 &
