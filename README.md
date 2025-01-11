python -m venv .venv
pip install -r requirements.txt
docker-compose build && docker-compose up -d
