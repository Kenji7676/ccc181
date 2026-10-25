"""CCC181 Week 2: a "Hello, Flask" starter app.

Run it with:
    flask --app app run --debug
then open http://127.0.0.1:5000
"""
from flask import Flask, render_template

app = Flask(__name__)

SERVICES = [
    {"id": 1, "name": "Buy merch"},
    {"id": 2, "name": "Claim pre-order"},
    {"id": 3, "name": "Payment / inquiry"},
]

SIZES = ["XS", "S", "M", "L", "XL", "2XL"]

TICKETS = [
    {"number": 1, "name": "Francis Geronimo",
     "email": "francis.geronimo@g.msuiit.edu.ph",
     "service_id": 1, "status": "waiting",
     "item": "Langkit T-shirt", "size": "M", "quantity": 2},
    {"number": 2, "name": "Cris Pondoyo",
     "email": "cris.pondoyo@g.msuiit.edu.ph",
     "service_id": 2, "status": "waiting",
     "item": "Langkit hoodie", "size": "L", "quantity": 1},
    {"number": 3, "name": "Michael Adeva",
     "email": "michael.adeva@g.msuiit.edu.ph",
     "service_id": 1, "status": "called",
     "item": "Langkit tote bag", "size": "N/A", "quantity": 1},
]


@app.route("/")
def index():
    # render_template looks inside the templates/ folder and passes
    # keyword arguments to the template as variables.
    return render_template("index.html", name="Ana", tickets=TICKETS)


@app.route("/queue/<int:ticket_id>")
def ticket(ticket_id):
    # <int:ticket_id> only matches numbers, so /queue/abc returns 404.
    return render_template("ticket.html", ticket_id=ticket_id)


@app.route("/hello")
def hello():
    # The plain-string version from the Routes slide.
    return "Hello, CCC181!"


if __name__ == "__main__":
    # Lets you also start the app with: python app.py
    app.run(debug=True)
