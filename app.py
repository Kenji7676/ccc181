"""CCC181 Week 2: a "Hello, Flask" starter app.

Run it with:
    flask --app app run --debug
then open http://127.0.0.1:5000
"""
from flask import Flask, render_template, abort
import re

app = Flask(__name__)

from flask import Flask, abort, flash, redirect, render_template, request, url_for

app = Flask(__name__)
app.secret_key = "dev-only-change-me"

SERVICES = [
    {"id": 1, "name": "Buy merch"},
    {"id": 2, "name": "Claim pre-order"},
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
    {"number": 2, "name": "Michael Adeva",
     "email": "michael.adeva@g.msuiit.edu.ph",
     "service_id": 1, "status": "called",
     "item": "Langkit tote bag", "size": "N/A", "quantity": 1},
]

def queue_key(t):
    """Paying customers go first; ties go to the lower ticket number."""
    return (t.get("stage") != "paying", t["number"])


def find_ticket(ticket_id):
    t = next((t for t in TICKETS if t["number"] == ticket_id), None)
    if t is None:
        abort(404)
    return t


def people_ahead(t):
    if t["status"] != "waiting":
        return 0
    return sum(
        1 for o in TICKETS
        if o["status"] == "waiting"
        and o["service_id"] == t["service_id"]
        and queue_key(o) < queue_key(t)
    )

@app.route("/")
def index():
    # render_template looks inside the templates/ folder and passes
    # keyword arguments to the template as variables.
    return render_template("index.html", name="Ana", tickets=TICKETS)


@app.get("/queue/<int:ticket_id>")
def ticket(ticket_id):
    t = find_ticket(ticket_id)
    service = next((s for s in SERVICES if s["id"] == t["service_id"]), None)
    return render_template("ticket.html", ticket=t, service=service, ahead=people_ahead(t))


@app.post("/queue/<int:ticket_id>/ready")
def ready(ticket_id):
    t = find_ticket(ticket_id)
    if t["status"] == "waiting":
        t["stage"] = "paying"
        flash("Got it! You’ll be called before customers who are still browsing.", "success")
    return redirect(url_for("ticket", ticket_id=ticket_id))


@app.post("/queue/<int:ticket_id>/leave")
def leave(ticket_id):
    t = find_ticket(ticket_id)
    if t["status"] in ("waiting", "called"):
        t["status"] = "no-show"
        flash(f"You left the queue. Ticket A-{t['number']:03d} is no longer active.", "info")
    return redirect(url_for("index"))


@app.route("/hello")
def hello():
    # The plain-string version from the Routes slide.
    return "Hello, CCC181!"

STAGES = {"browsing", "paying"}
STUDENT_ID_RE = re.compile(r"^\d{4}-\d{4}$")


def queue_summary():
    waiting = [t for t in TICKETS if t["status"] == "waiting"]
    return {
        "total": len(waiting),
        "paying": sum(1 for t in waiting if t.get("stage") == "paying"),
        "browsing": sum(1 for t in waiting if t.get("stage") == "browsing"),
    }


@app.get("/join")
def join_form():
    return render_template("join.html", form={}, errors={}, summary=queue_summary())


@app.post("/join")
def join():
    form = request.form
    name = form.get("name", "").strip()
    student_id = form.get("student_id", "").strip()
    stage = form.get("stage", "")
    errors = {}

    if not name:
        errors["name"] = "Enter your name"
    elif len(name) > 80:
        errors["name"] = "Name must be 80 characters or fewer."

    if not STUDENT_ID_RE.match(student_id):
        errors["student_id"] = "Invalid format: YYYY-NNNN"

    if stage not in STAGES:
        errors["stage"] = "Choose one option."

    if errors:
        flash("Please fix the highlighted fields.", "danger")
        return render_template("join.html", form=form, errors=errors,
                               summary=queue_summary()), 400

    number = max((t["number"] for t in TICKETS), default=0) + 1
    TICKETS.append({
        "number": number,
        "name": name,
        "student_id": student_id,
        "stage": stage,
        "service_id": SERVICES[0]["id"],  # wireframe has no service picker, so use a default
        "status": "waiting",
    })
    flash(f"You're in the queue! Your ticket number is #{number}.", "success")
    return redirect(url_for("ticket", ticket_id=number))

@app.route("/staff")
def staff_dashboard():
    return "Staff dashboard coming soon"

if __name__ == "__main__":
    # Lets you also start the app with: python app.py
    app.run(debug=True)
