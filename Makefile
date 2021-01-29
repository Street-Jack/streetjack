.PHONY: test
test:
	@python3 -m unittest discover tests

.PHONY: benchmark-simulation
benchmark-simulation:
	@nosetests tests/test_simulation.py --with-timer

.PHONY: coverage
coverage:
	@nosetests --cover-erase --with-coverage --cover-package=streetjack
