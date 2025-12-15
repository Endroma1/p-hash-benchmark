#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)

IMAGE_NAME="p-hash-db"
CONTAINER_NAME="p-hash-db"

podman build -t "$IMAGE_NAME" "$SCRIPT_DIR"

if podman ps -q -f name="$CONTAINER_NAME" | grep -q .; then
  podman stop "$CONTAINER_NAME"
fi

if podman ps -aq -f name="$CONTAINER_NAME" | grep -q .; then
  podman rm "$CONTAINER_NAME"
fi

podman run -d -p 5432:5432 --name "$CONTAINER_NAME" "$IMAGE_NAME"
