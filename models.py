from datetime import datetime

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    String,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

db = SQLAlchemy()

# Allowed values. The app imports these, and the CHECK constraints below are
# built from them, so the code and the database can never disagree.
ROLES = ("customer", "staff")
STAGES = ("browsing", "paying")
STATUSES = ("waiting", "called", "served", "no-show", "left")


def _in_list(column, values):
    """Build "column IN ('a', 'b')" for a CHECK constraint."""
    return f"{column} IN ({', '.join(repr(v) for v in values)})"


class User(db.Model):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(80))
    student_id: Mapped[str] = mapped_column(String(9), unique=True)
    role: Mapped[str] = mapped_column(
        String(10), default="customer", server_default="customer"
    )

    # passive_deletes="all": never touch tickets from Python, so the database's
    # ON DELETE RESTRICT decides (a user who has tickets cannot be deleted).
    tickets: Mapped[list["Ticket"]] = relationship(
        back_populates="user", passive_deletes="all"
    )

    __table_args__ = (
        CheckConstraint("length(trim(name)) > 0", name="ck_users_name_not_blank"),
        CheckConstraint(
            "student_id ~ '^[0-9]{4}-[0-9]{4}$'", name="ck_users_student_id_format"
        ),
        CheckConstraint(_in_list("role", ROLES), name="ck_users_role"),
    )


class Service(db.Model):
    __tablename__ = "services"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(60), unique=True)
    # True for services that ask "still browsing or ready to pay" (Buy merch)
    uses_stage: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default=text("false")
    )
    # False hides the service from the Join form without deleting its history
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default=text("true")
    )

    tickets: Mapped[list["Ticket"]] = relationship(
        back_populates="service", passive_deletes="all"
    )

    __table_args__ = (
        CheckConstraint("length(trim(name)) > 0", name="ck_services_name_not_blank"),
    )


class Ticket(db.Model):
    __tablename__ = "tickets"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))
    service_id: Mapped[int] = mapped_column(
        ForeignKey("services.id", ondelete="RESTRICT")
    )
    # Empty (NULL) when the service does not use it, e.g. Claim pre-order
    stage: Mapped[str | None] = mapped_column(String(10))
    status: Mapped[str] = mapped_column(
        String(20), default="waiting", server_default="waiting"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    # Set when staff call the ticket; starts the 3-minute limit
    called_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Set when staff mark the ticket served; used for waiting-time reports
    served_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    user: Mapped["User"] = relationship(back_populates="tickets")
    service: Mapped["Service"] = relationship(back_populates="tickets")

    __table_args__ = (
        CheckConstraint(_in_list("status", STATUSES), name="ck_tickets_status"),
        # A NULL stage passes this check, so services without a stage are fine
        CheckConstraint(_in_list("stage", STAGES), name="ck_tickets_stage"),
        CheckConstraint(
            "called_at IS NULL OR called_at >= created_at",
            name="ck_tickets_called_after_created",
        ),
        CheckConstraint(
            "served_at IS NULL OR served_at >= created_at",
            name="ck_tickets_served_after_created",
        ),
        # One active ticket per student per service (FR-12)
        Index(
            "one_active_ticket_per_service",
            "user_id",
            "service_id",
            unique=True,
            postgresql_where=text("status IN ('waiting', 'called')"),
        ),
    )

    @property
    def code(self) -> str:
        """Ticket code shown to people, e.g. A-001."""
        return f"A-{self.id:03d}"