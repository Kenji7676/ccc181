import os
import re

from dotenv import load_dotenv
from flask import Flask, abort, flash, redirect, render_template, request, url_for
from flask_migrate import Migrate
from sqlalchemy import func, and_, or_, case
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload

from models import Service, Ticket, User, db

load_dotenv()

app = Flask(__name__)
app.secret_key = "dev-only-change-me"  # Week 11 moves this into an environment variable
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ["DATABASE_URL"]
app.config["SQLALCHEMY_ECHO"] = os.environ.get("SQLALCHEMY_ECHO") == "1"

db.init_app(app)
migrate = Migrate(app, db)

from datetime import timedelta, timezone

STAGES = {"browsing", "paying"}
STUDENT_ID_RE = re.compile(r"^\d{4}-\d{4}$")

def active_services():
    """Services shown on the join form (switched-off ones are hidden)."""
    return db.session.scalars(
        db.select(Service).where(Service.is_active).order_by(Service.name)
    ).all()

def all_services():
    """Every service, including switched-off ones (for the staff screens)."""
    return db.session.scalars(db.select(Service).order_by(Service.name)).all()

def queue_order():
    """Call order: paying customers first, then whoever joined earliest."""
    return (case((Ticket.stage == "paying", 0), else_=1), Ticket.created_at, Ticket.id)

def queue_summary():
    """Counts for the Join page, computed from the tickets table."""
    rows = db.session.execute(
        db.select(Ticket.stage, func.count())
        .where(Ticket.status == "waiting")
        .group_by(Ticket.stage)
    ).all()
    counts = {stage: n for stage, n in rows}
    return {
        "total": sum(counts.values()),
        "paying": counts.get("paying", 0),
        "browsing": counts.get("browsing", 0),
    }

def stage_question_shown(form):
    """True if the chosen service asks 'still browsing or ready to pay?'."""
    sid = str(form.get("service_id", ""))
    service = db.session.get(Service, int(sid)) if sid.isdigit() else None
    return bool(service and service.uses_stage)

def join_page(form, errors, code=200):
    return render_template(
        "join.html",
        form=form,
        errors=errors,
        services=active_services(),
        summary=queue_summary(),
        show_stage=stage_question_shown(form),
    ), code

def active_ticket(student_id, service_id):
    """The waiting or called ticket this student already holds for a service."""
    return db.session.scalar(
        db.select(Ticket)
        .join(User)
        .where(
            User.student_id == student_id,
            Ticket.service_id == service_id,
            Ticket.status.in_(("waiting", "called")),
        )
    )

def find_ticket(ticket_id):
    t = db.session.get(Ticket, ticket_id)
    if t is None:
        abort(404)
    return t


def people_ahead(t):
    """Waiting tickets for the same service that will be called before t.
    Paying customers go first, then the earliest to join."""
    if t.status != "waiting":
        return 0
    earlier = or_(
        Ticket.created_at < t.created_at,
        and_(Ticket.created_at == t.created_at, Ticket.id < t.id),
    )
    if t.stage == "paying":
        ahead = and_(Ticket.stage == "paying", earlier)
    else:
        ahead = or_(
            Ticket.stage == "paying",
            and_(or_(Ticket.stage.is_(None), Ticket.stage != "paying"), earlier),
        )
    return db.session.scalar(
        db.select(func.count())
        .select_from(Ticket)
        .where(
            Ticket.service_id == t.service_id,
            Ticket.status == "waiting",
            ahead,
        )
    )

#home
@app.route("/")
def index():
    return render_template("index.html")

#join
@app.get("/join")
def join_form():
    return join_page({}, {})

