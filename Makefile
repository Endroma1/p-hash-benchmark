VENV = .venv
PYTHON = $(VENV)/bin/python
DEPS = .deps_installed

$(VENV):
	python3 -m venv $(VENV)
	$(PYTHON) -m pip install -U pip

$(DEPS): requirements.txt | $(VENV)
	$(PYTHON) -m pip install -r requirements.txt
	touch $(DEPS)

run: $(DEPS) 
	$(PYTHON) -m uvicorn app:app --host 0.0.0.0 --port 8001

clean:
	rm -rf $(VENV) $(DEPS)

.PHONY: run clean
