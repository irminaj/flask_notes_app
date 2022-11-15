Flask_notes_app

WeBuzz - a blogging app.
Installation
Create virtual environment in project's root directory:

python -m venv venv

Activate the virtual environment:

For Linux / Mac:

source venv/bin/activate

    For Windows:

    source venv/Scripts/activate

Install the required packages:

pip install -r requirements.txt

Running
[1] Set the environment variables:

export FLASK_APP=webuzz
export FLASK_DEBUG=1

[2] Run the development server:

flask run

Alternative without setting environment variables:

flask --app webuzz --debug run

Software dependencies

Flask - a web development framework that is known for its lightweight and modular design. It has many out-of-the-box features and is easily adaptable to specific requirements.

Jinja2 - a fast, expressive, extensible templating engine. Special placeholders in the template allow writing code similar to Python syntax. Then the template is passed data to render the final document.

SQLAlchemy - the Python SQL toolkit and Object Relational Mapper that gives application developers the full power and flexibility of SQL.

Flask SQLAlchemy - an extension for Flask that adds support for SQLAlchemy to the app. It simplifies using SQLAlchemy with Flask by setting up common objects and patterns for using those objects, such as a session tied to each web request, models, and engines. This extension does not change how SQLAlchemy works or is used.

WTForms - a flexible forms validation and rendering library for Python web development. It can work with whatever web framework and template engine that is chosen. It supports data validation, CSRF protection, internationalization (I18N), and more.

Flask WTF - simple integration of Flask and WTForms, including CSRF, file upload, and reCAPTCHA.

Bootstrap Flask - a collection of Jinja macros for Bootstrap and Flask. It helps to render Flask-related data and objects to Bootstrap markup HTML more easily.

For the full list of software dependencies see requirements.txt.