"""Main app file. Link all the module in a single Flask app
Load all the modules and dependencies together in a single Flask web application
Order is important here. Load app and dependencies first, then the modules.
Dash modules are loaded as objects, not self standing application, so it can interact witht the 
rest of the application

dependencies: 

Returns:
    (Flask application): main flask application
"""

from flask import Flask, jsonify, request
from flask_restful import Resource, Api
from config import Config


def create_app(config_class=Config):

    app = Flask(__name__)
    app.config.from_object(config_class)

    # creating an API object
    api = Api(app)

    # Create route class
    class Hello(Resource):
  
        # corresponds to the GET request.
        # this function is called whenever there
        # is a GET request for this resource
        def get(self):
    
            return jsonify({'message': 'hello world'})
    
        # Corresponds to POST request
        def post(self):
            
            data = request.get_json()     # status code
            return jsonify({'data': data}), 201
    
    api.add_resource(Hello, '/')

    return app