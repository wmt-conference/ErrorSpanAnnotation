#!/usr/bin/bash

python3 appraise-preparation/mqm_human_wmt.py --year wmt23 --redundancy 20 --langs en-de --sections 0.5 --systems "ONLINE-Y" "refA" | grep "\["
python3 appraise-preparation/mqm_human_wmt.py --year wmt23 --redundancy 20 --langs de-en --sections 0.5 --systems "ONLINE-Y" "refA" | grep "\["
python3 appraise-preparation/mqm_human_wmt.py --year wmt23 --redundancy 20 --langs en-cs --sections 0.5 --systems "ONLINE-Y" "refA" | grep "\["
python3 appraise-preparation/mqm_human_wmt.py --year wmt22 --redundancy 20 --langs en-hr --sections 0.5 --systems "Online-A" "refA" | grep "\["
python3 appraise-preparation/mqm_human_wmt.py --year wmt20 --redundancy 20 --langs en-pl --sections 0.5 --systems "Online-A.1576" "ref" | grep "\["
python3 appraise-preparation/mqm_human_wmt.py --year wmt23 --redundancy 20 --langs en-ru --sections 0.5 --systems "ONLINE-Y" "refA" | grep "\["
python3 appraise-preparation/mqm_human_wmt.py --year wmt23 --redundancy 20 --langs en-zh --sections 0.5 --systems "ONLINE-Y" "refA" | grep "\["
python3 appraise-preparation/mqm_human_wmt.py --year wmt23 --redundancy 20 --langs en-cs --tutorial "" --suffix "_gemba" --mqm "metric-scores/en-cs/GEMBA-MQM-xml-GPT4-src"  --sections 1 --systems "ONLINE-Y" "refA" | grep "\["

cp data/batches_*.json ~/Appraise/Examples/DirectMQM/
cp data/batches_*.json ~/Downloads/batches
cp appraise-preparation/*_manifest.json ~/Downloads/batches/
rsync -a ~/Downloads/batches/ appraise:batches/

python3 appraise-preparation/mqm_human_wmt.py --year wmt23 --redundancy 20 --langs en-cs --tutorial "" --suffix "_comet" --mqm "metric-scores/en-cs/XCOMET-XL"  --sections 1 --systems "ONLINE-Y" "refA" | grep "\["
python3 appraise-preparation/mqm_human_wmt.py --year wmt23 --redundancy 20 --langs en-de --tutorial "" --suffix "_hummqm" --mqm "human-scores/en-de.mqm.merged" --sections 1 --systems "ONLINE-Y" "refA" | grep "\["