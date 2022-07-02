#!/usr/bin/env bash
toolforge-jobs run mooncake --command "cd ~/tasks/manual/mooncake && python3 mooncake.py" --image tf-python39 --wait
cat mooncake.out
