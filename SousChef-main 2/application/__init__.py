# following application factory setup shown here:
# https://flask.palletsprojects.com/en/1.1.x/tutorial/factory/

import os
from flask import ( Flask, render_template )

def create_app(test_config=None):
    # application factory function (create and configure the app)
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev',
        DATABASE=os.path.join(app.instance_path, 'souschef.sqlite'),
    )

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # home page
    @app.route('/')
    def home_page():
        return render_template('flaskSousChefHomepage.html')

    # register blueprint for enter_ingredients
    from application import enter_ingredients
    app.register_blueprint(enter_ingredients.bp)

    from application import db
    db.init_app(app)

    from application import auth
    app.register_blueprint(auth.bp)

    return app

    # TO RUN APP FIRST START PYTHON ENV
    # source <env_name>/bin/activate>
    # THEN RUN
    # % export FLASK_APP=application
    # % export FLASK_ENV=development
    # % flask init-db
    # % flask run
  

    # IF ON WINDOWS CMD START PYTHON ENV WITH REQUIRED METHOD
    # THEN INSTEAD RUN THESE
    # set FLASK_APP=application
    # set FLASK_ENV=development
    # flask run