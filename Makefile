# Don't forget that make must have tabs...
.DEFAULT_GOAL := help

analysis:  ## Runs the static code analysis tool
	-tox -r -eflake8

clean-pyc:  ## Cleans the environment of pyc, pyo and ~ files.
	find . -name '*.pyc' -exec rm --force {} +
	find . -name '*.pyo' -exec rm --force {} +
	find . -name '*~' -exec rm --force {} +

dev-install:  ## Installs the app in a way that modifications to the files are run easily
	pip install -e .

help:  ## Prints this help message.
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

lint:  ## Runs pylint against the application with the default config
	-pylint ./setup.py ./extended_uva_judge

test:  ## Runs the tox suite against each of the target interpreters.
	tox -r
