rsync -azP --filter=":- .gitignore" --exclude .git/ . euler:/cluster/work/sachan/vilem/lightweight-quality-metrics/
rsync -azP --filter=":- .gitignore" --exclude .git/ euler:/cluster/work/sachan/vilem/lightweight-quality-metrics/data/mt-metrics-eval-v2-custom/wmt23/metric-scores/en-cs/