# Daymark static preview

A static preview of the Daymark task dashboard. It uses sample content only; sign-in, task management, search, filters, and pagination are not connected to a backend.

## Preview locally

Open `static/index.html` in a browser, or serve the static folder:

```powershell
python -m http.server 8000 --directory static
```

Then visit http://localhost:8000/.

## Deploy to Vercel

Connect this repository to Vercel. The `vercel.json` configuration publishes the `static` folder; no build command or Python runtime is required. Set the Vercel project root to the repository root.
