# Contributing

Thank you for considering contributing!<br>
We appreciate your help in making this [project](https://constructor.exg1o.org/) better.

## Requirements

- Linux
- [uv](https://docs.astral.sh/uv/) 0.10
- [PostgreSQL](https://www.postgresql.org/) 18
- [Redis](https://redis.io/) 8

## Installation

### 1. Clone the repository

```bash
git clone --recurse-submodules https://github.com/EXG1O/Constructor-Telegram-Bots-Backend.git
cd Constructor-Telegram-Bots-Backend
```

### 2. Build the frontend

Build the frontend separately by following the instructions in the [Constructor Telegram Bots Frontend](https://github.com/EXG1O/Constructor-Telegram-Bots-Frontend) repository.

### 3. Configure environment variables

Copy the `.env.example` file to `.env` and configure it with your settings:

```bash
cp .env.example .env
```

### 4. Set up environment and dependencies

```bash
uv sync --locked
source .venv/bin/activate
python manage.py migrate
python manage.py compilemessages -i .venv
python manage.py collectstatic
```

### 5. Start the application

Open separate terminals for each of the following commands:

```bash
gunicorn -c constructor_telegram_bots/gunicorn.py constructor_telegram_bots.wsgi:application
```

```bash
celery -A constructor_telegram_bots worker -l INFO -f logs/celery_worker.log
```

```bash
celery -A constructor_telegram_bots beat -l INFO -f logs/celery_beat.log
```

## Usage

Once the installation is complete, open your browser and navigate to `http://localhost:8000` to start developing.

## Code Formatting and Linting

We use **ruff** for code formatting and linting, and **mypy** for type checking.

### ruff

To format your code:

```bash
ruff format
```

To check your code for linting issues:

```bash
ruff check
```

To auto-fix issues:

```bash
ruff check --fix
```

### mypy

To run type checking:

```bash
mypy .
```

### Run all checks

To run all code quality checks (formatting, linting, and type checking) at once, use:

```bash
ruff format && ruff check --fix && mypy .
```

## Testing

We prioritize code quality and early bug detection through tests. Run the tests with:

```bash
python manage.py test
```

Please add tests for any new functionality to ensure complete coverage.

## Translations

To improve existing translations or add a new language:

```bash
python manage.py makemessages -i .venv -l <lang> --no-location
```

Replace `<lang>` with the language code (e.g., `en`, `ru`, `de`, `fr`, etc.).

All locale files are located in the `locale` directory. After making your changes, compile the messages:
```bash
python manage.py compilemessages -i .venv
```

## Logs

All log files can be found in the `logs` directory.

## Pull Requests

When submitting a PR, ensure that:

1. Your code follows the project's coding standards.
2. All tests pass successfully.
3. Your changes are well-documented with clear commit messages.
4. Each PR should address a single issue or feature.
