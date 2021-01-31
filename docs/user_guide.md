# Streetjack user guide

## Prerequisites

You need to have installed:

- :snake: python
- pip3 and pipenv

## Usage

### Initial setup

You'll need to install the dependencies and enter pipenv shell:

```bash
pipenv install
pipenv shell

source .envrc # If you have `direnv` installed you can just use `direnv allow`
```

### Training

You can create models by typing in:

```bash
python3 streetjack/runner.py train -model jacky -iter 200
```

All new models will be generated as `yml` files and saved into the `${PROJECT_ROOT}/data` directory. Every time you specify a model name that already exists it would continue training the previously created model. This gives you the comfort of stopping and contuing training whenever you want to. If anyways for some reason you want to start creating a model anew you could use the `--new` flag to destroy the old model and start learning all over from the beginning again:

```bash
python3 streetjack/runner.py train -model jacky -iter 200 --new
```

### Playing

You can play by providing an already existing model. The game would further provide you with the information you need to continue playing.

```bash
python3 streetjack/runner.py play -model dump
```
