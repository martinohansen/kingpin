.PHONY: all install-deps format type-check lint test install

PYTHON = python3
SRC_DIR = src
TEST_PATTERN = *_test.py

all: format type-check lint test

install-deps:
	$(PYTHON) -m pip install --upgrade pip
	pip install black mypy ruff
	mypy --install-types --non-interactive .

format:
	black --check $(SRC_DIR)/

type-check:
	mypy $(SRC_DIR)/

lint:
	ruff check $(SRC_DIR)/

test:
	$(PYTHON) -m unittest discover $(SRC_DIR)/ "$(TEST_PATTERN)"

install:
	pip install .
