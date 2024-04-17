#!/usr/bin/bash

# run me from top-level

# WMT metrics data
mkdir -p data/
cd data/
wget https://storage.googleapis.com/mt-metrics-eval/mt-metrics-eval-v2.tgz
tar -xzf mt-metrics-eval-v2.tgz
rm mt-metrics-eval-v2.tgz
cd ../

# get campaign preparation ddata
cd campaign-ruction-rc5
wget https://vilda.net/t/ruction_rc5.zip
unzip ruction_rc5.zip
rm -rf appraise-preparation
rm ruction_rc5.zip

cd ../../
