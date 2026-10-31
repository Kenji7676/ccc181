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
    {"id": 1, "name": "Buy merch", "uses_stage": True},
    {"id": 2, "name": "Claim pre-order", "uses_stage": False},
]

TICKETS = []

STAGES = {"browsing", "paying"}
STUDENT_ID_RE = re.compile(r"^\d{4}-\d{4}$")

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

@app.get("/queue/<int:ticket_id>/status.json")
def ticket_status(ticket_id):
    t = find_ticket(ticket_id)
    return {
        "status": t["status"],
        "stage": t.get("stage", "browsing"),
        "ahead": people_ahead(t),
    }

@app.route("/hello")
def hello():
    # The plain-string version from the Routes slide.
    return "Hello, CCC181!"

def queue_summary():
    waiting = [t for t in TICKETS if t["status"] == "waiting"]
    return {
        "total": len(waiting),
        "paying": sum(1 for t in waiting if t.get("stage") == "paying"),
        "browsing": sum(1 for t in waiting if t.get("stage") == "browsing"),
    }


def join_page(form, errors, code=200):
    picked = next((s for s in SERVICES if str(s["id"]) == form.get("service_id", "")), None)
    show_stage = bool(picked and picked.get("uses_stage"))
    return render_template("join.html", form=form, errors=errors,
                           summary=queue_summary(), services=SERVICES,
                           show_stage=show_stage), code


@app.get("/join")
def join_form():
    return join_page({}, {})


@app.post("/join")
def join():
    form = request.form
    name = form.get("name", "").strip()
    student_id = form.get("student_id", "").strip()
    service_id = form.get("service_id", type=int)
    service = next((s for s in SERVICES if s["id"] == service_id), None)
    errors = {}

    if not name:
        errors["name"] = "Enter your full name."
    elif len(name) > 80:
        errors["name"] = "Name must be 80 characters or fewer."

    if not STUDENT_ID_RE.match(student_id):
        errors["student_id"] = "Enter your student ID like 2024-0001."

    if service is None:
        errors["service_id"] = "Choose a service."

    # The browsing / ready-to-pay question only applies to services that use it
    stage = None
    if service and service.get("uses_stage"):
        stage = form.get("stage", "")
        if stage not in STAGES:
            errors["stage"] = "Choose one option."

    if errors:
        flash("Please fix the highlighted fields.", "danger")
        return join_page(form, errors, 400)

    number = max((t["number"] for t in TICKETS), default=0) + 1
    TICKETS.append({
        "number": number,
        "name": name,
        "student_id": student_id,
        "stage": stage,              # None for Claim pre-order
        "service_id": service["id"],
        "status": "waiting",
    })
    flash(f"You're in the queue! Your ticket number is #{number}.", "success")
    return redirect(url_for("ticket", ticket_id=number))

@app.get("/staff")
def staff_dashboard():
    service_id = request.args.get("service_id", type=int)

    active = [t for t in TICKETS if t["status"] in ("waiting", "called")]
    if service_id:
        active = [t for t in active if t["service_id"] == service_id]
    active.sort(key=queue_key)

    called = [t for t in active if t["status"] == "called"]
    waiting = [t for t in active if t["status"] == "waiting"]
    paying = [t for t in waiting if t.get("stage") == "paying"]
    browsing = [t for t in waiting if t.get("stage") != "paying"]

    return render_template(
        "staff.html",
        services=SERVICES,
        names={s["id"]: s["name"] for s in SERVICES},
        selected=service_id,
        called=called,
        current=min(called, key=lambda t: t["number"]) if called else None,
        paying=paying,
        browsing=browsing,
        next_ticket=waiting[0] if waiting else None,
        total=len(waiting),
    )


@app.post("/staff/call-next")
def call_next():
    service_id = request.form.get("service_id", type=int)
    waiting = [t for t in TICKETS if t["status"] == "waiting"
               and (not service_id or t["service_id"] == service_id)]
    if not waiting:
        flash("No one is waiting.", "warning")
    else:
        nxt = min(waiting, key=queue_key)
        nxt["status"] = "called"
        flash(f"Called ticket A-{nxt['number']:03d} · {nxt['name']}.", "info")
    return redirect(url_for("staff_dashboard", service_id=service_id))


@app.post("/staff/tickets/<int:ticket_id>/<action>")
def staff_action(ticket_id, action):
    new_status = {"call": "called", "serve": "served", "no-show": "no-show"}.get(action)
    if new_status is None:
        abort(404)
    t = find_ticket(ticket_id)
    t["status"] = new_status
    flash(f"Ticket A-{t['number']:03d} marked {new_status}.", "info")
    return redirect(url_for("staff_dashboard",
                            service_id=request.form.get("service_id", type=int)))
