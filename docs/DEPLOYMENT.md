# Deploying CoverPath

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
docker build -f backend/Dockerfile -t coverpath-api .
docker run -p 8000:8000 --env-file backend/.env coverpath-api

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

`CORS_ORIGINS` is the one that gets forgotten. Miss it and the site loads
perfectly and every request fails in the browser console.

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
  `https://coverpath-api.onrender.com`, with no trailing slash

`frontend/vercel.json` already handles the rest: the SPA rewrite so a deep link
like `/#/hospitals` resolves, and long cache headers on the hashed assets.

`VITE_API_BASE` is read at **build** time, not run time. Changing it means
redeploying, not just restarting.

---

## 3. Wiring the two together

The two settings have to name each other:

```
API:       CORS_ORIGINS=https://coverpath.vercel.app
Frontend:  VITE_API_BASE=https://coverpath-api.onrender.com
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

## 4. What to expect on a free tier

- **Cold starts.** Free container hosts sleep after inactivity. The first
  request wakes the container, which takes 30 seconds or so. The health check
  path keeps it warm on some hosts.
- **Memory.** OpenCV and PyMuPDF together want more than a 256 MB instance
  gives you once a 300 DPI page is in memory. 512 MB is comfortable.
- **Model latency.** A gated or slow model makes an upload take a minute. The
  activity panel exists partly so that minute is visible rather than mysterious.

---

## 5. Running it without a model

Leave `OLLAMA_API_KEY` unset and the app runs its deterministic path: rule-based
extraction, no verification loop, no vision escalation. Accuracy drops from
94.9% to 93.4% and missed fields roughly double, but nothing crashes and the
interface says which mode it is in.

This is also how CI runs, so the deterministic path is exercised on every push
rather than being a claim nobody checks.
