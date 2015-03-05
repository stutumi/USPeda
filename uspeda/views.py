from uspeda import app, db, bcrypt, mail
from uspeda.models import Crime, Residence, User, Review
import uspeda.validate as validate
from flask import render_template, jsonify, redirect, request, \
                  url_for, abort, flash, session
from flask_mail import Message
from itsdangerous import URLSafeTimedSerializer
from datetime import date
import json
import re

@app.route('/')
@app.route('/index')
def index():
    authenticated = False
    email = ''
    reviews = []
    if 'email' in session:
        email = session['email']
        # user reviews
        user_q = User.query.filter_by(email=email).first()
        reviews = user_q.reviews
        authenticated = True
    return render_template('index.html', authenticated=authenticated,
                           title='USPeda ' + email, email=email, reviews=reviews)

@app.route('/update')
def update_map():
    crime_q = Crime.query.all()
    crime = []
    # cache for crime? 
    for c in crime_q: 
        crime.append({'lat': c.lat, 'lng': c.lng, 'weight': c.weight})

    avg_score = request.args.get('avg_score', type=int)
    if not avg_score: 
        residence_q = Residence.query.all()
    else:
        residence_q = Residence.query.filter(Residence.avg_score == avg_score).all()
    residence = []
    for r in residence_q:
        residence.append({'lat': r.lat, 'lng': r.lng,
                         'name': r.name, 'owner': r.owner, 
                         'avg_score': r.avg_score})

    return jsonify(residence=residence, crime=crime)


@app.route('/review', methods=['GET'])
def get_review():
    if not 'email' in session:
        abort(401)
    email = session['email']
    review_id = request.args.get('rev_id', '', type=int)
    review_q = Review.query.filter_by(id=review_id).first()
    if review_q:
        return render_template('review.html', review=review_q, email=email)
    return render_template('review.html', review=[])


@app.route('/residence', methods=['GET'])
def get_residence():
    if 'email' in session:
        lat = request.args.get('lat', '', type=float)
        lng = request.args.get('lng', '', type=float)
        residence_q = Residence.query.filter_by(lat=lat, lng=lng).first()
        if residence_q:
            reviews = residence_q.reviews
            if reviews:
                return render_template('residence.html', reviews=reviews)
        return render_template('residence.html', reviews=[])
    else:
        return '''<h4>Não autorizado!</h4>
                  <h5>Entre com o seu email @usp.br para ter acesso.</h5>'''


@app.route('/options', methods=['GET'])
def get_options():
    ''' 
    Render content for right click on map  
    '''
    if 'email' in session:
        return render_template('/options.html')
    return abort(401)


@app.route('/register', methods=['POST'])
def register():
    '''
    Register a new user 
    '''
    email = request.form.get('email', '').strip()
    password = request.form.get('password', '').strip()
    password2 = request.form.get('password2', '').strip()

    data = request.form

    error = validate.user_register(data)
    if not error:
        # send confirmation email
        mail_confirmation(data['email'])
        user = User(data['email'], data['password'])
        db.session.add(user)
        db.session.commit()
        flash('E-mail de confirmação enviado, verifique!')
    else:
        flash(error)
    return redirect(url_for('index'))


def mail_confirmation(email):
    '''
    Send confirmation email 
    '''

    serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
    code = serializer.dumps(email, salt=app.config['SECURITY_PASSWORD_SALT'])
    msg = Message("USPeda.me - Confirmação de registro",
                  sender="do-not-reply@uspeda.me",
                  recipients=[email])
    msg.html = "Clique no link abaixo para confirmar o seu registro:" \
               "<p><a href=http://177.81.72.220:5000/confirmar?cod" \
               "={0}>http://177.81.72.220:5000/confirmar?cod={0}</a></p>" \
               .format(code)
    mail.send(msg)


@app.route('/confirmar', methods=['GET'])
def confirm_reg():
    '''
    Confirm registration using user's received code  
    '''
    code = request.args.get('cod', '').strip()
    if code:
        serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
        try:
            email = serializer.loads(code,
                                     salt=app.config['SECURITY_PASSWORD_SALT'],
                                     max_age=3600)
        except:
            flash('ERRO: Código expirado!')
            return redirect(url_for('index'))
        user_q = User.query.filter_by(email=email).first()
        user_q.confirmed = True
        session['email'] = email
        session['user_id'] = user_q.id
        user_q.update_last_seen()
    return redirect(url_for('index'))


