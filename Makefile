test:
	uv run pytest

check:
	ruff check .

format:
	uv run ruff format .
	uv run ruff check . --fix

podman-run:
	podman run \
		--name ai-agent \
		-e POSTGRES_USER=postgres \
		-e POSTGRES_DB=postgres \
		-e POSTGRES_PASSWORD=ai-agent \
		-p 5434:5432 \
		-v postgres-volume:/Users/joaofig/data/postgres \
		-d pgvector/pgvector:pg17-trixie

docker-run:
	docker run \
		--name ai-agent \
		-e POSTGRES_USER=postgres \
		-e POSTGRES_DB=postgres \
		-e POSTGRES_PASSWORD=ai-agent \
		-p 5434:5432 \
		-v postgres-volume:/Users/joaofig/data/postgres \
		-d pgvector/pgvector:pg17-trixie

prune-docker:
	docker system prune --all --force --volumes
