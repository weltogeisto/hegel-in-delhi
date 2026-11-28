#!/bin/bash
# W22 by day (late): llama.cpp b12816 into a folder of its own beside release-b11429, and Inkling 2 Mini UD-Q4_K_M. Nothing live touched.
set -u
B=b12816
R=/home/ai/local-ai/llama/release-$B
M=/mnt/c/AI/models/Inkling-2-Mini
F=Inkling-2-Mini-UD-Q4_K_M.gguf
WANT=78fcedcf93c5d1bfe83e225513b71392bb52259be0eaa5f8899c856a2e5834ae   # HF X-Linked-ETag (sha256 of the LFS object)
mkdir -p $R/downloads $M
cd $R/downloads
for a in llama-$B-bin-ubuntu-cuda-12.8-x64.tar.gz cudart-llama-$B-bin-ubuntu-cuda-12.8-x64.tar.gz; do
  curl -fsSL --retry 5 -C - -o $a https://github.com/ggml-org/llama.cpp/releases/download/$B/$a || { echo "PREP FAIL download $a"; exit 1; }
done
cd $R
tar -xzf downloads/llama-$B-bin-ubuntu-cuda-12.8-x64.tar.gz
mkdir -p cudart-llama-$B-bin-ubuntu-cuda-12.8-x64 && tar -xzf downloads/cudart-llama-$B-bin-ubuntu-cuda-12.8-x64.tar.gz -C cudart-llama-$B-bin-ubuntu-cuda-12.8-x64
ls -la $R; find $R -maxdepth 3 -name llama-server
echo "PREP llama ok $(date +%T)"
cd $M
curl -fL --retry 10 --retry-delay 5 -C - -o $F "https://huggingface.co/unsloth/Inkling-2-Mini-GGUF/resolve/main/$F" 2>>$M/download.err || { echo "PREP FAIL model download"; exit 1; }
echo "PREP model downloaded $(date +%T) $(stat -c %s $F) bytes"
GOT=$(sha256sum $F | cut -d' ' -f1)
echo "$GOT  $F" > $M/$F.sha256
[ "$GOT" = "$WANT" ] && echo "PREP model sha256 ok $GOT" || echo "PREP FAIL sha256 $GOT != $WANT"
echo "PREP done $(date +%T)"
