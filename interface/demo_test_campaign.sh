#!/usr/bin/bash

python3 interface/mqm_human_wmt.py --year wmt23 --redundancy 20 --langs en-de --no-mqm --tasks-per-section 1 --sections 1 --systems "ONLINE-Y" "refA" | grep "\["
python3 interface/mqm_human_wmt.py --year wmt23 --redundancy 20 --langs de-en --no-mqm --tasks-per-section 1 --sections 1 --systems "ONLINE-Y" "refA" | grep "\["
python3 interface/mqm_human_wmt.py --year wmt23 --redundancy 20 --langs en-cs --no-mqm --tasks-per-section 1 --sections 1 --systems "ONLINE-Y" "refA" | grep "\["
python3 interface/mqm_human_wmt.py --year wmt22 --redundancy 20 --langs en-hr --no-mqm --tasks-per-section 1 --sections 1 --systems "Online-A" "refA" | grep "\["
python3 interface/mqm_human_wmt.py --year wmt20 --redundancy 20 --langs en-pl --no-mqm --tasks-per-section 1 --sections 1 --systems "Online-A.1576" "ref" | grep "\["

cp data/batches_*.json ~/Appraise/Examples/DirectMQM/