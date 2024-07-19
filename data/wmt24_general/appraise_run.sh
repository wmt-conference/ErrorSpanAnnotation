# run in Appraise dir

rm -rf static appraise.log db.sqlite3 Batches;

python3 manage.py migrate;
DJANGO_SUPERUSER_USERNAME=test DJANGO_SUPERUSER_PASSWORD=test python3 manage.py createsuperuser --noinput --email "test@test.test";
python3 manage.py collectstatic --no-post-process;


python3 manage.py StartNewCampaign /home/vilda/ErrorSpanAnnotations/data/wmt24_general/appraise_manifest_wave0ende.json \
    --batches-json /home/vilda/ErrorSpanAnnotations/data/wmt24_general/batches_wave0.en-de.json \
    --csv-output /home/vilda/ErrorSpanAnnotations/data/wmt24_general/appraise_credentials.csv;

# TODO: export

python3 manage.py runserver;