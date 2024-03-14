#!/usr/bin/bash

python3 appraise-preparation/mqm_human_wmt.py --year wmt23 --redundancy 20 --langs en-de --sec-bad "en-de" --sec-tutorial "de-en.mqm" --suffix "_mqm" --sections 0.5 --systems "ONLINE-Y" "refA" | grep "\["
python3 appraise-preparation/mqm_human_wmt.py --year wmt23 --redundancy 20 --langs en-de --sec-bad "en-de" --sec-tutorial "de-en.esa" --suffix "_esa" --sections 0.5 --systems "ONLINE-Y" "refA" | grep "\["
cp data/batches_wmt23_en-de_{esa,mqm}.json ~/Appraise/Examples/DirectMQM/


cp data/batches_*.json ~/Downloads/batches
cp appraise-preparation/*_manifest.json ~/Downloads/batches/
rsync -a ~/Downloads/batches/ appraise:batches/
