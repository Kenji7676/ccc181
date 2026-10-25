# ClinicQ: Hello, Flask

Starter Flask app for **CCC181 Week 2: Git, GitHub & Flask Foundations**.
It shows the project structure, routes, templates and static files from the slides.

## Project structure

```
my-app/
├── app.py              # creates the app and defines routes
├── requirements.txt    # packages to rebuild the environment
├── .gitignore          # keeps .venv, caches and secrets out of Git
├── .venv/              # your virtual environment (not committed)
├── templates/          # Jinja2 HTML files for render_template()
│   ├── base.html       # shared layout
│   ├── index.html      # home page
│   └── ticket.html     # page for /queue/<ticket_id>
└── static/             # served at /static/...
    ├── css/style.css
    └── js/main.js
```

## Routes

| URL | View function | What you see |
|---|---|---|
| `/` | `index()` | "Hello, Ana!" and a list of tickets, rendered with `index.html` |
| `/queue/<int:ticket_id>` | `ticket()` | A page for that ticket, e.g. `/queue/12` |
| `/hello` | `hello()` | The plain text "Hello, CCC181!" |

Try `/queue/abc`: the `int` converter only accepts numbers, so Flask returns 404.

## 1. Set up the Python environment

```bash
# create (once per project)
python -m venv .venv

# activate (every new terminal)
.venv\Scripts\activate          # Windows
source .venv/bin/activate       # macOS/Linux

# install the packages
pip install -r requirements.txt
```

Your prompt shows `(.venv)` when the environment is active. Some systems use `python3` or `py` instead of `python`.
If PowerShell blocks the activate script, run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` once, or use Command Prompt.

If you add more packages later, record them with:

```bash
pip freeze > requirements.txt
```

## 2. Run the app

```bash
flask --app app run --debug
```

Open http://127.0.0.1:5000. With `--debug`, the server reloads every time you save a file. Never use debug mode in production.

## 3. Put it on GitHub

### Once per computer

```bash
git config --global user.name "Your Name"
git config --global user.email you@g.msuiit.edu.ph   # same email as your GitHub account
git config --list
```

### Create the local repository and first commit

```bash
git init
git branch -M main
git status              # .venv should NOT appear, thanks to .gitignore
git add .
git commit -m "Add Flask starter app"
```

### Connect to GitHub and push

1. On GitHub, create a new **empty** repository (no README, no .gitignore).
2. Copy its URL, then:

```bash
git remote add origin <repo-url>
git push -u origin main
```

GitHub does not accept your account password for Git over HTTPS. Sign in through Git Credential Manager or the GitHub CLI, or use a personal access token or SSH key.

### Everyday loop

```bash
git pull origin main     # before you start working
git status
git add <file>
git commit -m "Add join-queue form"
git push origin main     # when you have commits to share
```

## 4. Lab: ship it through a pull request

1. On GitHub, open an issue: **"Set up Flask starter app"**.
2. Pull the latest `main`, then create a branch:
   ```bash
   git switch main
   git pull origin main
   git switch -c feature/flask-setup
   ```
3. Create `.venv`, install Flask, write `requirements.txt` and `.gitignore`.
4. Build `app.py` with a home route and one dynamic route, rendered with `base.html` and `index.html`.
5. Commit in small steps, then push the branch:
   ```bash
   git push -u origin feature/flask-setup
   ```
6. On GitHub, click **Compare & pull request** and write `Closes #N` in the description (N is your issue number). Merge it, then:
   ```bash
   git switch main
   git pull origin main
   ```

**Early finishers:** add another static CSS rule linked with `url_for`, or a third route based on one Must feature from your project milestone.

## Commit message tips

- Short summary in the imperative: "Add...", "Fix..."
- One logical change per commit
- Commit early and often
- Good: "Add join-queue form". Unhelpful: "update", "asdf", "final na talaga".
