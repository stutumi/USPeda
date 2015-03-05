from uspeda.models import all_users
import re

REGISTER_KEYS = ['email', 'password', 'password2']
LOGIN_KEYS = ['email', 'password']
REVIEW_KEYS = ['review_text', 'score', 'lat', 'lng', 
               'res_name', 'owner', 'address', 'zipcode']
CRIME_kEYS = ['lat', 'lng', 'weight']
MIN_PWD_SIZE = 10
MIN_EMAIL_SIZE = 8 # a@usp.br

def _common_register_login(data, keys):
    for key in keys:
        if key not in data.keys():
            return 'Incomplete data: {0}.'.format(key)

    for key, val in data.items():
        if not val.strip():
            return '{0} is empty.'.format(key)

    # the email is an email from USP
    if not re.match("^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+"
                    "@(?:[a-zA-Z0-9\-]+\.)?usp\.br$", data['email'], re.IGNORECASE) and \
                    len(data['email']) < MIN_EMAIL_SIZE:
       return  'Email inválido. Utilize e-mail acadêmico da USP.'

    if len(data['password']) < MIN_PWD_SIZE:
        return 'Senha deve ter pelo menos 10 dígitos.'


def user_login(data):
    error = _common_register_login(data, LOGIN_KEYS)
    if error:
        return error
    if data['email'] not in all_users:
        return 'Usuário e/ou senha incorretos'

def user_register(data):
    error = _common_register_login(data, REGISTER_KEYS)
    if error:
        return error

    if data['email'] in all_users:
        return 'Usuário já registrado.'


def _common_crime_review(data, keys):
    for key in keys:
        if key not in data.keys():
            return 'Incomplete data: {0}.'.format(key)

    for key, val in data.items():
        if not str(val).strip():
            return '{0} is empty'.format(key)

    latlng_types = (int, float)
    if type(data['lng']) not in latlng_types or type(data['lat']) not in latlng_types:
        return 'Incorrect type for latitude and/or Longitute.'

    # valid position? 
    if not (-90. <= data['lat'] <= 90.) or not (-180. <= data['lng'] <= 180.):
        return 'Longitute and/or latitude out of range.'

def crime(data):
    error = _common_crime_review(data, CRIME_kEYS)
    if error:
        return error

    if not (1 <= data['weight'] <= 5):
        return 'Weight out of range.'

def review(data):
    error = _common_crime_review(data, REVIEW_KEYS)
    if error:
        return error

    num_keys = ['lat', 'lng', 'score']
    text_keys = [k for k in REVIEW_KEYS if k not in num_keys]
    for k in text_keys:
        pass # TODO: validate stuff 