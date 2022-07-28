#!/usr/bin/env bash
toolforge-jobs run venv-job --command "cd $PWD && bash ../../venv.sh" --image tf-python39 --wait
rm -rf venv-job.*
