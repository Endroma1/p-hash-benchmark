#!/bin/bash
. ./db/rebuild_db.sh

echo "Reading input images"
make -C ./load_image/ >/dev/null

echo "Starting modification"
make -C ./modify_image/ >/dev/null

echo "Starting hashing"
make -C ./hash_image/ >/dev/null

echo "Starting matching"
make -C ./match_image/ >/dev/null
