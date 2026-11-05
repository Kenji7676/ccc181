## Browser

The attributes on the Join form match the columns they fill:

- **Name:** `required` and `maxlength="80"`, matching `users.name`, which is `String(80)` and NOT NULL.
- **Student ID:** `required`, `maxlength="9"` and `pattern="[0-9]{4}-[0-9]{4}"`, matching `users.student_id`, which is `String(9)`, NOT NULL and checked against the `0000-0000` format.
- **Service:** `required` on the service choices, matching `tickets.service_id`, which is NOT NULL and refers to an existing service.
- **Browsing or ready to pay:** `required` only while it is visible, because `tickets.stage` can be empty for services that do not ask it, such as Claim pre-order. The script disables these inputs when they are hidden, so they are never sent.

These attributes give honest users quick feedback, but anyone can skip them. The form uses `novalidate`, so the server's own messages are the ones people see, and the real checks happen in Flask and in the database.

## Flask (curl, skipping the form)

Before the tests, `SELECT count(*) FROM tickets;` gave 7. After all four requests, the query still showed 7, so nothing bad was saved.

| Rule | Layer | How I tested it | What happened |
| --- | --- | --- | --- |
| Name, Student ID and service are required | Flask | `curl.exe -i -X POST http://127.0.0.1:5000/join -d "name=" -d "student_id=" -d "service_id=999"` | `HTTP/1.1 400 BAD REQUEST`, form shows "Enter your full name (up to 80 characters).", "Enter your student ID like 2024-0001." and "Choose a service." |
| Student ID must be 0000-0000 | Flask | `curl.exe -i -X POST http://127.0.0.1:5000/join -d "name=Test" -d "student_id=12345" -d "service_id=1" -d "stage=browsing"` | 400, "Enter your student ID like 2024-0001." |
| Name is at most 80 characters | Flask | `$long = "x" * 200` then `curl.exe -i -X POST http://127.0.0.1:5000/join -d "name=$long" -d "student_id=2024-0001" -d "service_id=1" -d "stage=browsing"` | 400, "Enter your full name (up to 80 characters)." |
| A switched-off service cannot be joined | Flask | Claim pre-order switched off in Manage services, then `curl.exe -i -X POST http://127.0.0.1:5000/join -d "name=Test" -d "student_id=2024-0001" -d "service_id=2"` | 400, "Choose a service." and Claim pre-order is missing from the Join form |

## Database (psql, skipping Flask)

| Rule | Constraint type | How I tested it | What happened |
| --- | --- | --- | --- |
| A ticket needs a service that exists | FOREIGN KEY | `INSERT INTO tickets (user_id, service_id) VALUES ((SELECT min(id) FROM users), 999);` | `ERROR: insert or update on table "tickets" violates foreign key constraint "tickets_service_id_fkey"` and `DETAIL: Key (service_id)=(999) is not present in table "services".` |
| Only the five statuses are allowed | CHECK | `UPDATE tickets SET status = 'lost' WHERE id = (SELECT min(id) FROM tickets);` | `ERROR: new row for relation "tickets" violates check constraint "ck_tickets_status"`and `DETAIL:  Failing row contains (1, 1, 1, browsing, lost, 2026-11-05 04:44:19.36162+00, 2026-11-05 05:24:43.654186+00, null).` |
| Stage must be browsing or paying | CHECK | `UPDATE tickets SET stage = 'vip' WHERE id = (SELECT min(id) FROM tickets);` | `ERROR: new row for relation "tickets" violates check constraint "ck_tickets_stage"` and `DETAIL:  Failing row contains (1, 1, 1, vip, served, 2026-11-05 04:44:19.36162+00, 2026-11-05 05:24:43.654186+00, null).` |
| Student ID must be 0000-0000 | CHECK | `INSERT INTO users (name, student_id) VALUES ('Bad', '12345');` | `ERROR: new row for relation "users" violates check constraint "ck_users_student_id_format"` and `DETAIL:  Failing row contains (6, Bad, 12345, customer).` |
| A name cannot be blank | CHECK | `INSERT INTO users (name, student_id) VALUES ('   ', '2030-0002');` | `ERROR: new row for relation "users" violates check constraint "ck_users_name_not_blank"` and `DETAIL:  Failing row contains (7,    , 2030-0002, customer).` |
| A ticket cannot be called before it was created | CHECK | `UPDATE tickets SET called_at = created_at - interval '1 day' WHERE id = (SELECT min(id) FROM tickets);` | `ERROR: new row for relation "tickets" violates check constraint "ck_tickets_called_after_created"` and `DETAIL:  Failing row contains (1, 1, 1, browsing, served, 2026-11-05 04:44:19.36162+00, 2026-11-04 04:44:19.36162+00, null).` |
| A user needs a name | NOT NULL | `INSERT INTO users (name, student_id) VALUES (NULL, '2030-0001');` | `ERROR: null value in column "name" of relation "users" violates not-null constraint` and `DETAIL:  Failing row contains (8, null, 2030-0001, customer).` |
| One row per Student ID | UNIQUE | `INSERT INTO users (name, student_id) SELECT 'Copy', student_id FROM users LIMIT 1;` | `ERROR: duplicate key value violates unique constraint "users_student_id_key"` and `DETAIL: Key (student_id)=(2024-0001) already exists.` and `DETAIL:  Key (student_id)=(2024-0006) already exists.` |
| Two services cannot share a name | UNIQUE | `INSERT INTO services (name) SELECT name FROM services LIMIT 1;` | `ERROR: duplicate key value violates unique constraint "services_name_key"` and `DETAIL: Key (name)=(Buy merch) already exists.` and `DETAIL:  Key (name)=(Buy merch) already exists.` |
| One active ticket per student per service | UNIQUE (partial index) | `INSERT INTO tickets (user_id, service_id) SELECT user_id, service_id FROM tickets WHERE status IN ('waiting', 'called') LIMIT 1;` | `ERROR: duplicate key value violates unique constraint "one_active_ticket_per_service"` and `DETAIL: Key (user_id, service_id)=(1, 1) already exists.` |
| A service with tickets cannot be deleted | ON DELETE RESTRICT | `DELETE FROM services WHERE id = (SELECT service_id FROM tickets LIMIT 1);` | `ERROR: update or delete on table "services" violates foreign key constraint "tickets_service_id_fkey" on table "tickets"` and `DETAIL: Key (id)=(1) is still referenced from table "tickets".` |

A good row, to show the defaults the database fills in:

| | | | |
| --- | --- | --- | --- |
| A valid ticket is accepted, and the database fills in its defaults | DEFAULT (and all constraints pass) | `INSERT INTO tickets (user_id, service_id) VALUES (1, 1) RETURNING id, status, created_at;` | Succeeded and returned the new `id`, `status = waiting` and a `created_at` time, all set by the database. I deleted the row afterward. |

## No SQL in f-strings

The app never builds SQL by gluing user input into a string. Every query is written with SQLAlchemy (`db.select(...)`, `db.session.get(...)` and the model classes), which sends values to PostgreSQL separately from the SQL text. Input such as `' OR '1'='1` is therefore treated as an ordinary string, never as code, so SQL injection is not possible through the Join form or the staff routes.

I checked this by searching all Python files for SQL keywords inside f-strings:

`git grep -nE 'f["'"'"'].*(SELECT|INSERT|UPDATE|DELETE)' -- '*.py'`

The command printed nothing. The only f-strings in the app build flash messages and ticket codes, and `models.py` uses one to build a fixed CHECK constraint from the lists of allowed values, which contains no user input.

