#!/usr/bin/env bash
# Ein Clip: bash animate_one.sh <id> [replace]   → /workspace/www/<id>.mp4 + Kontrollstreifen <id>.jpg
id=$1; mode=${2:-anim}; cd /workspace/Wan2.2; S=/workspace/out/${id}_$mode; rm -rf $S; mkdir -p $S
ref=/workspace/in/$id.jpg; [ -f $ref ] || ref=/workspace/in/face.jpg
if [ "$mode" = replace ]; then
  python ./wan/modules/animate/preprocess/preprocess_data.py --ckpt_path ./Wan2.2-Animate-14B/process_checkpoint --video_path /workspace/in/$id.mp4 --refer_path $ref --save_path $S --resolution_area 1280 720 --iterations 3 --k 7 --w_len 1 --h_len 1 --replace_flag > $S/pre.log 2>&1
  python generate.py --task animate-14B --ckpt_dir ./Wan2.2-Animate-14B/ --src_root_path $S --refert_num 1 --replace_flag --use_relighting_lora --save_file $S/out.mp4 > $S/gen.log 2>&1
else
  python ./wan/modules/animate/preprocess/preprocess_data.py --ckpt_path ./Wan2.2-Animate-14B/process_checkpoint --video_path /workspace/in/$id.mp4 --refer_path $ref --save_path $S --resolution_area 1280 720 --retarget_flag > $S/pre.log 2>&1
  python generate.py --task animate-14B --ckpt_dir ./Wan2.2-Animate-14B/ --src_root_path $S --refert_num 1 --save_file $S/out.mp4 > $S/gen.log 2>&1
fi
O=$(ls -t $S/*.mp4 2>/dev/null | grep -v src_ | head -1)
if [ -n "$O" ]; then cp "$O" /workspace/www/${id}_$mode.mp4; ffmpeg -v error -y -i "$O" -vf "select='not(mod(n,10))',scale=200:-1,tile=10x1" -frames:v 1 /workspace/www/${id}_$mode.jpg; echo "OK $id $mode"; else echo "FAIL $id $mode"; tail -5 $S/pre.log $S/gen.log; fi
