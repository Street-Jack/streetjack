# Streetjack contribution guide

## Prerequisites

You need to have installed:

- :snake: python
- pip3 and pipenv
- make
- direnv (recommended but not needed)
- git

## Contribution

### Initial setup

You'll need to install the dependencies and enter pipenv shell:

```bash
pipenv install
pipenv shell

source .envrc # If you have `direnv` installed you can just use `direnv allow`
```

### Running the tests

You can tests by using the `Makefile`:

```bash
# To run all tests.
make test

# Or separately unit and integration tests.
make unit-test
make integration-test

# To run a benchmark simulation of how long a game takes.
make benchmark-simulation

# To generate a coverage report.
make coverage

# Or separately for unit and integration tests.
make cov-unit
make cov-integration
```

### Making a commit

Before you make a commit you should definitely make sure you code is properly formatted, written according to PEP-8 and all tests are passing.

```bash
make fmt
make lint
make test
```
