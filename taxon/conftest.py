import pytest
import os

from taxon import create_app
import taxon.models as m

@pytest.fixture
def app():
    overrides = dict(SQLALCHEMY_DATABASE_URI="sqlite://")
    app = create_app(test=True, **overrides)
    return app

@pytest.yield_fixture
def db(app):
    db = app.extensions['sqlalchemy'].db
    db.session.commit()
    db.drop_all()
    db.create_all()

    u = m.User(email='gettaxon@gmail.com', username='gettaxon')
    u.password = 'testing'
    db.session.add(u)
    db.session.commit()
    yield db
    db.session.rollback()
    db.drop_all()
