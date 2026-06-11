FROM alpine:3.21 AS builder
RUN apk add --no-cache gcc musl-dev
WORKDIR /build
COPY source/app.c .
RUN gcc -Os -static -s -o app app.c

FROM scratch
WORKDIR /app
COPY --from=builder /build/app .
COPY source/datetime.txt .
EXPOSE 8000
ENTRYPOINT ["/app/app"]
