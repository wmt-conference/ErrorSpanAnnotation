# run in Appraise dir

rm -rf static appraise.log db.sqlite3 Batches;

python3 manage.py migrate;
DJANGO_SUPERUSER_USERNAME=test DJANGO_SUPERUSER_PASSWORD=test python3 manage.py createsuperuser --noinput --email "test@test.test";
python3 manage.py collectstatic --no-post-process;

export ROOT="/home/vilda/ErrorSpanAnnotations";
export ROOT="../";

# just WAVE0 EN-DE
python3 manage.py StartNewCampaign ${ROOT}/data/wmt24_general/appraise/manifest_wave0ende.json \
    --batches-json ${ROOT}/data/wmt24_general/batches/wave0.en-de.json \
    --csv-output ${ROOT}/data/wmt24_general/appraise/credentials_wave0ende.csv;

# just WAVE0 EN-CS
python3 manage.py StartNewCampaign ${ROOT}/data/wmt24_general/appraise/manifest_wave0encs.json \
    --batches-json ${ROOT}/data/wmt24_general/batches/wave0.en-cs.json \
    --csv-output ${ROOT}/data/wmt24_general/appraise/credentials_wave0encs.csv;

# just WAVE0 EN-JA
python3 manage.py StartNewCampaign ${ROOT}/data/wmt24_general/appraise/manifest_wave0enja.json \
    --batches-json ${ROOT}/data/wmt24_general/batches/wave0.en-ja.json \
    --csv-output ${ROOT}/data/wmt24_general/appraise/credentials_wave0enja.csv;

# whole WAVE0
python3 manage.py StartNewCampaign ${ROOT}/data/wmt24_general/appraise/manifest_wave0.json \
    --batches-json ${ROOT}/data/wmt24_general/batches/wave0.*.json \
    --csv-output ${ROOT}/data/wmt24_general/appraise/credentials_wave0.csv;

# whole WAVE1
python3 manage.py StartNewCampaign ${ROOT}/data/wmt24_general/appraise/manifest_wave1.json \
    --batches-json ${ROOT}/data/wmt24_general/batches/wave1.*.json \
    --csv-output ${ROOT}/data/wmt24_general/appraise/credentials_wave1.csv;


python3 manage.py StartNewCampaign ${ROOT}/data/wmt24_general/appraise/manifest_wave0.json \
    --batches-json ${ROOT}/data/wmt24_general/batches/wave0.*.json \
    --csv-output ${ROOT}/data/wmt24_general/appraise/credentials_wave0_codes.csv \
    --task-confirmation-tokens;

# start
python3 manage.py runserver;

# export
python3 manage.py ExportSystemScoresToCSV wmt24wave0

# for testing VM
sudo setcap CAP_NET_BIND_SERVICE=+eip $(realpath $(which python3))
export APPRAISE_ALLOWED_HOSTS="127.0.0.1,172.211.57.127"
nohup python3 manage.py runserver 0.0.0.0:80 &