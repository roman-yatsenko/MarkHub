# MarkHub

Markdown content development service for your GitHub repositories

## Install & Run

1. Install [Python 3.8+](https://www.python.org/downloads/)
2. Install [Poetry](https://python-poetry.org/docs/#installation)
3. Clone the project.
4. Create `.env` file in the project folder:

    ```text
    DEBUG=True
    SECRET_KEY=<any_symbols>
    ALLOWED_HOSTS=127.0.0.1
    IMGUR_CLIENT_ID=<imgur_client_id>
    IMGUR_API_KEY=<imgur_api_key>
    ```

5. Run in the project folder:

    ```shell
    poetry shell
    poetry install
    python manage.py makemigrations
    python manage.py migrate
    python manage.py collectstatic 
    python manage.py createsuperuser # set superuser's login and password
    python manage.py runserver
    ```

6. Open in the browser http://127.0.0.1:8000/admin and use your newly-created superuser credentials to login.
7. Go to the `Sites` table and set the domain name to `127.0.0.1`. The `Display Name` is for internal admin use so we can leave it as is for now.
8. Next go back to the admin homepage and click on the add button for Social Applications on the bottom. Add a name `GitHub` and then the Client ID and Secret ID from Github (To configure a new OAuth application on Github, go to https://github.com/settings/applications/new.). Final step is to add our site to the Chosen sites on the bottom. Then click save.
9. Open in the browser http://127.0.0.1:8000 and Sign Up with your GitHub account.
