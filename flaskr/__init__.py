import os

from flask import Flask, g, request, session
from flask_babel import Babel


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)

    app.config.from_mapping(
        SECRET_KEY=os.environ["SECRET_FLASK_KEY"],
        DATABASE=os.path.join(app.instance_path, 'flaskr.sqlite'),
        BABEL_DEFAULT_LOCALE="en"
    )

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile('babel.cfg', silent=True)
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    from . import db
    db.init_app(app)

    from . import auth
    app.register_blueprint(auth.bp)

    from . import capt
    app.register_blueprint(capt.bp)
    app.add_url_rule('/', endpoint='index')

    babel = Babel(app)
    
    @babel.localeselector
    def get_locale():
        translations = [str(translation) for translation in babel.list_translations()]
        # if a user is logged in, use the locale from the user settings
        user = g.user
        print("User", user)
        if user is not None and "locale" in user:
            print("User locale :", user.locale)
            return user.locale
        s_locale = session.get("locale")
        if s_locale is not None:
            print("Session locale:", s_locale)
            return s_locale
        local = request.accept_languages.best_match(translations)
        print("Guessed locale:", local," (from", translations,")")
        return local

    @babel.timezoneselector
    def get_timezone():
        user = getattr(g, 'user', None)
        if user is not None:
            return user.timezone

    @app.route('/favicon.ico')
    def favicon():
        return send_from_directory(os.path.join(app.root_path, 'static'),
                                   'favicon.ico', mimetype='image/vnd.microsoft.icon')


    return app

