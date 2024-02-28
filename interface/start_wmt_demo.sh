#!/usr/bin/bash

rm -rf static appraise.log db.sqlite3 Batches;

python3 manage.py migrate;
DJANGO_SUPERUSER_USERNAME=test DJANGO_SUPERUSER_EMAIL="" DJANGO_SUPERUSER_PASSWORD=test python manage.py createsuperuser --noinput;
python3 manage.py collectstatic --no-post-process;

python3 manage.py StartNewCampaign Examples/DirectMQM/manifest_ondrej_demo.json \
    --batches-json \
        Examples/DirectMQM/batches_wmt20_en-pl.json \
        Examples/DirectMQM/batches_wmt22_en-hr.json \
        Examples/DirectMQM/batches_wmt23_de-en.json \
        Examples/DirectMQM/batches_wmt23_en-cs.json \
        Examples/DirectMQM/batches_wmt23_en-de.json \
        Examples/DirectMQM/batches_wmt23_en-ru.json \
        Examples/DirectMQM/batches_wmt23_en-zh.json \
    --csv-output Examples/DirectMQM/output.csv

python3 manage.py runserver;