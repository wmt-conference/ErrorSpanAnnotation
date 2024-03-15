#!/usr/bin/bash

rm -rf static appraise.log db.sqlite3 Batches;
python3 manage.py migrate;
DJANGO_SUPERUSER_USERNAME=test DJANGO_SUPERUSER_PASSWORD=test python3 manage.py createsuperuser --noinput --email="admin@appraise.org";
python3 manage.py collectstatic --no-post-process;

python3 manage.py StartNewCampaign \
    ~/Downloads/ruction_rc4/appraise-preparation/ruction_manifest_esa.json \
    --batches-json ~/Downloads/ruction_rc4/data/batches_wmt23_en-de_esa.json \
    --csv-output ~/error-span-annotations/tmp/ruction_users_esa.csv

python3 manage.py StartNewCampaign \
    ~/Downloads/ruction_rc4/appraise-preparation/ruction_manifest_esa_gemba.json \
    --batches-json ~/Downloads/ruction_rc4/data/batches_wmt23_en-de_esa_gemba.json \
    --csv-output ~/error-span-annotations/tmp/ruction_users_esa_gemba.csv

python3 manage.py StartNewCampaign \
    ~/Downloads/ruction_rc4/appraise-preparation/ruction_manifest_mqm.json \
    --batches-json ~/Downloads/ruction_rc4/data/batches_wmt23_en-de_mqm.json \
    --csv-output ~/error-span-annotations/tmp/ruction_users_mqm.csv

python3 manage.py runserver  

export APPRAISE_ALLOWED_HOSTS="127.0.0.1,172.211.57.127"
nohup python3 manage.py runserver 0.0.0.0:80 &