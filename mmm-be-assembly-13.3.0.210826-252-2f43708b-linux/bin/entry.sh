#!/usr/bin/env bash
set -o pipefail

wait_for_healthy() {
    MAX_WAIT=300
    echo "Waiting for healthy on port $1 for up to $MAX_WAIT seconds."
    for i in `seq $MAX_WAIT`; do
        if wget -t 1 -O - "http://localhost:$1/actuator/health" >> /dev/null; then
            echo "Healthy within $i seconds."
            return 0
        fi
        sleep 1
    done
    echo "Not healthy within $MAX_WAIT seconds."
    return 1
}

if [[ "$1" = 'smoke' ]]; then
    wait_for_healthy 8021
    exit $?
fi

set -e

# MMM core JAVA_OPTS are set in mmm.nomad file in one-metadata-nomad repository
if [[ -n "$REMOTE_DEBUG" ]]; then
    export JAVA_OPTS="$JAVA_OPTS -agentlib:jdwp=transport=dt_socket,server=y,suspend=n,address=*:50021"
fi

exec bin/start.sh "$@"
