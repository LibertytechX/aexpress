-include .env
export

.PHONY: run dev build sqlc migrate-up migrate-down

run:
	@go run cmd/main.go

dev:
	@go tool air

build:
	@go build -o tmp/main cmd/main.go

sqlc:
	@go run github.com/sqlc-dev/sqlc/cmd/sqlc@latest generate

migrate-up:
	@go run github.com/pressly/goose/v3/cmd/goose@latest -dir db/migrations postgres "$(DATABASE_URL)" up

migrate-down:
	@go run github.com/pressly/goose/v3/cmd/goose@latest -dir db/migrations postgres "$(DATABASE_URL)" down