@app.post("/join")
def join():
    form = request.form
    name = form.get("name", "").strip()
    student_id = form.get("student_id", "").strip()
    service_id = form.get("service_id", type=int)
    service = db.session.get(Service, service_id) if service_id else None
    if service is not None and not service.is_active:
        service = None

    errors = {}
    if not name or len(name) > 80:
        errors["name"] = "Enter your full name (up to 80 characters)."
    if not STUDENT_ID_RE.match(student_id):
        errors["student_id"] = "Enter your student ID like 2024-0001."
    if service is None:
        errors["service_id"] = "Choose a service."

    # The browsing / ready-to-pay question only applies to some services
    stage = None
    if service is not None and service.uses_stage:
        stage = form.get("stage", "")
        if stage not in STAGES:
            errors["stage"] = "Choose one option."

    if errors:
        flash("Please fix the highlighted fields.", "danger")
        return join_page(form, errors, 400)

    # Already holding an active ticket for this service? Show it, do not add another
    existing = active_ticket(student_id, service.id)
    if existing is not None:
        flash(f"You already have ticket {existing.code} for {service.name}.", "info")
        return redirect(url_for("ticket", ticket_id=existing.id))

    # Reuse the student's row if they have joined before
    user = db.session.scalar(db.select(User).filter_by(student_id=student_id))
    if user is None:
        user = User(name=name, student_id=student_id)
    else:
        user.name = name

    ticket = Ticket(user=user, service=service, stage=stage)
    db.session.add(ticket)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        # A double tap or a second tab got there first: show the ticket that exists
        existing = active_ticket(student_id, service.id)
        if existing is not None:
            flash(f"You already have ticket {existing.code} for {service.name}.", "info")
            return redirect(url_for("ticket", ticket_id=existing.id))
        flash("Something went wrong saving your ticket. Please try again.", "danger")
        return join_page(form, {}, 409)

    flash(f"You joined the queue. Your ticket is {ticket.code}.", "success")
    return redirect(url_for("ticket", ticket_id=ticket.id))

@app.get("/queue/<int:ticket_id>")
def ticket(ticket_id):
    t = find_ticket(ticket_id)
    return render_template("ticket.html", ticket=t, service=t.service,
                           ahead=people_ahead(t))

@app.post("/queue/<int:ticket_id>/ready")
def ready(ticket_id):
    t = find_ticket(ticket_id)
    if t.status == "waiting" and t.stage == "browsing":
        t.stage = "paying"
        db.session.commit()
        flash("Got it! You’ll be called before customers who are still browsing.", "success")
    return redirect(url_for("ticket", ticket_id=ticket_id))


@app.post("/queue/<int:ticket_id>/leave")
def leave(ticket_id):
    t = find_ticket(ticket_id)
    if t.status in ("waiting", "called"):
        t.status = "left"
        db.session.commit()
        flash(f"You left the queue. Ticket {t.code} is no longer active.", "info")
    return redirect(url_for("index"))


@app.get("/queue/<int:ticket_id>/status.json")
def ticket_status(ticket_id):
    t = find_ticket(ticket_id)
    return {"status": t.status, "stage": t.stage, "ahead": people_ahead(t)}

#staff
@app.get("/staff")
def staff_dashboard():
    service_id = request.args.get("service_id", type=int)
    stmt = (
        db.select(Ticket)
        .where(Ticket.status.in_(("waiting", "called")))
        .options(selectinload(Ticket.user), selectinload(Ticket.service))
        .order_by(*queue_order())
    )
    if service_id:
        stmt = stmt.where(Ticket.service_id == service_id)
    active = db.session.scalars(stmt).all()

    called = sorted((t for t in active if t.status == "called"),
                    key=lambda t: (t.called_at or t.created_at, t.id))
    waiting = [t for t in active if t.status == "waiting"]
    paying = [t for t in waiting if t.stage == "paying"]
    browsing = [t for t in waiting if t.stage != "paying"]

    services = all_services()
    return render_template(
        "staff.html",
        services=services,
        names={s.id: s.name for s in services},
        selected=service_id,
        called=called,
        current=called[0] if called else None,
        paying=paying,
        browsing=browsing,
        next_ticket=waiting[0] if waiting else None,
        total=len(waiting),
    )

@app.post("/staff/call-next")
def call_next():
    service_id = request.form.get("service_id", type=int)
    stmt = (
        db.select(Ticket)
        .where(Ticket.status == "waiting")
        .order_by(*queue_order())
        .limit(1)
        .with_for_update(skip_locked=True)  # two staff pressing at once call different tickets
    )
    if service_id:
        stmt = stmt.where(Ticket.service_id == service_id)
    nxt = db.session.scalar(stmt)

    if nxt is None:
        flash("No one is waiting.", "warning")
    else:
        nxt.status = "called"
        nxt.called_at = func.now()
        db.session.commit()
        flash(f"Called ticket {nxt.code} · {nxt.user.name}.", "info")
    return redirect(url_for("staff_dashboard", service_id=service_id))

