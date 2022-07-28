#!/usr/bin/env bash
toolforge-jobs run fulltext-replace --command "cd ~/tasks/manual/fulltext-replace && fulltext-replace/bin/python fulltext-replace.py" --image tf-python39 --wait
cat fulltext-replace.out
