SHELL=/bin/bash

OBJS=dist

.PHONY: all clean install install-dev uninstall

environment:
	conda create -n pvt-dev python=3.9 -c conda-forge -y; conda activate pvt-dev && make install-dev

install-dev:
	pip install -e .

install: ./dist
	pip install ./dist

uninstall:
	pip uninstall "$$(basename $$(realpath .))"

clean:
	rm -vrf ${OBJS}

hatch:
	pip install hatch

##################################################
##################################################
# RUNNABLES
##################################################
##################################################

# todo: add the dev packages for testing in somehwhere
# - pytest
# - pytest-benchmark
# - pytest-xdist # parallel testing
# - pytest-qt
# - pytest-mock
run-tests:
	pytest -n auto --benchmark-disable

# currently segfaults.
run-benchmarks:
	pytest 
	# echo "error: recipe not implemented"
	# exit 1

##################################################
##################################################
# ARTIFACTS
##################################################
##################################################

./dist: ./src hatch
	hatch build
