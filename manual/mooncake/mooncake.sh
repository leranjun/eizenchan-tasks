#!/usr/bin/env bash
toolforge-jobs run mooncake --command "python3 mooncake.py" --image tf-bullseye-std --wait
cat mooncake.out
