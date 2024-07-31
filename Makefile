.PHONY: all install-deps install lint list-tests test test-verbose examples concepts coverage clean

PYTHON ?= python3

all:
	@echo usage:
	@echo   "make install-deps -> install dependencies"
	@echo   "make install      -> install the FVM"
	@echo   "make lint         -> pass pylint over the python code"
	@echo   "make list-tests   -> list all the tests"
	@echo   "make test         -> run the tests"
	@echo   "make test-verbose -> run the tests with full stdout/stderr output"
	@echo   "make concepts     -> run the concepts"
	@echo   "make examples     -> run the examples"
	@echo   "make pycoverage   -> generate code coverage report for the python code"
	@echo   "make testall      -> run the tests, concepts and examples"
	@echo   "make clean        -> remove temporary files"

install-deps:
	@echo Sorry, $@ is not implemented yet

install:
	@echo Sorry, $@ is not implemented yet

lint:
	pylint --output-format=colorized test/*.py src/*/*.py

list-tests:
	pytest --collect-only

test:
	coverage run -m pytest -v --junit-xml="results.xml"

test-verbose:
	coverage run -m pytest -v -s --junit-xml="results.xml"

examplelist += 00-counter
examplelist += 01-countervunit
examplelist += 02-linearinterpolator

conceptlist += transactions

examples: $(examplelist)
concepts: $(conceptlist)

transactions:
	$(PYTHON) -m concepts.transactions.formal

00-counter:
	$(PYTHON) -m examples.00-counter.formal

01-countervunit:
	$(PYTHON) -m examples.01-countervunit.formal

02-linearinterpolator:
	$(PYTHON) -m examples.02-linearinterpolator.formal

pycoverage:
	coverage report -m
	coverage html
	coverage xml

testall: test concepts examples

clean:
	rm -f results.xml flex*.log vish_stacktrace.vstf modelsim.ini
	rm -rf ./*/__pycache__ ./*/*/__pycache__
	rm -rf work fvm_out
	rm -rf .coverage coverage.xml htmlcov
