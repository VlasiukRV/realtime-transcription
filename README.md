# REAL TIME TRANSLATION

> 🛠️ This project is based on 
> 
> - **Conda** (for environment management) 
> 
> - **Uvicorn** (as the ASGI server for FastAPI).
> 

## 1. Run Locally

### ✅ Step 1: Create and Activate Conda Environment

If you haven't created the environment yet, do so with:

```bash
conda create -n transcription python=3.11
conda activate transcription
```

###  ✅ Step 2: Install Dependencies

Install all required Python packages using pip:

```bash
pip install -r requirements.txt
```
### ✅ Step 3: Launch the App

Start the FastAPI server using Uvicorn, which is a lightning-fast ASGI server, with:

````bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
````

### ✅ Step 4: Open in Browser

Open your browser and navigate to:

```browser
http://localhost:8000
```