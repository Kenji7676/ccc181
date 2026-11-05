# Lang-Q-t

Lang-Q-t is a virtual queue for the Langkit University Shop. Customers join the line for Buy merch or Claim pre-order and see their ticket, status and place in line on their phone, while the shop staff call, serve or mark customers as no-show from a dashboard. It replaces having to physically stand in line in a crowded shop, and it allows early-arriving customers to keep browsing without fear that the get pushed back to the bottom of the paying queue once they're finished. It was built for CCC181 with Flask, Jinja and Bootstrap 5. After Week 4, PostgreSQL has been integrated into the app to serve as a database.

## What it does

* **Join** (`/join`): a customer enters a name and a Student ID (format `0000-0000`) and chooses a service. For Buy merch, they also choose whether they are still browsing or ready to pay. The server checks every field and keeps what was typed when something is wrong. The page also shows how many people are waiting.
* **My place** (`/queue/<id>`): shows the ticket code, service, status, how many people are ahead in the same queue, and a Leave button with a confirmation step. A browsing customer can press "I'm ready to pay" to move into the paying group. The page checks for updates every 10 seconds and changes without a reload.
* **Staff dashboard** (`/staff`): shows the called and waiting tickets in queue order, grouped into Called, Ready to pay and Waiting. It has a Call next button, a service filter, and Call, Serve and No-show buttons on each row. It refreshes every 5 seconds.

Customers who are ready to pay are always called before customers who are still browsing, whoever joined first. Claim pre-order customers are not asked about browsing and wait in order of arrival.

Tickets use the code `A-<number>`, for example `A-007`. Each number is used once and never reused.

The requirements for this app are in [docs/requirements.md](docs/requirements.md).

## Run it

You need Python 3.11 or newer.

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows (PowerShell: .venv\Scripts\Activate.ps1)
source .venv/bin/activate       # macOS/Linux
pip install -r requirements.txt
flask --app app run --debug
```

Open http://127.0.0.1:5000. To try it on a phone, run `flask --app app run --debug --host 0.0.0.0` and visit your laptop's IP address on the same Wi-Fi.

## Things to know

* **The queue is cleared on every restart.** Tickets live in a Python list, so stopping the server or saving a file while `--debug` is on empties the queue. A database in Week 4 fixes this.
* **The staff pages have no login yet.** Anyone who opens `/staff` can call, serve and mark tickets. Staff login is planned for a later week.
* **The secret key is a development value.** It will move into an environment variable before the app is deployed.
* **Live updates use polling.** My place asks the server for its status every 10 seconds, and the dashboard reloads its own content every 5 seconds. Neither page needs a manual refresh.

## Project structure

```
app.py                  # routes, queue rules and validation
requirements.txt        # packages to rebuild the environment
.gitignore              # keeps .venv/ and __pycache__/ out of Git
templates/
    base.html           # shared layout, navigation and flash messages
    index.html          # home page
    join.html           # join form
    ticket.html         # My place
    staff.html          # staff dashboard
static/
    css/style.css       # Lang-Q-t design (Langkit maroon and gold)
    js/main.js          # double-submit guard on the join form
docs/
    week1/              # proposal and requirements
    week3/              # personas, wireframes, self-review, accessibility, usability test, report
```

## Routes

| URL | Method | What it does |
| --- | --- | --- |
| `/` | GET | Home page |
| `/join` | GET, POST | Show the join form, create a ticket |
| `/queue/<id>` | GET | My place for one ticket (404 if it does not exist) |
| `/queue/<id>/status.json` | GET | Status, stage and people ahead, polled by My place |
| `/queue/<id>/ready` | POST | Move a browsing customer into the paying group |
| `/queue/<id>/leave` | POST | Leave the queue |
| `/staff` | GET | Staff dashboard, optional `?service_id=` filter |
| `/staff/call-next` | POST | Call the next waiting customer, ready-to-pay first |
| `/staff/tickets/<id>/<action>` | POST | Call, serve or no-show one ticket |

## Documents

* Week 3: the personas, wireframes, self-review, accessibility results, usability test and report are in `docs/week3/`. The report is `docs/week3/report.md`.