.PHONY: default coverage isort

default:
	tox

coverage:
	python3-coverage erase
	-rm -r htmlcov
	python3-coverage run --branch --source="." -m unittest discover
	python3-coverage html -d htmlcov

isort:
	isort --recursive televize.py tests
