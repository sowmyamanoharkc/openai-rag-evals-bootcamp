# Convenience targets for the OpenAI · RAG · Evals bootcamp.

PY ?= python

.PHONY: help install summarize extract ingest rag eval eval-large compare capstone capstone-eval ci-eval ci-eval-capstone test test-capstone clean

help:
	@echo "Targets:"
	@echo "  install          pip install -r requirements.txt"
	@echo "  summarize        Run Assignment 1 summarizer on data/samples/article.txt (STYLE=eli5)"
	@echo "  extract          Run Assignment 2 extractor on data/samples/transcript.txt"
	@echo "  ingest           Run Assignment 3 ingest with default chunk size (500/50)"
	@echo "  rag Q='...'      Ask the RAG CLI a question"
	@echo "  eval             Run Assignment 4 eval suite (writes reports/)"
	@echo "  eval-large       Run Assignment 4 eval with chunk size 1000 / top_k 8"
	@echo "  compare          Run baseline + large-chunks back-to-back"
	@echo "  ci-eval          Run Assignment 4 eval + pytest regression tests (CI gate)"
	@echo "  test             pytest assignment_04_evals/solution/tests/"
	@echo "  clean            Remove chroma_db, reports, logs, tickets.json, __pycache__"

install:
	$(PY) -m pip install -r requirements.txt

STYLE ?= eli5
summarize:
	$(PY) -m assignment_01_hello_openai.solution.summarize data/samples/article.txt --style $(STYLE)

extract:
	$(PY) -m assignment_02_structured_tools.solution.extract data/samples/transcript.txt

ingest:
	$(PY) -m assignment_03_rag.solution.ingest --chunk-size 500 --chunk-overlap 50

ingest-large:
	$(PY) -m assignment_03_rag.solution.ingest --chunk-size 1000 --chunk-overlap 100

rag:
	@if [ -z "$$Q" ]; then echo "Usage: make rag Q='your question'"; exit 1; fi
	$(PY) -m assignment_03_rag.solution.main "$$Q"

eval:
	$(PY) -m assignment_04_evals.solution.run_eval --config-name baseline --top-k 5 --threshold 0.30

eval-large:
	$(MAKE) ingest-large
	$(PY) -m assignment_04_evals.solution.run_eval --config-name large_chunks --top-k 8 --threshold 0.30
	$(MAKE) ingest

compare:
	$(MAKE) ingest
	$(PY) -m assignment_04_evals.solution.run_eval --config-name baseline --top-k 3 --threshold 0.30
	$(MAKE) ingest-large
	$(PY) -m assignment_04_evals.solution.run_eval --config-name large_chunks --top-k 8 --threshold 0.30
	$(MAKE) ingest
	@echo "Both reports written to reports/. Now write reports/comparison.md."

ci-eval:
	$(PY) -m assignment_04_evals.solution.run_eval --config-name ci --top-k 5 --threshold 0.30
	$(PY) -m pytest assignment_04_evals/solution/tests/ -v

test:
	$(PY) -m pytest assignment_04_evals/solution/tests/ -v

clean:
	rm -rf chroma_db reports logs tickets.json
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
