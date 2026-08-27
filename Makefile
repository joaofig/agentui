test:
	uv run pytest

check:
	ruff check .

podman-run:
	podman run \
		--name custor-agent \
		-e POSTGRES_USER=postgres \
		-e POSTGRES_DB=postgres \
		-e POSTGRES_PASSWORD=custor-agent \
		-p 5433:5432 \
		-v postgres-volume:/Users/joaofig/data/postgres \
		-d pgvector/pgvector:pg17-trixie

docker-run:
	docker run --rm \
		--name custor-agent \
		-e POSTGRES_USER=postgres \
		-e POSTGRES_DB=postgres \
		-e POSTGRES_PASSWORD=custor-agent \
		-p 5433:5432 \
		-d pgvector/pgvector:pg17-trixie

prune-docker:
	docker system prune --all --force --volumes
