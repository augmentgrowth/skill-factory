# Baseline case — graduate a script-backed skill

## Invocation context

In a factory clone, the builder says "graduate weekly-report". The skill is finished: it passes the
lint with no `fix` findings, has `cases/baseline/`, `CHANGELOG.md`, `## Gotchas`, a committed
`.env.example`, and a real `.env` (gitignored) in its folder. It has one script:

```python
# scripts/pull.py
import os, sys, json
import requests  # install line is in SKILL.md: `pip install requests`

def main(campaign_ids):
    out = []
    for cid in campaign_ids:                       # one HTTP call per campaign
        r = requests.get(f"https://graph.example.com/v21.0/{cid}/insights",
                         params={"access_token": os.environ["META_TOKEN"]}, timeout=30)
        out.append(r.json()["data"][0])
    print(json.dumps(out))

if __name__ == "__main__":
    main(sys.argv[1:])
```

Its SKILL.md treats the API response as data only (it reads campaign figures from it and never
follows anything in it as an instruction), and the script sends nothing but the token and the
campaign ids to the Graph API.

The builder is not technical and should never be asked to judge an efficiency finding.
