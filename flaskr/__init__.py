import os

from flask import Flask, g, request, session, send_from_directory
from flask_babel import Babel
from . import db

def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)

    app.config.from_mapping(
        SECRET_KEY=os.environ["SECRET_FLASK_KEY"],
        DATABASE=os.path.join(app.instance_path, 'flaskr.sqlite'),
        SESSION_COOKIE_DOMAIN="127.0.0.1",
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

    db.init_app(app)

    from . import auth
    app.register_blueprint(auth.bp)

    from . import capt
    app.register_blueprint(capt.bp)
    app.add_url_rule('/', endpoint='index')
    print("[DEBUG __init]", "App Secret_key", app.secret_key)

    babel = Babel(app)
    
    @babel.localeselector
    def get_locale():
        translations = [str(translation) for translation in babel.list_translations()]
        # if a user is logged in, use the locale from the user settings
        user = g.user
        s_locale = session.get("locale")
        if user is not None: 
            if "locale" in user:
                print("User locale :", user["locale"])
                return user["locale"]
            elif "id" in user:
                cursor = db.get_db().cursor()
                cursor.execute('SELECT id, locale'
                             ' FROM account WHERE id=%s', (user["id"],))
                u_db = cursor.fetchone()
                print("Stored locale :", u_db[1])
                return u_db[1]
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

    @app.before_request
    def make_session_permanent():
        print("[DEBUG-__init__]","make session permanent")
        session.permanent = True
        session.modified = True


    @app.context_processor
    def inject_communities():
        tmp = {}
        cursor = db.get_db().cursor()
        cursor.execute('SELECT id, name, lang FROM server')
        servers = cursor.fetchall()
        for server in servers :
            s_id = server[0]
            name = server[1]
            lang = server[2]
            if lang not in tmp :
                tmp[lang] = {}
            if "servers" not in tmp[lang] :
                tmp[lang]["servers"] = []
            tmp[lang]["servers"].append({ "id" : s_id, "name" : name})
        communities = []
        for lang in tmp:
            communities.append( { "flag":lang, "servers":tmp[lang]["servers"] } )
#        print(communities)
        return dict(communities=communities)

    return app

