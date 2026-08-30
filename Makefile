.PHONY: all install install-locked install-paper run data test verify figures paper docker clean

all: install run test

install:
	pip install -r requirements.txt

# Exact pinned versions used for the published numbers
install-locked:
	pip install -r requirements-lock.txt

run:
	cd hyperbench && python run_all.py && mv -f results_summary.json run_metadata.json ../results/

# Regenerate the per-experiment JSON files as well as the summary
data:
	cd hyperbench && \
	  python exp_a_energy_audit.py > /dev/null && \
	  python exp_b_viq.py > /dev/null && \
	  python exp_c_warp_scaling.py > /dev/null && \
	  python exp_d_control.py > /dev/null && \
	  python run_all.py > /dev/null && \
	  mv -f results_*.json run_metadata.json ../results/
	@echo "results/ regenerated"

test:
	python tests/test_paper_claims.py

verify: data test
	python scripts/checksums.py --verify

# Figure generation needs matplotlib (requirements-paper.txt)
install-paper:
	pip install -r requirements-paper.txt

figures:
	python figures/make_architecture_figure.py

paper:
	bash scripts/build_paper.sh

docker:
	docker build -t hyperbench . && docker run --rm hyperbench

clean:
	find . -name __pycache__ -type d -exec rm -rf {} + 2>/dev/null || true
	rm -rf paper/build
	rm -f hyperbench/results_*.json hyperbench/run_metadata.json
