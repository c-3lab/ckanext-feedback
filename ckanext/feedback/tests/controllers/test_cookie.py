import uuid

import pytest
from flask import Flask, make_response

from ckanext.feedback.controllers.cookie import (
    get_like_status_cookie,
    get_repeat_post_limit_cookie,
    set_like_status_cookie,
    set_repeat_post_limit_cookie,
)


@pytest.fixture
def app():
    app = Flask(__name__)
    app.config["TESTING"] = True
    return app


@pytest.fixture
def resource_id():
    return str(uuid.uuid4())


def test_set_like_status_cookie_true(app, resource_id):
    with app.test_client() as client:

        @app.route("/set_true")
        def set_cookie_true():
            resp = make_response("OK")
            return set_like_status_cookie(resp, resource_id, "True")

        res = client.get("/set_true")
        cookie = res.headers.get("Set-Cookie")
        assert f"like_status_{resource_id}=True" in cookie
        assert "Max-Age=2147483647" in cookie


def test_set_like_status_cookie_false(app, resource_id):
    with app.test_client() as client:

        @app.route("/set_false")
        def set_cookie_false():
            resp = make_response("OK")
            return set_like_status_cookie(resp, resource_id, "False")

        res = client.get("/set_false")
        cookie = res.headers.get("Set-Cookie")
        assert f"like_status_{resource_id}=False" in cookie
        assert "Max-Age=2147483647" in cookie


def test_set_repeat_post_limit_cookie_nomal(app, resource_id):
    with app.test_client() as client:

        @app.route("/set_cookie")
        def set_cookie_nomal():
            resp = make_response("OK")
            return set_repeat_post_limit_cookie(resp, resource_id)

        res = client.get("/set_cookie")
        cookie = res.headers.get("Set-Cookie")
        assert f"repeat_post_limit_{resource_id}=alreadyPosted" in cookie
        assert "Max-Age=2147483647" in cookie


def test_set_repeat_post_limit_cookie_empty_id(app):
    with app.test_client() as client:

        @app.route("/set_cookie_empty")
        def set_cookie_empty():
            resp = make_response("OK")
            return set_repeat_post_limit_cookie(resp, "")

        res = client.get("/set_cookie_empty")
        cookie = res.headers.get("Set-Cookie")
        assert "repeat_post_limit_=alreadyPosted" in cookie


def test_set_repeat_post_limit_cookie_none_id(app):
    with app.test_client() as client:

        @app.route("/set_cookie_none")
        def set_cookie_none():
            resp = make_response("OK")
            return set_repeat_post_limit_cookie(resp, None)

        res = client.get("/set_cookie_none")
        cookie = res.headers.get("Set-Cookie")
        assert "repeat_post_limit_None=alreadyPosted" in cookie


def test_get_like_status_cookie_true(app, resource_id):
    with app.test_client() as client:

        @app.route("/get_cookie")
        def get_cookie_true():
            return get_like_status_cookie(resource_id) or "None"

        client.set_cookie("localhost", f"like_status_{resource_id}", "true")
        res = client.get("/get_cookie")
        assert res.data.decode() == "true"


def test_get_like_status_cookie_false(app, resource_id):
    with app.test_client() as client:

        @app.route("/get_cookie")
        def get_cookie_false():
            return get_like_status_cookie(resource_id) or "None"

        client.set_cookie("localhost", f"like_status_{resource_id}", "false")
        res = client.get("/get_cookie")
        assert res.data.decode() == "false"


def test_get_like_status_cookie_none(app, resource_id):
    with app.test_client() as client:

        @app.route("/get_cookie")
        def get_cookie_none():
            return get_like_status_cookie(resource_id) or "None"

        res = client.get("/get_cookie")
        assert res.data.decode() == "None"


def test_get_like_status_cookie_empty_id(app):
    with app.test_client() as client:

        @app.route("/get_cookie")
        def get_cookie_empty():
            return get_like_status_cookie("") or "None"

        client.set_cookie("localhost", "like_status_", "true")
        res = client.get("/get_cookie")
        assert res.data.decode() == "true"


def test_get_repeat_post_limit_cookie_set(app, resource_id):
    with app.test_client() as client:

        @app.route("/get_repeat_cookie")
        def get_cookie_nomal():
            return get_repeat_post_limit_cookie(resource_id) or "None"

        client.set_cookie(
            "localhost", f"repeat_post_limit_{resource_id}", "alreadyPosted"
        )
        res = client.get("/get_repeat_cookie")
        assert res.data.decode() == "alreadyPosted"


def test_get_repeat_post_limit_cookie_none(app, resource_id):
    with app.test_client() as client:

        @app.route("/get_repeat_cookie")
        def get_cookie_none():
            return get_repeat_post_limit_cookie(resource_id) or "None"

        res = client.get("/get_repeat_cookie")
        assert res.data.decode() == "None"


def test_get_repeat_post_limit_cookie_empty_id(app):
    with app.test_client() as client:

        @app.route("/get_repeat_cookie")
        def get_cookie_empty():
            return get_repeat_post_limit_cookie("") or "None"

        client.set_cookie("localhost", "repeat_post_limit_", "alreadyPosted")
        res = client.get("/get_repeat_cookie")
        assert res.data.decode() == "alreadyPosted"
