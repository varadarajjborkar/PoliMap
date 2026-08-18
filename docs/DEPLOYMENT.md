# Deploying PoliMap

Two pieces, deployed differently, for one reason.

The frontend is a static bundle of HTML, CSS and JavaScript. It goes anywhere.

The API cannot go on a serverless platform, and it is worth being specific about
why rather than discovering it halfway through:

1. **Tesseract is a binary.** Reading a photographed policy shells out to it.
   No Python wheel contains it, and serverless Python runtimes give you no way
   to install a system package.
2. **Requests are long.** Reading a scanned document runs OCR and several model
   calls. That exceeds the request timeout on most serverless tiers.
3. **The activity stream is a held-open connection.** Server-sent events need a
   connection that lives for minutes. Serverless functions are built to end.

So: **frontend on Vercel, API in a container.** Render, Railway and Fly.io all
work; the Dockerfile is not specific to any of them.

---

## 1. The API

### Build and run locally first

```bash
docker build -f backend/Dockerfile -t polimap-api .
docker run -p 8000:8000 --env-file backend/.env polimap-api

curl localhost:8000/api/health
```

The build context is the repository root, not `backend/`, because the image
needs `datagen/` to produce the hospital corpus. That happens at build time via
`build_all --core`, which writes the three JSON files the running app reads and
skips rendering the policy documents. Those are 80 MB and only the tests and
benchmarks open them.

### Deploy it

Point your host at the repository with:

- **Dockerfile path**: `backend/Dockerfile`
- **Docker context**: `.` (the repository root)
- **Health check path**: `/api/health`

### Environment

| Variable | Needed | Notes |
|---|---|---|
| `OLLAMA_API_KEY` | no | Without it the app runs its deterministic extractor and says so |
| `CORS_ORIGINS` | **yes** | Your frontend's origin, exactly, no trailing slash |
| `SESSION_STORE` | no | `sqlite` (default) or `memory` |
| `SESSION_TTL_MINUTES` | no | Default 720. Sessions and page images expire after this |
| `LOG_LEVEL` | no | `INFO` by default |
| `PORT` | no | Most hosts set it themselves; the image honours it |
| `TRUST_PROXY` | **yes, on any real host** | See below. Render, Railway and Fly all put a proxy in front |
| `BEHIND_TLS` | recommended | Turns on HSTS. True wherever the host terminates TLS, which is everywhere with a https URL |
| `ENABLE_DOCS` | no | `/docs` and the OpenAPI schema. Off by default and best left off |
| `MAX_DOCUMENT_PAGES` | no | Default 60. Pages one upload may contain |
| `MAX_EVENT_STREAMS` | no | Default 200. Activity streams held open at once |

Two of these get forgotten, and they fail in opposite ways.

`CORS_ORIGINS` fails loudly: the site loads perfectly and every request fails
in the browser console.

`TRUST_PROXY` fails quietly, which is worse. Every managed host puts a proxy in
front of your container, so without it every request in the world arrives from
the proxy's address and shares one rate-limit allowance. Nothing errors. The
app simply starts refusing people, and the first busy user locks out everyone
else. The app says so in its log the first time it sees a forwarded header
without this set, so check the log if the live site starts answering 429 to
people who have not done anything.

Set it only where a proxy really is in front. Where nothing is proxying, the
forwarded header is written by whoever is calling, and trusting it hands every
caller a fresh allowance per request, which is the same as having no limit.

### Persistence

Session rows and page images live under `/app/data`. Without a mounted volume
they are lost when the container restarts, which is tolerable for state that
expires in hours anyway, but it does mean an open tab loses its session on every
redeploy. Mount a volume there if that matters to you.

### Scale

Run one worker per container, which is what the image does. The event bus that
feeds the activity stream is in-process, so a second worker would serve some
browsers a stream carrying none of their own events. Scale by running more
containers behind a load balancer with sticky sessions.

---

## 2. The frontend on Vercel

Import the repository, then set:

- **Root directory**: `frontend`
- **Framework preset**: Vite (detected)
- **Environment variable**: `VITE_API_BASE` = your API's origin, for example
  `https://polimap-api.onrender.com`, with no trailing slash

`frontend/vercel.json` already handles the rest: the SPA rewrite so a deep link
like `/#/hospitals` resolves, and long cache headers on the hashed assets.

`VITE_API_BASE` is read at **build** time, not run time. Changing it means
redeploying, not just restarting.

---

## 3. Wiring the two together

The two settings have to name each other:

```
API:       CORS_ORIGINS=https://polimap.vercel.app
Frontend:  VITE_API_BASE=https://polimap-api.onrender.com
```

Both must be `https` if the site is. A browser refuses to let an https page call
an http API, and the failure appears as a generic network error rather than
anything that names the cause.

### Checking it works

```bash
curl https://your-api-host/api/health
```

Expect `dataset_built: true`. If it is false, the corpus did not build and
`/api/reference` will return 503, which surfaces in the app as an empty list of
cities and treatments.

Then open the site and check `/api/health/providers` through the settings panel:
it reports which model is serving each role, or says plainly that none is
reachable.

---

## 4. What a push actually does

Worth being clear about, because it surprises people: **the tests on GitHub and
the deploy are two separate things happening at the same time, and neither waits
for the other.**

Push to `main` and Vercel starts building the frontend immediately. GitHub
Actions starts the test run immediately. Whichever finishes first finishes
first. A red test run does not stop the deploy, does not roll it back, and does
not stop the live site updating: by the time the tests report, the new frontend
is usually already serving. The same is true of the API if the host is set to
deploy on push.

So a broken commit reaches the live site. The tests tell you afterwards.

If that is not what you want, the gate belongs on the deploy rather than in this
repository:

- **Vercel**: project settings, Git, "Ignored Build Step", or protect `main` so
  work lands through pull requests that cannot merge until checks pass.
- **The API host**: turn auto-deploy off and deploy manually, or point it at a
  tag rather than a branch.

The pull request route is the one worth having. Branch protection with the
Backend, Frontend and API image checks required means nothing reaches `main`
that has not passed, and then "deploys on push to `main`" is safe by
construction.

---

## 5. What to expect on a free tier

- **Cold starts.** Free container hosts sleep after inactivity. The first
  request wakes the container, which takes 30 seconds or so. The health check
  path keeps it warm on some hosts.
- **Memory.** OpenCV and PyMuPDF together want more than a 256 MB instance
  gives you once a 300 DPI page is in memory. 512 MB is comfortable.
- **Model latency.** A gated or slow model makes an upload take a minute. The
  activity panel exists partly so that minute is visible rather than mysterious.

---

## 6. Running it without a model

Leave `OLLAMA_API_KEY` unset and the app runs its deterministic path: rule-based
extraction, no verification loop, no vision escalation. Accuracy drops from
94.9% to 93.4% and missed fields roughly double, but nothing crashes and the
interface says which mode it is in.

This is also how CI runs, so the deterministic path is exercised on every push
rather than being a claim nobody checks.
