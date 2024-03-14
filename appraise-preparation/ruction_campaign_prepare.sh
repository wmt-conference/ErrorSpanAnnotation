#!/usr/bin/bash

python3 appraise-preparation/mqm_human_wmt.py \
    --year wmt23 --redundancy 20 --langs en-de --bad-segments 12 --sec-tutorial "de-en.mqm" \
    --suffix "_mqm" \
    --src-docs 15 --systems "ONLINE-Y" "refA" \
    --mqm-filter "human-scores/en-de.mqm.merged" \
;

python3 appraise-preparation/mqm_human_wmt.py \
    --year wmt23 --redundancy 20 --langs en-de --bad-segments 12 --sec-tutorial "de-en.esa" \
    --suffix "_esa" \
    --src-docs 15 --systems "ONLINE-Y" "refA" \
    --mqm-filter "human-scores/en-de.mqm.merged" \
;

python3 appraise-preparation/mqm_human_wmt.py \
    --year wmt23 --redundancy 20 --langs en-de --bad-segments 12 --sec-tutorial "de-en.esa" \
    --suffix "_esa_gemba" \
    --src-docs 15 --systems "ONLINE-Y" "refA"  \
    --mqm-filter "human-scores/en-de.mqm.merged" \
    --mqm "metric-scores/en-de/GEMBA-MQM-ESA-GPT4-src" \
;
 

cp data/batches_wmt23_en-de_{esa,mqm}*.json ~/Appraise/Examples/DirectMQM/
cp data/batches_wmt23_en-de_{esa,mqm}*.json ~/Downloads/batches
rsync -a ~/Downloads/batches/ appraise:batches/

cp appraise-preparation/*_manifest.json ~/Downloads/batches/



python3 appraise-preparation/mqm_human_wmt.py \
    --year wmt23 --langs en-de --bad-segments 12 --sec-tutorial "de-en.mqm" \
    --suffix "_mqm" \
    --src-docs 74 \
    --mqm-filter "human-scores/en-de.mqm.merged" \
;

python3 appraise-preparation/mqm_human_wmt.py \
    --year wmt23 --langs en-de --bad-segments 12 --sec-tutorial "de-en.esa" \
    --suffix "_esa" \
    --src-docs 74 \
    --mqm-filter "human-scores/en-de.mqm.merged" \
;

python3 appraise-preparation/mqm_human_wmt.py \
    --year wmt23 --langs en-de --bad-segments 12 --sec-tutorial "de-en.esa" \
    --suffix "_esa_gemba" \
    --src-docs 74 \
    --mqm "metric-scores/en-de/GEMBA-MQM-ESA-GPT4-src" \
    --mqm-filter "human-scores/en-de.mqm.merged" \
;