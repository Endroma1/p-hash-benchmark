#!/bin/bash
. ./db/rebuild_db.sh

sleep 5
echo "Starting modification"
make -C ./modify_image/

echo "Starting hashing"
make -C ./hash_image/

echo "Starting matching"
make -C ./match_image/
