.PHONY: all install-deps install list-tests test test-verbose clean

all:
	@echo usage:
	@echo   "make install-deps -> install dependencies"
	@echo   "make install      -> install the FVM"
	@echo   "make list-tests   -> list all the tests"
	@echo   "make test         -> run the tests"
	@echo   "make test-verbose -> run the tests with full stdout/stderr output"
	@echo   "make clean        -> remove temporary files"

install-deps:
	@echo Sorry, $@ is not implemented yet

install:
	@echo Sorry, $@ is not implemented yet

list-tests:
	pytest --collect-only

test:
	pytest -v

test-verbose:
	pytest -v -s

clean:
	rm -rf ./test/__pycache__
	rm -rf ./src/builder/__pycache__
