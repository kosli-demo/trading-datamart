#!/usr/bin/env sh
set -eu

# Container HEALTHCHECK probe. Alpine ships wget (not curl). Hits /ready, which
# is 200 only when datetime.txt is present and well-formed; any non-200 makes
# wget exit non-zero and the healthcheck fail.
#
# 127.0.0.1, not localhost: the image's /etc/hosts maps localhost to both
# 127.0.0.1 and ::1, and busybox wget tries the IPv6 ::1 first and gives up
# when puma (listening on IPv4 0.0.0.0) refuses it.

wget --quiet --output-document=- "http://127.0.0.1:${PORT:-8000}/ready"