# Which current statuses each action may start from
ALLOWED_FROM = {
    "call": {"waiting"},
    "serve": {"called"},
    "no-show": {"waiting", "called"},
}

@app.post("/staff/tickets/<int:ticket_id>/delete")
def delete_ticket(ticket_id):
    t = find_ticket(ticket_id)
    code = t.code
    db.session.delete(t)  # hard delete: the row is gone for good
    db.session.commit()
    flash(f"Ticket {code} was deleted.", "warning")
    return redirect(url_for("staff_dashboard",
                            service_id=request.form.get("service_id", type=int)))

@app.post("/staff/tickets/<int:ticket_id>/<action>")
def staff_action(ticket_id, action):
    new_status = {"call": "called", "serve": "served", "no-show": "no-show"}.get(action)
    if new_status is None:
        abort(404)
    t = find_ticket(ticket_id)

    if t.status not in ALLOWED_FROM[action]:
        # a stale page or a double click: do not overwrite what already happened
        flash(f"Ticket {t.code} is already {t.status}.", "warning")
    else:
        t.status = new_status
        if new_status == "served":
            t.served_at = func.now()
        if new_status == "called":
            t.called_at = func.now()
        db.session.commit()
        flash(f"Ticket {t.code} marked {new_status}.", "info")
    return redirect(url_for("staff_dashboard",
                            service_id=request.form.get("service_id", type=int)))

@app.get("/staff/services")
def services_list():
    return render_template("services.html", services=all_services())

@app.post("/staff/services")
def service_create():
    name = request.form.get("name", "").strip()
    uses_stage = request.form.get("uses_stage") == "on"
    if not name or len(name) > 60:
        flash("Enter a service name (up to 60 characters).", "danger")
        return redirect(url_for("services_list"))
    db.session.add(Service(name=name, uses_stage=uses_stage))
    try:
        db.session.commit()
        flash(f"Service “{name}” added.", "success")
    except IntegrityError:
        db.session.rollback()
        flash(f"A service named “{name}” already exists.", "danger")
    return redirect(url_for("services_list"))

@app.post("/staff/services/<int:service_id>")
def service_edit(service_id):
    s = db.get_or_404(Service, service_id)
    name = request.form.get("name", "").strip()
    if not name or len(name) > 60:
        flash("Enter a service name (up to 60 characters).", "danger")
        return redirect(url_for("services_list"))
    s.name = name
    s.uses_stage = request.form.get("uses_stage") == "on"
    s.is_active = request.form.get("is_active") == "on"  # unticked boxes are not sent
    try:
        db.session.commit()
        flash(f"Service “{name}” saved.", "success")
    except IntegrityError:
        db.session.rollback()
        flash(f"A service named “{name}” already exists.", "danger")
    return redirect(url_for("services_list"))

@app.post("/staff/services/<int:service_id>/delete")
def service_delete(service_id):
    s = db.get_or_404(Service, service_id)
    name = s.name  # read it before the row is gone
    if s.tickets:
        flash(f"“{name}” has tickets, so it cannot be deleted. Turn it off instead.", "danger")
        return redirect(url_for("services_list"))
    db.session.delete(s)
    try:
        db.session.commit()
        flash(f"Service “{name}” deleted.", "warning")
    except IntegrityError:
        db.session.rollback()
        flash(f"“{name}” is still in use, so it cannot be deleted.", "danger")
    return redirect(url_for("services_list"))

#database
@app.cli.command("seed")
def seed():
    """Add the starting services if they are not there yet."""
    starting = [
        ("Buy merch", True),         # asks "still browsing or ready to pay?"
        ("Claim pre-order", False),  # no browsing question
    ]
    for name, uses_stage in starting:
        exists = db.session.scalar(db.select(Service).filter_by(name=name))
        if exists is None:
            db.session.add(Service(name=name, uses_stage=uses_stage))
    db.session.commit()
    print("Services are ready.")

#time
PH_TIME = timezone(timedelta(hours=8))  # Philippine time has no daylight saving


@app.template_filter("local")
def local_time(value):
    """Show a database time in Philippine time, e.g. Nov 05, 08:01 AM."""
    return value.astimezone(PH_TIME).strftime("%b %d, %I:%M %p") if value else ""