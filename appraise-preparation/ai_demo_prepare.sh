#!/usr/bin/bash

python3 analysis/scripts/02-run_xcomet.py --segments-from-batch data/batches_wmt23_en-cs.json --langs en-cs --comet XL

python3 appraise-preparation/mqm_human_wmt.py --year wmt23 --redundancy 20 --langs en-cs --suffix "_gemba" --mqm "metric-scores/en-cs/GEMBA-MQM-xml-GPT4-src" --sections 0.5 --systems "ONLINE-Y" "refA" | grep "\["
python3 appraise-preparation/mqm_human_wmt.py --year wmt23 --redundancy 20 --langs en-cs --suffix "_comet" --mqm "metric-scores/en-cs/XCOMET-XL"              --sections 0.5 --systems "ONLINE-Y" "refA" | grep "\["
python3 appraise-preparation/mqm_human_wmt.py --year wmt23 --redundancy 20 --langs en-de --suffix "_hummqm" --mqm "human-scores/en-de.mqm.merged"             --sections 0.5 --systems "ONLINE-Y" "refA" | grep "\["

cp data/batches_*.json ~/Appraise_origin/Examples/DirectMQM/

zip ai_demo_rc0.zip appraise-preparation/ai_demo_start.sh data/batches_wmt23_en-cs_{comet,gemba}.json ~/Appraise_origin/Examples/DirectMQM/manifest_ai_demo.json