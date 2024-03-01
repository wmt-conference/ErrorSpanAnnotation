#!/usr/bin/bash

rm -rf static appraise.log db.sqlite3 Batches;

python3 manage.py migrate;
DJANGO_SUPERUSER_USERNAME=test DJANGO_SUPERUSER_PASSWORD=test python manage.py createsuperuser --noinput --email="test@test.test";
python3 manage.py collectstatic --no-post-process;

python3 manage.py StartNewCampaign Examples/DirectMQM/manifest_ai_demo.json \
    --batches-json \
        Examples/DirectMQM/batches_wmt23_en-cs_comet.json \
        Examples/DirectMQM/batches_wmt23_en-cs_gemba.json \
    --csv-output Examples/DirectMQM/output.csv

python3 manage.py runserver;