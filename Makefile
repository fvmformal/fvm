.PHONY: all install-deps install list-tests test test-verbose examples clean

all:
	@echo usage:
	@echo   "make install-deps -> install dependencies"
	@echo   "make install      -> install the FVM"
	@echo   "make list-tests   -> list all the tests"
	@echo   "make test         -> run the tests"
	@echo   "make test-verbose -> run the tests with full stdout/stderr output"
	@echo   "make examples     -> run the examples"
	@echo   "make clean        -> remove temporary files"

install-deps:
	@echo Sorry, $@ is not implemented yet

install:
	@echo Sorry, $@ is not implemented yet

list-tests:
	pytest --collect-only

test:
	pytest -v --junit-xml="results.xml"

test-verbose:
	pytest -v -s --junit-xml="results.xml"

examplelist += 00-counter
examplelist += 01-countervunit
examplelist += 02-linearinterpolator

conceptlist += transactions

examples: $(examplelist)
concepts: $(conceptlist)

00-counter:
	python3 -m examples.00-counter.formal

01-countervunit:
	python3 -m examples.01-countervunit.formal

02-linearinterpolator:
	python3 -m examples.02-linearinterpolator.formal

transactions:
	python3 -m concepts.transactions.formal

clean:
	rm -f results.xml flex*.log vish_stacktrace.vstf modelsim.ini
	rm -rf ./*/__pycache_ ./*/*/__pycache__
	rm -rf work
	rm -rf fvm_out
