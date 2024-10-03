#!/usr/bin/bash

mkdir -p data/
wget https://storage.googleapis.com/mt-metrics-eval/mt-metrics-eval-v2.tgz
tar -xzf mt-metrics-eval-v2.tgz
rm mt-metrics-eval-v2.tgz
mv mt-metrics-eval-v2/ data/mt-metrics-eval-v2

mkdir -p logs