PYTHON ?= python3
JOBS ?= 8
HOST ?= Xeon8375C
CPUS ?= 32-39
DATA ?= reference/data.json
SPEEDS ?= speeds.json
OUTPUT ?= data.json

.PHONY: reproduce benchmark build chart-data compare verify-xeon test sanity
reproduce:
	$(MAKE) benchmark
	$(MAKE) chart-data
benchmark:
	$(PYTHON) scripts/benchmark.py --jobs $(JOBS) $(ARGS)
build:
	$(PYTHON) scripts/build.py --jobs $(JOBS)
chart-data:
	$(PYTHON) scripts/chart_data.py --data "$(DATA)" --speeds $(SPEEDS) --output "$(OUTPUT)"
compare:
	$(PYTHON) scripts/compare.py --speeds $(SPEEDS) --host $(HOST)
verify-xeon:
	$(PYTHON) scripts/build.py --jobs $(JOBS)
	$(PYTHON) scripts/sanity.py --host Xeon8375C --cpus $(CPUS)
	$(PYTHON) scripts/benchmark.py --host Xeon8375C --subset --cpus $(CPUS) --skip-build
	$(PYTHON) scripts/compare.py --subset --host Xeon8375C --speeds speeds.json

test:
	$(PYTHON) -m unittest discover -s tests -v

sanity:
	$(PYTHON) scripts/sanity.py --host $(HOST) --cpus $(CPUS)
