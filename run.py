"""Ponto de entrada: `flask --app run run` em desenvolvimento, `gunicorn run:app` em produção."""
from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run()
