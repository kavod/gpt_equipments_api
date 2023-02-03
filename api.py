import jwt
import datetime
from flask import Flask, request

app = Flask(__name__)

secret_key = "mysecretkey"

@app.route("/login", methods=["POST"])
def login():
    username = request.json.get("username", "")
    password = request.json.get("password", "")

    # Verify username and password
    if username != "admin" or password != "secret":
        return {"error": "Invalid username or password"}, 401

    # Generate JWT token
    token = jwt.encode({"username": username, "exp": datetime.datetime.utcnow() + datetime.timedelta(minutes=30)}, secret_key)
    return {"token": token.decode("utf-8")}

def requires_auth(f):
    def decorated(*args, **kwargs):
        token = request.headers.get("Authorization", None)
        if not token:
            return {"error": "Token is missing"}, 401
        try:
            jwt.decode(token, secret_key)
        except jwt.ExpiredSignatureError:
            return {"error": "Token has expired"}, 401
        except jwt.DecodeError:
            return {"error": "Token is invalid"}, 401
        return f(*args, **kwargs)
    return decorated

@app.route("/equipments", methods=["GET"])
@requires_auth
def list_equipments():
    # Get all the equipment data from the database
    cursor = db.cursor()
    query = "SELECT * FROM mt_equipments"
    cursor.execute(query)
    result = cursor.fetchall()

    # Format the equipment data as a list of dictionaries
    equipments = []
    for equipment in result:
        equipments.append({"id": equipment[0], "name": equipment[1], "date_achat": equipment[2], "prix_achat": equipment[3]})

    # Return the equipment data as a JSON response
    return jsonify({"equipments": equipments})

@app.route("/equipments", methods=["POST"])
@requires_auth
def add_equipment():
    # Get the equipment data from the request
    data = request.get_json()
    name = data["name"]
    date_achat = data["date_achat"]
    prix_achat = data["prix_achat"]

    # Insert the equipment data into the database
    cursor = db.cursor()
    query = "INSERT INTO mt_equipments (name, date_achat, prix_achat) VALUES (%s, %s, %s)"
    values = (name, date_achat, prix_achat)
    cursor.execute(query, values)
    db.commit()

    # Return a success message
    return jsonify({"message": "Equipment added successfully."})
