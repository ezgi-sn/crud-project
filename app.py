from flask import Flask, jsonify, request, render_template, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String, Float
from flask_marshmallow import Marshmallow
from flask_jwt_extended import JWTManager, jwt_required, create_access_token
from flask_mail import Mail, Message
import os

app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'planets.db')
app.config['JWT_SECRET_KEY'] = 'super-secret'
app.config['MAIL_SERVER']='sandbox.smtp.mailtrap.io'
app.config['MAIL_PORT'] = 2525
app.config['MAIL_USERNAME'] = 'eca6974de1b3b6'
app.config['MAIL_PASSWORD'] = '8cb1b4e036200f'
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False

db = SQLAlchemy(app)
ma = Marshmallow(app) #orm
jwt = JWTManager(app)
mail = Mail(app)

#cmd->flask db_create
@app.cli.command('db_create')
def db_create():
    db.create_all()

@app.cli.command('db_drop')
def db_drop():
    db.drop_all()

#cmd->flask db_seed
#cli -> command line interface
@app.cli.command('db_seed')
def db_seed():
    mercury = Planet(planet_name='Mercury',
                     planet_type='Class b',
                     home_star='Sol',
                     mass= 3.128e23,
                     radius=1516,
                     distance=35.98e6)

    venus = Planet(planet_name='Venus',
                     planet_type='Class d',
                     home_star='Sol',
                     mass= 4.678e23,
                     radius=1516,
                     distance=35.98e6)
    earth = Planet(planet_name='Earth',
                     planet_type='Class m',
                     home_star='Sol',
                     mass=5.928e23,
                     radius=3959,
                     distance=92.98e6)
    db.session.add(mercury)
    db.session.add(venus)
    db.session.add(earth)

    test_user = User(first_name='William2',
                     last_name='Herschel2',
                     e_mail='test2@test.com',
                     password='P@ssw0rd' )
    db.session.add(test_user)
    db.session.commit()
    print('Database seeded')

@app.route('/')
def index():
    return render_template('main.html', name='ezgi')


@app.route('/about')
def about():
    return jsonify(message= 'About me')

@app.route('/not_found')
def not_found():
    return jsonify("That resouurce was not found"), 404

@app.route('/parameters')
def parameters():
    name = request.args.get('name')
    age = int(request.args.get('age'))
    if age<18:
        return jsonify(message = "Sorry " + name + " you are not old enough" ), 401
    else:
        return jsonify(message = "Welcome " + name)


@app.route('/url_variables/<string:name>/<int:age>')
def url_variables(name,age):
    if age<18:
        return jsonify(message = "Sorry " + name + " you are not old enough" ), 401
    else:
        return jsonify(message = "Welcome " + name)

@app.route('/planets', methods=['GET'])
def planets():
    planets_list=Planet.query.all()
    result = planets_schema.dump(planets_list)
    return jsonify(result)

@app.route('/register', methods=['POST'])
def register():
    email = request.form['email']
    test = User.query.filter_by(e_mail=email).first()
    if test:
        return jsonify(message="that email already exists"), 409
    else:
        first_name=request.form['first_name']
        last_name=request.form['last_name']
        password=request.form['password']
        user = User(first_name=first_name,last_name=last_name,e_mail=email,password=password)
        db.session.add(user)
        db.session.commit()
        return jsonify(message="user created successfully"), 201


@app.route('/login', methods=['POST'])
def login():
    if request.is_json:
        email = request.json['email']
        password = request.json['password']
    else:
        email = request.form['email']
        password = request.form['password']

    test = User.query.filter_by(e_mail=email, password=password).first()
    if test:
        access_token = create_access_token(identity=email)
        return jsonify(message="Login succeeded", access_token=access_token)
    else:
        return jsonify(message="bad email or password"),401

@app.route('/retrieve_password/<string:email>', methods=['GET'])
def retrieve_password(email:str):
    user = User.query.filter_by(e_mail=email).first()
    if user:
        msg = Message("your planetary api password is"+ user.password,
                      sender="admin@planetary",
                      recipients=[email])
        mail.send(msg)
        return jsonify("password sent to " + email)
    else:
        return jsonify("that email doesnt exist"), 401

@app.route('/planet_details/<int:planet_id>', methods=['GET'])
def planet_details(planet_id:int):
    planet = Planet.query.filter_by(planet_id=planet_id).first()
    if planet:
        result = planet_schema.dump(planet)
        return jsonify(result)
    else:
        return jsonify("that planet dooes not exist"),404

@app.route('/add_planet', methods=['POST'])
#@jwt_required uses for authentication
def add_planet():
    planet_name = request.form['planet_name']
    test = Planet.query.filter_by(planet_name=planet_name).first()
    if test:
        return jsonify("the planet already exists")
    else:
        planet_type = request.form['planet_type']
        home_star = request.form['home_star']
        mass = float(request.form['mass'])
        radius = float(request.form['radius'])
        distance = float(request.form['distance'])

        new_planet = Planet(planet_name=planet_name, planet_type=planet_type, home_star=home_star,
                            mass= mass, radius=radius, distance=distance )
        db.session.add(new_planet)
        db.session.commit()
        return jsonify("you added a planet")

#postman->body->form data
@app.route('/update_planet', methods=['PUT'])
def update_planet():
    planet_id = int(request.form['planet_id'])
    planet = Planet.query.filter_by(planet_id = planet_id).first()

    if planet:
        planet.planet_name = request.form['planet_name']
        planet.planet_type = request.form['planet_type']
        planet.home_star = request.form['home_star']
        planet.mass = float(request.form['mass'])
        planet.radius = float(request.form['radius'])
        planet.distance = float(request.form['distance'])
        db.session.commit()


@app.route('/remove_planet/<int:planet_id>', methods =['DELETE'])
def remove_planet(planet_id:int):
    planet = Planet.query.filter_by(planet_id=planet_id).first()
    if planet:
        db.session.delete(planet)
        db.session.commit()
        return jsonify("you deleted a planet"),202
    else:
        return jsonify("the planet does not exist")
#database models
class User(db.Model):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    first_name = Column(String)
    last_name = Column(String)
    e_mail = Column(String, unique=True)
    password = Column(String)
class Planet(db.Model):
    __tablename__ = 'planets'
    planet_id = Column(Integer, primary_key=True)
    planet_name = Column(String)
    planet_type = Column(String)
    home_star = Column(String)
    mass = Column(Float)
    radius = Column(Float)
    distance = Column(Float)

#schemas/used for object serialization
class UserSchema(ma.Schema):
    class Meta:
        fields = ('id', 'first_name', 'last_name', 'e_mail', 'password')
class PlanetSchema(ma.Schema):
    class Meta:
        fields = ('planet_id', 'planet_name', 'planet_type', 'home_star', 'mass',
                 'radius', 'distance')


user_schema = UserSchema()
users_schema = UserSchema(many=True)

planet_schema = PlanetSchema()
planets_schema = PlanetSchema(many=True)


if __name__ == '__main__':
    app.run(debug=True)
