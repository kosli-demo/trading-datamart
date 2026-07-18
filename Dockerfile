FROM ruby:4.0.5-alpine3.24@sha256:f48938e9ae72a4d32e728b03c306e7a7ff21f0cb6c2ed33f44a078c700b2aea6
LABEL maintainer=jon@kosli.com

# tini reaps the puma process as PID 1. wget (for the HEALTHCHECK) is already
# in the base alpine image. The apk index/package fetch is retried a few times:
# the Alpine CDN occasionally resets the connection or fails the TLS handshake,
# and a single flake should not fail the whole fleet build. The command still
# fails if every attempt fails.
RUN apk add --no-cache tini \
 || ( sleep 5 && apk add --no-cache tini ) \
 || ( sleep 15 && apk add --no-cache tini )

WORKDIR /app

# Install gems first so this layer caches across source-only changes. puma ships
# a C extension, so the build toolchain is needed to compile it, then dropped.
COPY source/Gemfile .
RUN ( apk add --no-cache --virtual build-deps build-base \
   || ( sleep 5 && apk add --no-cache --virtual build-deps build-base ) \
   || ( sleep 15 && apk add --no-cache --virtual build-deps build-base ) ) \
 && bundle install \
 && apk del build-deps \
 && rm -rf /usr/local/bundle/cache/* /var/cache/apk/*

COPY source/ .

ENV PORT=8000
EXPOSE 8000
HEALTHCHECK --interval=5s --timeout=2s --retries=5 --start-period=5s \
  CMD sh config/healthcheck.sh
ENTRYPOINT ["/sbin/tini", "-g", "--"]
CMD ["sh", "-c", "bundle exec puma --port ${PORT} config.ru"]
