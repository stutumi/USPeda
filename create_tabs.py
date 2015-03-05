from uspeda import db
from uspeda.models import User

db.create_all()
me = User('wellington.castello@usp.br', '123412341234')
me.is_confirmed = True
db.session.add(me)
db.session.commit()
