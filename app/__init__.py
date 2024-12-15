from flask import Flask
from dotenv import load_dotenv


load_dotenv()

app = Flask(__name__)


from app.main import main_blueprint

app.register_blueprint(main_blueprint)

