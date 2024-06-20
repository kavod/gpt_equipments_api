import datetime
import jwt
from flask import Flask, request, jsonify
from functools import wraps
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

secret_key = "mysecretkey"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///equipments.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class Equipment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    date_achat = db.Column(db.String(100), nullable=False)
    prix_achat = db.Column(db.Float, nullable=False)

# Initialiser la base de données
with app.app_context():
    db.create_all()

@app.route("/login", methods=["POST"])
def login():
    username = request.json.get("username", "")
    password = request.json.get("password", "")

    # Verify username and password
    if username != "admin" or password != "secret":
        return {"error": "Invalid username or password"}, 401

    # Generate JWT token
    token = jwt.encode(
        {"username": username, "exp": datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=30)},
        secret_key,
        algorithm="HS256"
    )
    return {"token": token}

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get("Authorization", None)
        if not token:
            return {"error": "Token is missing"}, 401
        try:
            jwt.decode(token, secret_key, algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            return {"error": "Token has expired"}, 401
        except jwt.DecodeError:
            return {"error": "Token is invalid"}, 401
        return f(*args, **kwargs)
    return decorated

@app.route("/equipments", methods=["GET"])
@requires_auth
def list_equipments():
    equipments = Equipment.query.all()
    equipments_list = [{"id": eq.id, "name": eq.name, "date_achat": eq.date_achat, "prix_achat": eq.prix_achat} for eq in equipments]
    return jsonify({"equipments": equipments_list})

@app.route("/equipments", methods=["POST"])
@requires_auth
def add_equipment():
    data = request.get_json()
    new_equipment = Equipment(name=data["name"], date_achat=data["date_achat"], prix_achat=data["prix_achat"])
    db.session.add(new_equipment)
    db.session.commit()
    return jsonify({"message": "Equipment added successfully."})

if __name__ == "__main__":
    app.run(port=8080)
