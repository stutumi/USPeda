from uspeda import db, bcrypt
from sqlalchemy.engine import Engine
from sqlalchemy import event, desc
from datetime import date

@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

class Place(db.Model):
    '''
    A single place data point
    '''
    __abstract__ = True  # skip production of a table
    id = db.Column(db.Integer, primary_key=True)
    lat = db.Column(db.Float)
    lng = db.Column(db.Float)
    date_added = db.Column(db.Date)

    def __init__(self, lat, lng):
        self.lat = lat
        self.lng = lng
        self.date_added = date.today()


class Crime(Place):
    '''
    A single crime occurence
    '''
    __tablename__ = 'crime'
    weight = db.Column(db.Integer)

    def __init__(self, lat, lng, weight):
        Place.__init__(self, lat, lng)
        self.weight = weight


class Residence(Place):
    '''
    A single residence place
    '''
    __tablename__ = 'residence'
    name = db.Column(db.String(50))
    owner = db.Column(db.String(50))
    address = db.Column(db.String(100))
    zipcode = db.Column(db.String(10))
    avg_score = db.Column(db.Integer)
    date_added = db.Column(db.Date)

    # a residence may have various reviews
    reviews = db.relationship('Review', order_by=desc('Review.id'), backref='residence')
    revcounter = db.Column(db.Integer)

    def __init__(self, lat, lng, name, owner, address, zipcode):
        Place.__init__(self, lat, lng)
        self.name = name
        self.owner = owner
        self.address = address
        self.zipcode = zipcode
        self.revcounter = 0
        self.avg_score = 0

    def update_avg(self, sum_scores):
        '''
        This is called after this residence receives a new review 
        so that the average score is updated
        '''
        self.revcounter += 1
        self.avg_score = int(round(sum_scores/self.revcounter))
        db.session.commit()


class Review(db.Model):
    '''
    A single review of a residence
    '''
    __tablename__ = 'review'
    id = db.Column(db.Integer, primary_key=True)
    date_added = db.Column(db.Date)
    # there is a residence property here, see Residence class
    residence_id = db.Column(db.Integer, db.ForeignKey('residence.id'), nullable=False)
    # there is a user property here, see User class
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    review_text = db.Column(db.String(1000))
    score = db.Column(db.Integer)

    def __init__(self, review_text, score):
        self.date_added = date.today()
        self.review_text = review_text
        self.score = score


class User(db.Model):
    '''
    A single user login information
    '''
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(60))
    password = db.Column(db.String(60))
    register_date = db.Column(db.Date)
    confirmed = db.Column(db.Boolean)
    last_seen = db.Column(db.Date)  # update this field on every login
    # a user may write several reviews 
    reviews = db.relationship('Review', order_by=desc('Review.id'), backref='user')

    def __init__(self, email, password):
        self.email = email
        self.password = bcrypt.generate_password_hash(password)
        self.register_date = date.today()
        self.confirmed = False

    def update_last_seen(self):
        '''
        This is called when the user logs in in order to update 
        last_seen date 
        '''
        self.last_seen = date.today()
        db.session.commit()

    def check_password(self, password):
        '''
        Check if the password given matches the one stored
        ''' 
        if bcrypt.check_password_hash(self.password, password):
            return True
        return False

    @property
    def is_confirmed(self):
        '''
        Getter for the confirmed attribute 
        '''
        return self.confirmed

    @is_confirmed.setter
    def is_confirmed(self, value):
        '''
        Setter for the confirmed attribute 
        '''
        self.confirmed = value
        all_users.add(self.email) # update set of all_users for faster access 
        db.session.commit()

all_users = set()
def cache_all_users():
    try:
        users = User.query.all()
        for user in users:
            all_users.add(user.email)
    except:
        print('First time...')