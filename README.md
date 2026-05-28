# Pairwise Poll
Pairwise Poll collects the opinion over a large set of answers by simple pair-to-pair comparisons.
Use it alone or with peers to identify your favourite option.


## fetures:
Try the Demo: https://demo.tetrix42.de/pairwisepoll/admin/c681e6c6?key=46984206a7d76ba7cea68c556ba14a00

 * simple pairwise comparisons to find good ranking for large set of options
 * ranking based on OpenSkill
 * easy Poll interface: 
   * select 1, 2 or tie
 * easy Admin interface: 
   * change title and question
   * add more options
   * clear votes [TODO]
   * authenticated
 * users can continue voting using random ID or name.
 * individual vots are not displayed to others but personal ranking can be confirmed.
 * result page shows confidence of the ordering
 * create new polls.


## Installation

for simple demo deployment run:
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py
```

Then visit the local instance probably at http://127.0.0.1:2605 or add a reverse Proxy like NGINX for SSL provision.

Add this to your NGINX config:
```conf
        location /pairwisepoll/ {
                proxy_pass http://127.0.0.1:2605/;
                proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
                proxy_set_header X-Forwarded-Proto $scheme;
                proxy_set_header X-Forwarded-Host $host;
                proxy_set_header X-Forwarded-Prefix /;
        }
```