def validate_creds(email, password, password2):
    '''
    Check if user info is good enough 
    '''
    # Matches @*usp.br domain
    if re.match("^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+"
                "@(?:[a-zA-Z0-9\-]+\.)?usp\.br$", email, re.IGNORECASE):
        # Is it already registered?
        user_q = User.query.filter_by(email=email).first()
        if user_q:
            flash('ERRO: Usuário já registrado!')
            return False
        if len(password) > 10:
            if password == password2:
                return True
            else:
                flash('ERRO: Senhas não conferem!')
        else:
            flash('ERRO: Senha deve ter pelo menos 10 dígitos!')
    else:
        flash('ERRO: Utilize o e-mail acadêmico da USP!')
    return False


@app.route('/login', methods=['POST'])
def login():
    '''
    Log user in and start session
    '''
    data = request.form.to_dict()

    error = validate.user_login(data)
    print(data['email'])
    if not error:
        # maybe this query could go somewhere else?
        user_q = User.query.filter_by(email=data['email']).first()
        if user_q.is_confirmed:
            if user_q.check_password(data['password']):
                # set session
                session['email'] = data['email']
                session['user_id'] = user_q.id
                user_q.update_last_seen()
            else:
                flash('Usuário e/ou senha incorretos.')
        else:
            flash('Verifique e-mail de confirmação.')
    else:
        print(error)
        flash(error)
    return redirect(url_for('index'))


@app.route('/logout')
def logout():
    '''
    Log user out
    '''
    session.pop('email', None)
    return redirect(url_for('index'))


@app.route('/update_review', methods=['POST'])
def update_review():
    '''
    Update a review with a new text 
    '''
    if 'email' not in session:
        abort(401)
    try:
        data = request.get_json()
    except BadRequest:
        return abort(400)

    error = validate.review(data)
    if not error:
        review_id = data['review_id']
        review_text = data['review_text']
        print(type(review_id))
        score = data['score']

        review_q = Review.query.filter_by(id=review_id).first()
        if review_q:
            if review_q.user.email != session['email']:
                error = 'User do not have permission to edit review with ID: {0}'.format(review_id)
                flash(error)
                abort(401)
            review_q.review_text = review_text
            review_q.score = score
            db.session.commit()
            return jsonify({'review_id': review_q.id})
    error = 'Incorrect review ID: {0}'.format(res_id)
    flash(error)
    return abort(401)


@app.route('/add_review', methods=['POST'])
def add_review():
    '''
    Add a new review text and score for a residence
    If the residence is new create a new one, otherwise
    just add to existing one 
    '''
    if not 'email' in session:
        return abort(401)

    user = session['email'].split('@')[0]

    try:
        data = request.get_json()
    except BadRequest:
        return abort(400)

    error = validate.review(data)
    if not error:
        res_id = data.get('res_id', '').strip()
        if res_id:
            # adding review to existing residence? 
            residence = Residence.query.filter_by(id=res_id).first()
            if residence:
                new_res = False
            else: 
                error = 'Incorrect residence ID: {0}'.format(res_id)
                flash(error)
                abort(400)
        else:
            new_res = True
            residence = Residence(data['lat'], data['lng'], data['res_name'], 
                                  data['owner'], data['address'], data['zipcode'])
            db.session.add(residence)
            db.session.commit()

        review = Review(data['review_text'], data['score'])
        review.residence_id = residence.id
        review.user_id = session['user_id']
        db.session.add(review)
        db.session.commit()

        sum_scores = sum([r.score for r in residence.reviews])
        residence.update_avg(sum_scores)

        review = {'new_res': new_res, 'res_name': residence.name, 'owner': residence.owner, \
                  'author': user, 'rev_id': review.id, 'date': str(review.date_added), \
                  'score': review.score, 'lat': residence.lat, 'lng': residence.lng}

        return jsonify(review=review)
    flash(error)
    return jsonify(error=error)


@app.route('/add_crime', methods=['POST'])
def add_crime():
    ''' 
    Add a crime occurence to the map 
    '''
    if not 'email' in session:
        return abort(401)
    try:
        data = request.get_json()
    except BadRequest:
        return abort(400)

    error = validate.crime(data)
    if not error:
        point = Crime(data['lat'], data['lng'], data['weight'])
        db.session.add(point)
        db.session.commit()
        crime = {'lat': data['lat'], 'lng': data['lng'], 'weight': data['weight']}
        return jsonify(crime=crime)
    flash(error)
    return jsonify(error=error)
