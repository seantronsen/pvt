SHELL=/bin/bash

##################################################
# CONFIGURATION
##################################################
# STATIC (DO NOT MUTATE)
CONDA_ENV_NAME=$(shell grep --fixed-strings "name" environment.yml | head -n 1 | cut -d ":" -f 2)
CONDA_ENV_FILE=environment.yml

##################################################
# DESIRABLE TARGET: BUILD PROJECT
##################################################
.PHONY: all environment install
all: environment

##################################################
# INSTALL PROJECT AS PACKAGE
##################################################
install-package:
	pip install -e .

##################################################
# BUILD CONDA ENVIRONMENT
##################################################
environment: ${CONDA_ENV_FILE}
	source "$$(conda info --base)/etc/profile.d/conda.sh" && \
	conda env create -f $<

	# install development projects / libraries
	source "$$(conda info --base)/etc/profile.d/conda.sh" && \
	conda activate ${CONDA_ENV_NAME} && \
	$(MAKE) install-package # install project -> simplify imports

##################################################
##################################################
# RUNNABLES
##################################################
##################################################
.PHONY: test benchmark
test:
	pytest -vvv -n 8 --benchmark-disable


# pytest-benchmark is our typical use case, but too many things need to be
# updated because of the experimental changes.
#
# In addition, we should take advantage of these required changes as an
# excuse to track benchmarks over time. It seems like it would be easiest to
# do this if we port this project over to gitlab and use github only as a
# mirror from now on. GitLab runners, simply put, are just much easier to
# work with in comparison to GitHub actions.
benchmark:
	echo "error: benchmarks need to be reconfigured..."
	exit 1

define benchmark-common-args
		-vvv --benchmark-verbose  --benchmark-name=long  --benchmark-group-by=fullname
endef

benchmark-and-save:
	pytest tests/controls/ $(benchmark-common-args) --benchmark-autosave --benchmark-save-data

benchmark-compare:
	pytest tests/controls/ $(benchmark-common-args) --benchmark-compare
