# Project Setup

This documentation is a step-by-step guide to setup the configuration service
locally for the first time.

## Create Virtual Environment

We are using Python3.11 in this project, so lets setup a virtual environment
using that.

```bash
python3.11 -m venv .venv
```
This will create a .venv folder and a virtual environment for further work.

Next step, activate the virtual environment using : `source .venv/bin/activate`

## Install UV

We prefer to use `uv` since its fast and have a better developer experience. So,
if you don't have `uv`, lets first install it.

```bash
pip install uv
```
This will be the last time we will be using pip.

## Intall Poetry

We like to manage our dependencies using poetry. It gives a great way to
add, remove or manage transitive dependencies and their versions.

So, lets install `poetry`.
```bash
uv pip install poetry
```

Poetry uses the `pyproject.toml` file to scan and create a lock file. We will
use `poetry` to manage and `uv` to install dependencies. You can use any
preferred method you like. All the necessary dependencies are already present in
the `requirements.txt` or `pyproject.toml` file.

We will also need an additional poetry plugin for the above workflow, so lets
set it up.
```bash
poetry self add poetry-plugin-export
poetry self update
```
Now, you can export the requirements.txt file using poetry. We have this command
already set in the `Makefile` so lets use that.

```bash
make export-requirements
```
Now, just use uv to install the necessary requirements.

```bash
uv pip install -r requirements.txt
```

## Start the service

You can start the server using the below command.

```bash
make serve
```


