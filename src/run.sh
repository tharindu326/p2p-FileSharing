#!/bin/bash
# USAGE: ./run.sh config1.py config2.py config3.py

if [ $# -eq 0 ]; then
    echo "Usage: $0 config1.py [config2.py ...]"
    exit 1
fi

for cfg in "$@"
do
    echo "Starting Flask app with configuration: $cfg"
    python app.py --config $cfg &
    sleep 5
done

wait
