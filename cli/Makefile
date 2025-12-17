PYTHON ?= python3
REQ_FILE = requirements.txt
VENV_DIR = .venv
ACTIVATE = $(VENV_DIR)/bin/activate

.PHONY: run
run:
	@# create virtualenv if missing
	@test -d $(VENV_DIR) || $(PYTHON) -m venv $(VENV_DIR)
	@# install dependencies
	. $(ACTIVATE) && pip install --upgrade pip
	. $(ACTIVATE) && pip install -r $(REQ_FILE)
	@# run the app
	. $(ACTIVATE) && $(PYTHON) -m src.main

