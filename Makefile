export BBOT_ENV=development
export FLASK_ENV=development
export FLASK_APP=channels.web.app

.PHONY: all clean console coverage lint lintdoc static test uml web

all:
	@echo
	@echo "Usage:"
	@echo "    make [options]"
	@echo
	@echo "Options:"
	@echo "    clean      Clean temp files"
	@echo "    console    Run console app (development mode)"
	@echo "    coverage   Create code coverage report"
	@echo "    lint       Analyze source code to flag programming errors, bugs, etc."
	@echo "    lintdoc    Analyze docstrings in the source code"
	@echo "    static     Run a static type checker"
	@echo "    test       Run unit tests"
	@echo "    uml        Create uml diagrams"
	@echo "    web        Run web app (development mode)"
	@echo

clean:
	@find . -name "*.pyc" -print0 | xargs -0 rm -rf
	@find . -name "*.pyo" -print0 | xargs -0 rm -rf

console: clean
	@python -m channels.console.app $(MAKECMDGOALS)

coverage: clean
	@rm -rf htmlcov
	@rm -rf .coverage
	@coverage run -m pytest && coverage report && coverage html

lint: clean
	@pylint --output-format=colorized --rcfile=./.pylintrc  ./bbot
	@pylint --output-format=colorized --rcfile=./.pylintrc  ./channels/console
	@pylint --output-format=colorized --rcfile=./.pylintrc  ./channels/web
	@pylint --output-format=colorized --rcfile=./.pylintrc  ./flow
	@pylint --output-format=colorized --rcfile=./.pylintrc  ./tests

lintdoc: clean
	@pep257 ./bbot
	@pep257 ./channels/console
	@pep257 ./channels/web
	@pep257 ./flow
	@pep257 ./tests

static:	clean
	@mypy --ignore-missing-imports ./bbot
	@mypy --ignore-missing-imports ./channels/console
	@mypy --ignore-missing-imports ./channels/web
	@mypy --ignore-missing-imports ./flow
	@mypy --ignore-missing-imports ./tests

test: clean
	@python -m pytest -s

uml: clean
	@pyreverse flow bbot && \
	dot -Tpng classes.dot -Nfontname=Arial -Nfontsize=10 -Efontname=Arial -Efontsize=10 -s1 -o classes.png && \
	dot -Tpng packages.dot -Nfontname=Arial -Nfontsize=10 -Efontname=Arial -Efontsize=10 -s1 -o packages.png
	@rm classes.dot packages.dot

web: clean
	@flask run

