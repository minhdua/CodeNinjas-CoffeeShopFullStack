import os
from flask import Flask, request, jsonify, abort
from sqlalchemy import exc
import json
from flask_cors import CORS

from src.error_handlers import bad_request, forbidden, internal_server_error, not_found, unauthorized, unprocessable_entity

from .database.models import db_drop_and_create_all, setup_db, Drink
from .auth.auth import AuthError, requires_auth

app = Flask(__name__)
setup_db(app)
CORS(app)

'''
@TODO uncomment the following line to initialize the datbase
!! NOTE THIS WILL DROP ALL RECORDS AND START YOUR DB FROM SCRATCH
!! NOTE THIS MUST BE UNCOMMENTED ON FIRST RUN
!! Running this funciton will add one
'''
# db_drop_and_create_all()


@app.after_request
def after_request(response):
    """
    Set Access-Control-Allow
    """
    response.headers.add('Access-Control-Allow-Headers',
                         'Content-Type,Authorization,true')
    response.headers.add('Access-Control-Allow-Methods',
                         'GET, POST, PUT, PATCH, DELETE, OPTIONS')
    return response

# ROUTES


@app.route('/drinks', methods=['GET'])
def get_drinks():
    try:
        drink_objects = Drink.query.all()
        drinks = [drink.short() for drink in drink_objects]

        if len(drinks) == 0:
            abort(404)

        return jsonify({
            "success": True,
            "drinks": drinks
        }), 200

    except Exception as e:
        print(e)
        abort(400)


@app.route('/drinks-detail')
@requires_auth('get:drinks-detail')
def get_drinks_detail(payload):
    try:
        drink_objects = Drink.query.all()
        drinks = [drink.long() for drink in drink_objects]

        if len(drinks) == 0:
            abort(404)

        return jsonify({
            "success": True,
            "drinks": drinks
        }), 200

    except Exception:
        abort(400)


@app.route('/drinks', methods=['POST'])
@requires_auth('post:drinks')
def post_drinks(payload):
    body = request.get_json()
    new_title = body.get('title', None)
    new_recipe = body.get('recipe', None)

    if new_title is None or new_recipe is None:
        abort(422)

    try:
        if isinstance(new_recipe, dict):
            new_recipe = [new_recipe]
        new_recipe = json.dumps(new_recipe)
        drink = Drink(title=new_title, recipe=new_recipe)
        drink.insert()

        return jsonify({
            'success': True,
            'drinks': drink.long()
        })

    except Exception:
        abort(400)


@app.route('/drinks/<int:drink_id>', methods=['PATCH'])
@requires_auth('patch:drinks')
def patch_drinks(payload, drink_id):
    body = request.get_json()
    title = body.get('title', None)
    recipe = body.get('recipe', None)

    if title is None and recipe is None:
        abort(422)

    try:
        drink = Drink.query.filter(Drink.id == drink_id).one_or_none()
        if drink is None:
            abort(404)

        if title is not None:
            drink.title = title

        if recipe is not None:
            if isinstance(recipe, dict):
                recipe = [recipe]
            drink.recipe = json.dumps(recipe)

        drink.update()

        return jsonify({
            'success': True,
            'drinks': [drink.long()]
        }), 200

    except Exception:
        abort(400)


@app.route('/drinks/<int:drink_id>', methods=['DELETE'])
@requires_auth('delete:drinks')
def delete_drink(token, drink_id):
    try:
        drink = Drink.query.filter(Drink.id == drink_id).one_or_none()

        if drink is None:
            abort(404)

        drink.delete()

        return jsonify({
            'success': True,
            'delete': drink_id
        }), 200

    except Exception:
        abort(400)


app.register_error_handler(400, bad_request)
app.register_error_handler(401, unauthorized)
app.register_error_handler(403, forbidden)
app.register_error_handler(404, not_found)
app.register_error_handler(422, unprocessable_entity)
app.register_error_handler(500, internal_server_error)
