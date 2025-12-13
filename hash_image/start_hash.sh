SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)

. "$SCRIPT_DIR"/hash/bin/activate
python "$SCRIPT_DIR"/src/app.py
deactivate
