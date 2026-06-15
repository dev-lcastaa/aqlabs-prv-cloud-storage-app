# S3 Mock App (FastAPI + React + Docker)

Container-first MVP that behaves like a lightweight S3 mock:
- Create bucket folders
- Upload objects with key paths (example: reports/2026/june.csv)
- Persist object metadata in PostgreSQL
- Delete objects in single and multi mode
- Store real file data on a mounted host volume

## Stack

- Backend: FastAPI + SQLAlchemy
- Frontend: Vite React (modern dark UI)
- DB: PostgreSQL
- Orchestration: Docker Compose

## Project Layout

- backend/: FastAPI API and storage service
- frontend/: React UI
- volumes/storage/: host-mounted object storage
- volumes/postgres/: host-mounted PostgreSQL data
- docker-compose.yml: local container orchestration

## Run

```bash
docker compose up --build
```

Services:
- Frontend: http://localhost:5173
- Backend: http://localhost:8000
- API docs: http://localhost:8000/docs

## API Overview

- `GET /health`
- `GET /api/buckets`
- `POST /api/buckets` body: `{ "name": "my-bucket" }`
- `DELETE /api/buckets/{bucket_id}`
- `GET /api/buckets/{bucket_id}/objects`
- `POST /api/buckets/{bucket_id}/objects/folders` multipart form: `path`
- `POST /api/buckets/{bucket_id}/objects` multipart form:
  - `file`: binary
  - `key`: string object key, can contain `/`
  - `metadata`: optional JSON string
- `DELETE /api/buckets/{bucket_id}/objects/{object_id}`
- `POST /api/buckets/{bucket_id}/objects/delete-bulk` body: `{ "object_ids": ["...", "..."] }`

## Mounted Volume Behavior

Backend writes files under `/data/storage` inside the backend container.
Docker Compose maps that path to host folder `./volumes/storage`.

When you upload key `reports/2026/june.csv` to bucket id `abc123`, the host file path becomes:

`volumes/storage/abc123/reports/2026/june.csv`

## Notes

- Object keys are unique per bucket.
- Delete is hard-delete in MVP (file + metadata row).
- Bulk delete supports partial success and returns failed item reasons.
