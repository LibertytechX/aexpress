# Build stage
FROM golang:alpine AS builder

WORKDIR /app

# Install build dependencies
RUN apk add --no-cache git

# Copy go mod and sum files
COPY go.mod go.sum ./
RUN go mod download

# Copy the rest of the source code
COPY . .

# Build the application
RUN CGO_ENABLED=0 GOOS=linux go build -o main ./cmd/main.go

# Production stage
FROM alpine:latest

WORKDIR /app

# Install ca-certificates for HTTPS requests (OSRM might be on HTTPS)
RUN apk add --no-cache ca-certificates

# Copy the binary from the build stage
COPY --from=builder /app/main .

EXPOSE 8081

CMD ["./main"]
