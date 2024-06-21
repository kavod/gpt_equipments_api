import datetime
import jwt
from flask import Flask, request, jsonify
from functools import wraps
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import inspect, Column, DateTime, String, Float, Integer
from sqlalchemy.sql import func

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
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = db.Column(db.DateTime(timezone=True), onupdate=func.now(), server_default=func.now(), nullable=False)

    def  __repr__(self):
        ret = "ID: "+str(self.id) + "\nName: "+str(self.name)+ "\nDate achat: "+str(self.date_achat)
        ret += "\nPrix achat: "+str(self.prix_achat)
        ret += "\nCreated at: "+str(self.created_at)
        ret += "\nUpdated at: "+str(self.updated_at)
        return ret


# Initialiser la base de données et vérifier les colonnes
with app.app_context():
    db.create_all()

    inspector = inspect(db.engine)
    columns = inspector.get_columns('equipment')
    column_names = [column['name'] for column in columns]

    if 'created_at' not in column_names:
        with db.engine.connect() as connection:
            connection.execute('ALTER TABLE equipment ADD COLUMN created_at DATETIME DEFAULT (DATETIME(\'now\')) NOT NULL')
    if 'updated_at' not in column_names:
        with db.engine.connect() as connection:
            connection.execute('ALTER TABLE equipment ADD COLUMN updated_at DATETIME DEFAULT (DATETIME(\'now\')) NOT NULL')


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

def get_equipment_or_404(equipment_id):
    equipment = Equipment.query.get(equipment_id)
    if equipment is None:
        abort(404, description="Resource not found")
    return equipment

@app.route("/equipments", methods=["GET"])
@requires_auth
def list_equipments():
    equipments = Equipment.query.all()
    equipments_list = [{"id": eq.id, "name": eq.name, "date_achat": eq.date_achat, "prix_achat": eq.prix_achat, "created_at": eq.created_at, "updated_at": eq.updated_at} for eq in equipments]
    return jsonify({"equipments": equipments_list})

@app.route("/equipments", methods=["POST"])
@requires_auth
def add_equipment():
    data = request.get_json()
    new_equipment = Equipment(name=data["name"], date_achat=data["date_achat"], prix_achat=data["prix_achat"])
    db.session.add(new_equipment)
    print(new_equipment)
    db.session.commit()
    return jsonify({"message": "Equipment added successfully."})


@app.route("/equipments/<int:id>", methods=["PUT"])
@requires_auth
def update_equipment(id):
    data = request.get_json()
    equipment = get_equipment_or_404(id)

    equipment.name = data.get("name", equipment.name)
    equipment.date_achat = data.get("date_achat", equipment.date_achat)
    equipment.prix_achat = data.get("prix_achat", equipment.prix_achat)
    db.session.commit()

    return jsonify({"message": "Equipment updated successfully."})


@app.route("/equipments/<int:id>", methods=["DELETE"])
@requires_auth
def delete_equipment(id):
    equipment = get_equipment_or_404(id)
    db.session.delete(equipment)
    db.session.commit()

    return jsonify({"message": "Equipment deleted successfully."})

if __name__ == "__main__":
    app.run(host='0.0.0.0',port=8080)
