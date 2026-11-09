#!/bin/bash
# Valentina voice test (Chatterbox, open source). Outputs served on port 8000.
mkdir -p /workspace/voice/out && cd /workspace/voice
cat > serve.py <<'PY'
import http.server, functools
class H(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*'); super().end_headers()
http.server.ThreadingHTTPServer(('0.0.0.0', 8000), functools.partial(H, directory='/workspace/voice/out')).serve_forever()
PY
echo '<h3>Valentina voice: installing...</h3>' > out/index.html
nohup python serve.py > serve.log 2>&1 &
curl -sL https://raw.githubusercontent.com/valentinagymcoach/valentina-media/main/scripts/voice_gen.py -o gen.py
pip install -q chatterbox-tts > pip.log 2>&1 && echo PIP_OK >> pip.log
python gen.py > gen.log 2>&1 && echo GEN_OK >> gen.log
tail -3 gen.log
