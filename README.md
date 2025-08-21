# About
Listo is a minimal, lightning-fast to-do app built with FastAPI, that’s started as a skill-development project. 

# Local Deployment
You can run this application locally by following the following step-by-step process.
1. **Fork this repository**
2. **Create a virtual environment for your python project**
   ```bash
   python -m venv .venv
   ```
3. **Activate the virtual environment**
   ```bash
   .venv/Scripts/activate
   ```
5. **Install the project's dependencies**
   ```bash
   pip install -r requirements.txt
   ```
6. **Create a `.env` file and add the following parameters**
   ```text
   SECRET_KEY=some-secret-local-key
   ACCESS_TOKEN_EXPIRE_MINUTES=30
   ALGORITHM=HS256
   ```
7. **Run the following command on your terminal**
   ```bash
   uvicorn main:app --reload
   ```
