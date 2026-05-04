#!/usr/bin/env sh
set -eu

activation_file="${OT2_LICENSE_ACTIVATION_FILE:-/app/.activation.needs}"

if [ -n "${OT2_LICENSE_MACHINE_ID:-}" ]; then
    umask 077
    printf '%s\n' "$OT2_LICENSE_MACHINE_ID" > "$activation_file"
else
    rm -f "$activation_file"
fi

exec "$@"
