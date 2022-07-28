#!/usr/bin/env bash
toolforge-jobs run venv-job --command "cd $PWD && bash ../../venv.sh" --no-filelog --image tf-python39 --wait
