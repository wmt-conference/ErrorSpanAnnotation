for WAVE in 0 1 2 3 5 8; do
    echo -e "" > data/wmt24_general/appraise/manifest_wave${WAVE}.jsonl;
done


for LANGS in "cs-uk" "en-cs" "en-de" "en-es" "en-hi" "en-is" "en-ja" "en-ru" "en-uk" "en-zh" "ja-zh"; do
    echo $LANGS
    for WAVE in 0 1 2 3 5 8; do
        python3 ./preparation/wmt24/prepare_batches_main.py --langs $LANGS --wave $WAVE \
            | grep -e "^TASK_TO_ANNOTATORS: " \
            | sed "s/TASK_TO_ANNOTATORS: //" \
            >> data/wmt24_general/appraise/manifest_wave${WAVE}.jsonl;
    done
done

zip -r retral-wave0-rc7.zip data/wmt24_general/appraise/manifest_wave0.json data/wmt24_general/batches/wave0.*
zip -r retral-wave1-rc7.zip data/wmt24_general/appraise/manifest_wave1.json data/wmt24_general/batches/wave1.*
zip -r retral-wave2-rc8.zip data/wmt24_general/appraise/manifest_wave2.json data/wmt24_general/batches/wave2.*
zip -r retral-wave3-rc8.zip data/wmt24_general/appraise/manifest_wave3.json data/wmt24_general/batches/wave3.*
zip -r retral-wave5-rc9.zip data/wmt24_general/appraise/manifest_wave5.json data/wmt24_general/batches/wave5.*
zip -r retral-wave8-rc9.zip data/wmt24_general/appraise/manifest_wave8.json data/wmt24_general/batches/wave8.*

# NOTE: we chose waves 5 and 8 because of issue #3