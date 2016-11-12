.PHONY: test coverage isort check-isort check-flake8

test:
	python3 -m unittest discover

coverage:
	python3-coverage erase
	-rm -r htmlcov
	python3-coverage run --branch --source="." -m unittest discover
	python3-coverage html -d htmlcov

isort:
	isort --recursive televize.py tests

check-isort:
	isort --check-only --diff --recursive televize.py tests

check-flake8:
	flake8 --format=pylint televize.py tests
