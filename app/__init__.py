from apiflask import APIFlask, Schema, abort
from apiflask.fields import Integer, String
from config import Config


def create_app(config_class=Config):
    app = APIFlask(__name__, title='PowerApp', version='0.1')
    app.config['LOCAL_SPEC_PATH'] = 'openapi.json'   # run flask spec to write the OpenAPI specification file

    with app.app_context():
        from app.power_model.routes import power_bp 

        # Register Blueprints
        app.register_blueprint(power_bp, url_prefix='/power')

        @app.get('/')
        def say_hello():
            # returning a dict or list equals to use jsonify()
            return {'message': 'Hello!'}


        return app