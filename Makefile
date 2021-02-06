.PHONY: test
test: unit-test integration-test

.PHONY: unit-test
unit-test:
	@echo "\033[0;33mRunning unit tests...\033[0m"
	@python3 -m unittest discover tests/unit

.PHONY: integration-test
integration-test:
	@echo "\033[0;33mRunning integration tests...\033[0m"
	@python3 -m unittest discover tests/integration

.PHONY: benchmark-simulation
benchmark-simulation:
	@echo "\033[0;33mRunning simulation tests...\033[0m"
	@nosetests tests/integration/test_simulation.py --with-timer

.PHONY: coverage
coverage:
	@nosetests --cover-erase --with-coverage --cover-package=streetjack --cover-html

.PHONY: cov-unit
cov-unit:
	@nosetests -w tests/unit --cover-erase --with-coverage --cover-package=streetjack  --cover-html

.PHONY: cov-integration
cov-integration:
	@nosetests -w tests/integration --cover-erase --with-coverage --cover-package=streetjack  --cover-html

.PHONY: fmt
fmt:
	@black . -l 120

.PHONY: lint
lint:
	@echo "\033[0;33mLinting streetjack package...\033[0m"
	@pylint streetjack --max-line-length=120 --disable=missing-docstring --disable=too-many-locals --disable=super-init-not-called
	@echo "\033[0;33mLinting tests package...\033[0m"
	@pylint tests --max-line-length=120 --disable=missing-docstring --disable=too-many-locals --disable=too-many-public-methods
