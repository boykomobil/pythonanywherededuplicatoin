run:
	FLASK_RUN_PORT=$${PORT:-3000} python -m flask --app src.app run --host 0.0.0.0

worker:
	python -m src.worker

test:
	python -m pytest -q

format:
	python -m pip install ruff==0.6.9 && ruff check --fix .
