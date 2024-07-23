echo "" > data/for_tom.out


for LANGS in "cs-uk" "en-cs" "en-de" "en-es" "en-hi" "en-is" "en-ja" "en-ru" "en-uk" "en-zh" "ja-zh"; do
    echo $LANGS
    for WAVE in 0 1; do
        echo -e "\n\n\nLANGS: $LANGS\nWAVE: $WAVE" >> data/for_tom.out;
        python3 ./preparation/wmt24/prepare_batches_main.py --langs $LANGS --wave $WAVE >> data/for_tom.out;
    done
done