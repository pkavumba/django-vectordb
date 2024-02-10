# Using `django-vectordb` with Django 5

This guide provides step-by-step instructions on how to use `django-vectordb` in a Django 5 project.

> **Important:** The `sentence_transformers` library, which is used as the default for generating sentence embeddings, currently does not support Python 3.12. If you plan to use `sentence_transformers`, please ensure that you are using a Python version lower than 3.12. You don't have to worry about this if you are using OpenAI embeddings or a custom embedding function.

## Prerequisites

Ensure that you have Python and pip installed on your machine.

## Installation

1. **Install the required packages.**

    Use pip to install the necessary packages from the `requirements.txt` file:

    ```bash
    pip install -r requirements.txt
    ```

2. **Create a superuser for the blog.**

    Run the following command and follow the prompts to create a superuser:

    ```bash
    python manage.py createsuperuser
    ```

    You will be asked to provide a username and password. Remember these details as you will need them to log in to the blog.

## Running the Application

1. **Start the server.**

    Use the following command to start the Django server:

    ```bash
    python manage.py runserver
    ```

    By default, the server will start on port `8000`.

2. **Access the blog.**

    Open a web browser and navigate to `http://127.0.0.1:8000/`. You will be prompted to log in. Use the superuser credentials you created earlier to log in and start using the blog.
