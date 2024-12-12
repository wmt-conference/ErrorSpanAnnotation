# Error Span Annotation

## Collected data

Instructions WIP.

## Running the code

In order to run the scripts, you need to "install" the package with:
```
pip3 install -e .
```

Alternatively you can just run scripts from `scripts/`.
Further instructions WIP.

## Cite

Read [ESA](https://arxiv.org/abs/2406.11580) and [ESAAI](https://arxiv.org/abs/2406.12419) papers.
If you use Error Span Annotation protocol, please cite:

```
@misc{kocmizouhar2024esa,
      title={Error Span Annotation: A Balanced Approach for Human Evaluation of Machine Translation}, 
      author={Tom Kocmi and Vilém Zouhar and Eleftherios Avramidis and Roman Grundkiewicz and Marzena Karpinska and Maja Popović and Mrinmaya Sachan and Mariya Shmatova},
      year={2024},
      eprint={2406.11580},
      archivePrefix={arXiv},
      primaryClass={cs.CL},
      url={https://arxiv.org/abs/2406.11580}, 
}
```

and

```
@misc{zouharkocmi2024esaai,
      title={AI-Assisted Human Evaluation of Machine Translation}, 
      author={Vilém Zouhar and Tom Kocmi and Mrinmaya Sachan},
      year={2024},
      eprint={2406.12419},
      archivePrefix={arXiv},
      primaryClass={cs.CL},
      url={https://arxiv.org/abs/2406.12419}, 
}
```

<img src="misc/poster_ESA.png" width="900wv">


## Running the ESA/ESA<super>AI</super> interface

The ESA interface was implemented in [https://github.com/AppraiseDev/Appraise](Appraise).

```
# set up Appraise basics
git clone https://github.com/AppraiseDev/Appraise
git checkout develop
cd Appraise
pip3 install -r requirements.txt

# some Appraise stuff
python3 manage.py migrate;
DJANGO_SUPERUSER_USERNAME=test DJANGO_SUPERUSER_PASSWORD=test python3 manage.py createsuperuser --noinput --email "test@test.test";
python3 manage.py collectstatic --no-post-process;

# add the default ESA campaign
python3 manage.py StartNewCampaign Examples/MQM+ESA/manifest_esa.json \
    --batches-json Examples/MQM+ESA/batches_esa.json \
    --csv-output Examples/MQM+ESA/output_esa.csv;

# launch the server!
python3 manage.py runserver;

# keep it running but navigate to some of the links in Examples/MQM+ESA/output_esa.csv

# after everyone finishes, collect the data with the following command:
python3 manage.py ExportSystemScoresToCSV example15esa
```