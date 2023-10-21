from flask import Blueprint

test_bp = Blueprint('test', __name__)

@test_bp.route("/api/test")
def test():
    return "test"
