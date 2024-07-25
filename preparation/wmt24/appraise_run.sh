# run in Appraise dir

rm -rf static appraise.log db.sqlite3 Batches;

python3 manage.py migrate;
DJANGO_SUPERUSER_USERNAME=test DJANGO_SUPERUSER_PASSWORD=test python3 manage.py createsuperuser --noinput --email "test@test.test";
python3 manage.py collectstatic --no-post-process;

ROOT="/home/vilda/ErrorSpanAnnotations";
ROOT="../";

# just WAVE0 EN-DE
python3 manage.py StartNewCampaign ${ROOT}/data/wmt24_general/appraise/manifest_wave0ende.json \
    --batches-json ${ROOT}/data/wmt24_general/batches/wave0.en-de.json \
    --csv-output ${ROOT}/data/wmt24_general/appraise/credentials_wave0ende.csv;

# whole WAVE0
python3 manage.py StartNewCampaign ${ROOT}/data/wmt24_general/appraise/manifest_wave0.json \
    --batches-json ${ROOT}/data/wmt24_general/batches/wave0.*.json \
    --csv-output ${ROOT}/data/wmt24_general/appraise/credentials_wave0.csv;


# start
python3 manage.py runserver;

# export
python3 manage.py ExportSystemScoresToCSV wmt24wave0

# for testing VM
export APPRAISE_ALLOWED_HOSTS="127.0.0.1,172.211.57.127"
nohup python3 manage.py runserver 0.0.0.0:80 &