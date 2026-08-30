# Exact-environment reproduction of the HYPERBENCH results.
#
#   docker build -t hyperbench .
#   docker run --rm hyperbench                 # run experiments + tests
#   docker run --rm -v "$PWD/out:/out" hyperbench sh -c \
#       "python hyperbench/run_all.py && cp results_summary.json /out/"
#
# Pinned to the interpreter and library versions used for the published numbers.

FROM python:3.12.3-slim

WORKDIR /app

COPY requirements-lock.txt .
RUN pip install --no-cache-dir -r requirements-lock.txt

COPY hyperbench/ ./hyperbench/
COPY tests/ ./tests/
COPY results/ ./results/

# Reproduce every experiment, then verify every claim in the paper.
CMD ["sh", "-c", "cd hyperbench && python run_all.py && cd .. && python tests/test_paper_claims.py"]
