# Publish the source folder on GitHub

Suggested repository name: **bankops-copilot**

Suggested description:

> Treasury analysis copilot with LangGraph, read-only SQL tools, date-aware policy RAG, optional GigaChat, FastAPI, Streamlit and reproducible evaluation. Synthetic data.

Suggested topics: `python`, `langgraph`, `fastapi`, `rag`, `gigachat`, `ai-agents`, `fintech`, `streamlit`, `llm-evaluation`.

## Upload from the GitHub website

1. Extract the ZIP. Open the inner `bankops-copilot` folder.
2. Create an empty GitHub repository named `bankops-copilot`.
3. Choose **uploading an existing file** or **Add file → Upload files**.
4. Upload the folder's contents so `README.md` is at the repository root. Do not upload only the ZIP or nest everything under another `bankops-copilot` directory.
5. Ensure `.github/workflows/ci.yml`, `.gitignore`, `.dockerignore` and `.env.example` are included. Some file pickers hide files whose names start with a dot.
6. Commit the files and open the Actions tab to see CI results.

Upload the delivered source before running the app, or exclude `.venv/`, `runtime/`, caches and any `.env`
you created. `.env.example` is safe; `.env` can contain credentials and must stay private.
The GitHub website does not apply `.gitignore` to files you manually choose to upload.

## Git command-line route

In the extracted folder, replace YOUR-USERNAME with your own account name:

```bash
git init
git add .
git commit -m "Build treasury copilot with SQL, policy RAG and evaluation"
git branch -M main
git remote add origin https://github.com/YOUR-USERNAME/bankops-copilot.git
git push -u origin main
```

Do not invent an employment relationship with Sber in the repository name, description or CV.
The README already distinguishes implemented behavior, optional integrations and untested live paths.

## Portfolio wording

“Built an independent treasury-analysis copilot using LangGraph, FastAPI, read-only SQL tools and effective-date
policy retrieval. Added a Streamlit dashboard, optional GigaChat integration, synthetic regression fixtures,
and CI checks.”

This describes a project, not commercial banking experience. Add a screenshot from your own successful local
run and record a short demonstration once you can explain the calculation and evidence trace.
