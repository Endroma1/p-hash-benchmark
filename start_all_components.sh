#!/bin/bash
. ./db/rebuild_db.sh

sleep 5
echo "Starting modification"
. ./modify_image/start_modify.sh

echo "Starting hashing"
. ./hash_image/start_hash.sh

echo "Starting matching"
. ./match_image/start_match.sh
