uvicorn main:app --reload --port 8001# realtime-transcription

## 1 Run local

### Install the dependencies
```bash
pip install -r requirements.txt
```

###  Launch the app
```bash
streamlit run streamlit_app.py
```
# realtime-transcription with server

## 2 Run on serverside

###  Launch the server host="0.0.0.0", port=8000
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
Open your browser and navigate to http://localhost:8000 to access the index.html