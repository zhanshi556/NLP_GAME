# nlp_1

## Project Structure

```
.
├─ frontend/              # Vue 前端
│  ├─ src/
│  │  ├─ main.js
│  │  ├─ App.vue
│  │  └─ components/
│  │      └─ GameView.vue
├─ backend/               # Python FastAPI 后端
│  ├─ main.py
│  └─ game_logic.py
├─ requirements.txt
└─ README.md
```

## Run Backend

```bash
pip install -r requirements.txt
uvicorn backend.main:app --reload
```

Open http://127.0.0.1:8000/docs to test the API.
