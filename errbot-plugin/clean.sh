#!/bin/bash

find . -name __pycache__ -exec rm -Rf {} \;
find . -name *.pyc -exec rm -Rf {} \;
rm -Rf ./errbot/data/*