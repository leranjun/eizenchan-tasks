#!/usr/bin/env bash
toolforge-jobs run mooncake --command "python3 mooncake.py" --image tf-python39 --wait
cat mooncake.out
