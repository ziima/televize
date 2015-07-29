.PHONY: tests

tests:
	python tests/__init__.py discover

coverage:
	python-coverage erase
	-rm -r htmlcov
	python-coverage run --branch --source="." tests/__init__.py discover
	python-coverage html -d htmlcov
