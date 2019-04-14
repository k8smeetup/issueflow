#!/bin/sh
set -x
DEST="./errbot"
rm -Rf "${DEST}"
mkdir -p {"${DEST}","${DEST}/plugins"}
cp config.py "${DEST}/"
cp Dockerfile "${DEST}/"
cp prepare.sh "${DEST}/"
cp requirements.txt "${DEST}/"
cp -Rf transbot "${DEST}/plugins/"
cp -Rf ../githubutil "${DEST}/plugins/transbot/githubutil"
cp -Rf ../gitutil "${DEST}/plugins/transbot/gitutil"
cp -Rf ../transutil "${DEST}/plugins/transbot/transutil"
cp -Rf ../config/repository.yaml "${DEST}"