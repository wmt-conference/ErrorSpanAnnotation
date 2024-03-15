#!/usr/bin/bash

rm -rf static appraise.log db.sqlite3 Batches;

python3 manage.py migrate;
DJANGO_SUPERUSER_USERNAME=test DJANGO_SUPERUSER_PASSWORD=test python3 manage.py createsuperuser --noinput --email="admin@appraise.org";
python3 manage.py collectstatic --no-post-process;

python3 manage.py StartNewCampaign ~/batches/wmt_demo_manifest.json \
    --batches-json \
        ~/batches/batches_wmt23_en-de.json \
        ~/batches/batches_wmt23_de-en.json \
        ~/batches/batches_wmt23_en-cs.json \
        ~/batches/batches_wmt22_en-hr.json \
        ~/batches/batches_wmt20_en-pl.json \
        ~/batches/batches_wmt23_en-ru.json \
        ~/batches/batches_wmt23_en-zh.json \
    --csv-output ~/batches/wmt_demo_users.csv


python3 manage.py StartNewCampaign ~/batches/wmt_demo_manifest_esa.json \
    --batches-json \
        ~/batches/batches_wmt23_en-de_esa.json \
    --csv-output ~/batches/wmt_demo_users_esa.csv

python3 manage.py StartNewCampaign ~/batches/wmt_demo_manifest_mqm.json \
    --batches-json \
        ~/batches/batches_wmt23_en-de_mqm.json \
    --csv-output ~/batches/wmt_demo_users_mqm.csv

python3 manage.py StartNewCampaign ~/batches/wmt_demo_manifest_esa_gemba.json \
    --batches-json \
        ~/batches/batches_wmt23_en-de_esa_gemba.json \
    --csv-output ~/batches/wmt_demo_users_esa_gemba.csv

        

export APPRAISE_ALLOWED_HOSTS="127.0.0.1,172.211.57.127"
nohup python3 manage.py runserver 0.0.0.0:80 &