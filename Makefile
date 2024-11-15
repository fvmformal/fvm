.PHONY: all install lint list-tests test test-verbose concepts examples pycoverage venv clean realclean

# If packages are installed at system level, VENV can be undefined and system
# python, pip3, pylint, pytest, etc, will be executed instead of the
# executables inside the venv
VENV_DIR ?= .venv
VENV ?= . $(VENV_DIR)/bin/activate &&
PYTHON ?= python3

all:
	@echo usage:
	@echo   "make venv         -> create python virtual environment"
	@echo   "make reqs         -> install dependencies"
	@echo   "make dev-reqs     -> install development dependencies"
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
	@echo   "make realclean    -> remove temporary files and python venv"

# reqs and dev-reqs depend on a file we create inside the venv, so we can avoid
# calling "pip3 install ..." if the requirements have already been installed
reqs: $(VENV_DIR)/reqs_installed

dev-reqs: $(VENV_DIR)/dev-reqs_installed

$(VENV_DIR)/reqs_installed: .venv
	$(VENV) pip3 install -r requirements.txt -q
	touch $(VENV_DIR)/reqs_installed

$(VENV_DIR)/dev-reqs_installed: .venv
	$(VENV) pip3 install -r dev-requirements.txt -q
	touch $(VENV_DIR)/dev-reqs_installed

# Install the FVM
install:
	@echo Sorry, $@ is not implemented yet

# Lint the python code
lint: dev-reqs
	$(VENV) pylint --output-format=colorized test/*.py src/*/*.py || pylint-exit $$?

# List the tests
list-tests: reqs dev-reqs
	$(VENV) pytest --collect-only

# Run the tests
test: reqs dev-reqs
	$(VENV) coverage run -m pytest -v --junit-xml="results.xml"

# Run the tests in verbose mode
test-verbose: reqs dev-reqs
	$(VENV) coverage run -m pytest -v -s --junit-xml="results.xml"

# List with all the examples
examplelist += 00-counter
examplelist += 01-countervunit
examplelist += 02-linearinterpolator
examplelist += 04-dualcounter
examplelist += 05-uart_tx

# List with all the concepts
conceptlist += transactions_deprecated
conceptlist += parameterized_sequences
conceptlist += inheriting_vunits
conceptlist += inheriting_multiple_vunits
conceptlist += parameterized_properties
conceptlist += multiple_designs
conceptlist += symbolic_constants
conceptlist += user_defined_hdltypes
conceptlist += user_defined_hdltypes_in_package
conceptlist += user_defined_hdltypes_in_external_package
conceptlist += assert_to_assume

# examples target runs all the examples
# concept target runs all the concepts
examples: $(examplelist)
concepts: $(conceptlist)

# Print the lists, in case this is needed for debugging
list-examples:
	@echo $(examplelist)

list-concepts:
	@echo $(conceptlist)

# Generic rules to run examples and concepts
%: examples/% reqs
	$(VENV) $(PYTHON) -m examples.$@.formal

%: concepts/% reqs
	$(VENV) $(PYTHON) -m concepts.$@.formal

# Calculate python code coverage
pycoverage: dev-reqs
	$(VENV) coverage combine
	$(VENV) coverage report -m
	$(VENV) coverage html
	$(VENV) coverage xml

# Run everything
testall: test concepts examples

# Create python venv if it doesn't exist
venv: .venv

# When creating the venv, we use the system's python (we can't use the venv's
# python because it doesn't exist yet)
.venv:
	python3 -m venv .venv

# Remove generated files
clean:
	rm -f results.xml flex*.log vish_stacktrace.vstf modelsim.ini
	rm -rf ./*/__pycache__ ./*/*/__pycache__ .pytest_cache
	rm -rf work fvm_out
	rm -rf .coverage coverage.xml htmlcov
	rm -f modelsim.ini qverify.log qverify_cmds.tcl
	rm -f pylint.log pylint.txt
	rm -rf .qverify .visualizer qcache propcheck.db
	rm -f visualizer.log qverify_ui.log qverify_ui_cmds.tcl sysinfo.log
	rm -rf test/testlib
	rm -f test/test/test.vhd test/test/test2.vhd test/test/test3.vhd
	rm -f test/test/test.psl test/test/test2.psl test/test/test3.psl

# Remove venv and generated files
realclean: clean
	rm -rf .venv
