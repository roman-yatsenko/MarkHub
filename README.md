# MarkHub

Markdown content development service for your GitHub repositories

## Install & Run

1. Install [Python 3.8+](https://www.python.org/downloads/)
2. Install [Poetry](https://python-poetry.org/docs/#installation)
3. Clone the project
4. Run in the project folder:

    ```shell
    poetry shell
    poetry install
    python manage.py makemigrations
    python manage.py migrate
    python manage.py collectstatic
    python manage.py runserver
    ```

5. Open in browser http://127.0.0.1:8000/
6. Sign Up with your GitHub account
