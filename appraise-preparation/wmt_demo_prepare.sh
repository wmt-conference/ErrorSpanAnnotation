#!/usr/bin/bash

python3 appraise-preparation/mqm_human_wmt.py --year wmt23 --redundancy 20 --langs en-de --tasks-per-section 1 --sections 1 --systems "ONLINE-Y" "refA" | grep "\["
python3 appraise-preparation/mqm_human_wmt.py --year wmt23 --redundancy 20 --langs de-en --tasks-per-section 1 --sections 1 --systems "ONLINE-Y" "refA" | grep "\["
python3 appraise-preparation/mqm_human_wmt.py --year wmt23 --redundancy 20 --langs en-cs --tasks-per-section 1 --sections 1 --systems "ONLINE-Y" "refA" | grep "\["
python3 appraise-preparation/mqm_human_wmt.py --year wmt22 --redundancy 20 --langs en-hr --tasks-per-section 1 --sections 1 --systems "Online-A" "refA" | grep "\["
python3 appraise-preparation/mqm_human_wmt.py --year wmt20 --redundancy 20 --langs en-pl --tasks-per-section 1 --sections 1 --systems "Online-A.1576" "ref" | grep "\["
python3 appraise-preparation/mqm_human_wmt.py --year wmt23 --redundancy 20 --langs en-ru --tasks-per-section 1 --sections 1 --systems "ONLINE-Y" "refA" | grep "\["
python3 appraise-preparation/mqm_human_wmt.py --year wmt23 --redundancy 20 --langs en-zh --tasks-per-section 1 --sections 1 --systems "ONLINE-Y" "refA" | grep "\["

cp data/batches_*.json ~/Appraise/Examples/DirectMQM/
cp appraise-preparation/*_manifest.json ~/Downloads/batches/
rsync -a ~/Downloads/batches/ appraise:batches/

python3 appraise-preparation/mqm_human_wmt.py --year wmt23 --redundancy 20 --langs en-cs --suffix "_gemba" --mqm "metric-scores/en-cs/GEMBA-MQM-xml-GPT4-src" --tasks-per-section 1 --sections 1 --systems "ONLINE-Y" "refA" | grep "\["
python3 appraise-preparation/mqm_human_wmt.py --year wmt23 --redundancy 20 --langs en-cs --suffix "_comet" --mqm "metric-scores/en-cs/XCOMET-XL" --tasks-per-section 1 --sections 1 --systems "ONLINE-Y" "refA" | grep "\["
python3 appraise-preparation/mqm_human_wmt.py --year wmt23 --redundancy 20 --langs en-de --suffix "_hummqm" --mqm "human-scores/en-de.mqm.merged" --tasks-per-section 1 --sections 1 --systems "ONLINE-Y" "refA" | grep "\["