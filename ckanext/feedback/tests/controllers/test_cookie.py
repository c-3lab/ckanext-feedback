import pytest
from flask import Flask, make_response
from ckanext.feedback.controllers.cookie import (
    set_like_status_cookie,
    set_repeat_post_limit_cookie,
    get_like_status_cookie,
    get_repeat_post_limit_cookie,
)

@pytest.fixture
def app():
    app = Flask(__name__)
    app.config["TESTING"] = True
    return app


def test_set_like_status_cookie_true(app):
    with app.test_client() as client:
        
        @app.route("/set_true")
        def set_cookie_true():
            resp = make_response("OK")
            return set_like_status_cookie(resp,"123","True")
        res = client.get("/set_true")
        cookie = res.headers.get("Set-Cookie")
        assert "like_status_123=True" in cookie
        assert "Max-Age=2147483647" in cookie

def test_set_like_status_cookie_false(app):
    with app.test_client() as client:


        @app.route("/set_false")
        def set_cookie_false():
            resp = make_response("OK")
            return set_like_status_cookie(resp,"123","False")
        res = client.get("/set_false")
        cookie = res.headers.get("Set-Cookie")
        assert "like_status_123=False" in cookie
        assert "Max-Age=2147483647" in cookie

def test_set_like_status_cookie_invalid_value_raises(app):
    with app.test_request_context():
        resp = make_response("OK")
        with pytest.raises(ValueError):
            set_like_status_cookie(resp, "abc", "maybe")

def test_set_repeat_post_limit_cookie_nomal(app):
     with app.test_client() as client:
        @app.route("/set_cookie")
        def set_cookie_nomal():
            resp = make_response("OK")
            return set_repeat_post_limit_cookie(resp, "123")

        res = client.get("/set_cookie")
        cookie = res.headers.get("Set-Cookie")
        assert "repeat_post_limit_123=alreadyPosted" in cookie
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

def test_set_repeat_post_limit_cookie_numeric_id(app):
    with app.test_client() as client:
        @app.route("/set_cookie_num")
        def set_cookie_numeric():
            resp = make_response("OK")
            return set_repeat_post_limit_cookie(resp, 456)

        res = client.get("/set_cookie_num")
        cookie = res.headers.get("Set-Cookie")
        assert "repeat_post_limit_456=alreadyPosted" in cookie

def test_set_repeat_post_limit_cookie_none_id(app):
    with app.test_client() as client:
        @app.route("/set_cookie_none")
        def set_cookie_none():
            resp = make_response("OK")
            return set_repeat_post_limit_cookie(resp, None)

        res = client.get("/set_cookie_none")
        cookie = res.headers.get("Set-Cookie")
        assert "repeat_post_limit_None=alreadyPosted" in cookie

def test_get_like_status_cookie_true(app):
    with app.test_client() as client:
        @app.route("/get_cookie")
        def get_cookie_true():
            return get_like_status_cookie("123") or "None"

        client.set_cookie("localhost", "like_status_123", "true")
        res = client.get("/get_cookie")
        assert res.data.decode() == "true"

def test_get_like_status_cookie_false(app):
    with app.test_client() as client:
        @app.route("/get_cookie")
        def get_cookie_false():
            return get_like_status_cookie("456") or "None"

        client.set_cookie("localhost", "like_status_456", "false")
        res = client.get("/get_cookie")
        assert res.data.decode() == "false"

def test_get_like_status_cookie_none(app):
    with app.test_client() as client:
        @app.route("/get_cookie")
        def get_cookie_none():
            return get_like_status_cookie("789") or "None"

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

def test_get_repeat_post_limit_cookie_set(app):
    with app.test_client() as client:
        @app.route("/get_repeat_cookie")
        def get_cookie_nomal():
            return get_repeat_post_limit_cookie("123") or "None"

        client.set_cookie("localhost", "repeat_post_limit_123", "alreadyPosted")
        res = client.get("/get_repeat_cookie")
        assert res.data.decode() == "alreadyPosted"

def test_get_repeat_post_limit_cookie_none(app):
    with app.test_client() as client:
        @app.route("/get_repeat_cookie")
        def get_cookie_none():
            return get_repeat_post_limit_cookie("456") or "None"

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

def test_get_repeat_post_limit_cookie_special_id(app):
    with app.test_client() as client:
        @app.route("/get_repeat_cookie")
        def get_cookie_special():
            return get_repeat_post_limit_cookie("@!#") or "None"

        client.set_cookie("localhost", "repeat_post_limit_@!#", "alreadyPosted")
        res = client.get("/get_repeat_cookie")
        assert res.data.decode() == "alreadyPosted"
