SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)

podman stop p-hash-db
podman rm p-hash-db
podman build -t p-hash-db "$SCRIPT_DIR"/
podman run -d -p 5432:5432 --name p-hash-db p-hash-db
