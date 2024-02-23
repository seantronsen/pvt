SHELL=/bin/bash

OBJS=dist

.PHONY: all clean install install-dev uninstall

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
# ARTIFACTS
##################################################
##################################################

./dist: ./src hatch
	hatch build
