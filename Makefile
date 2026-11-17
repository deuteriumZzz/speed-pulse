PYTHON = python3
SCRIPT = speedtest_pro.py

.PHONY: install run test

install:
	$(PYTHON) -m pip install -r requirements.txt

run:
	$(PYTHON) $(SCRIPT)

test: install run
