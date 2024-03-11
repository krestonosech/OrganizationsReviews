from flask import Flask, render_template, request, jsonify
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

app = Flask(__name__)
engine = create_engine('sqlite:///reviews.db', echo=True)
db_session = scoped_session(sessionmaker(bind=engine))

Base = declarative_base()
Base.query = db_session.query_property()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    password = Column(String(128), nullable=False)

    def __init__(self, username, password):
        self.username = username
        self.password = password

    def __repr__(self):
        return '<User %r>' % self.username

class Organization(Base):
    __tablename__ = 'organizations'
    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True, nullable=False)
    address = Column(String(128), nullable=False)

    def __init__(self, name, address):
        self.name = name
        self.address = address

    def __repr__(self):
        return '<Organization %r>' % self.name

class Review(Base):
    __tablename__ = 'reviews'
    id = Column(Integer, primary_key=True)
    organization_id = Column(Integer, nullable=False)
    user_id = Column(Integer, nullable=False)
    rating = Column(Integer, nullable=False)
    review = Column(String(500), nullable=False)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)

    def __init__(self, organization_id, user_id, rating, review):
        self.organization_id = organization_id
        self.user_id = user_id
        self.rating = rating
        self.review = review

    def __repr__(self):
        return '<Review %r>' % self.id

Base.metadata.create_all(bind=engine)

def add_user(username, password):
    existing_user = User.query.filter_by(username=username).first()
    if existing_user is not None:
        print(f"Username {username} is already taken.")
        return
    new_user = User(username=username, password=password)
    db_session.add(new_user)
    db_session.commit()

add_user('admin', 'admin')
add_user('Petya', '1234')
add_user('Kolya', 'nagibator2005')

@app.route('/')
def home():
    return render_template('mama.html')

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    user = User.query.filter_by(username=username).first()
    if user and user.password == password:
        return jsonify({'success': True})
    else:
        return jsonify({'success': False})

@app.route('/add_organization', methods=['POST'])
def add_organization():
    data = request.get_json()
    name = data.get('name')
    address = data.get('address')
    new_organization = Organization(name=name, address=address)
    db_session.add(new_organization)
    db_session.commit()
    return jsonify({'message': 'Organization added successfully'})

@app.route('/get_org_id/<org_name>', methods=['GET'])
def get_org_id(org_name):
    organization = Organization.query.filter_by(name=org_name).first()
    if organization is None:
        return jsonify({'message': 'Organization not found'}), 404
    return jsonify({'id': organization.id})


@app.route('/organizations', methods=['GET'])
def get_organizations():
    organizations = Organization.query.all()
    return jsonify([{'id': org.id, 'name': org.name, 'address': org.address} for org in organizations])


@app.route('/edit_organization/<int:id>', methods=['PUT'])
def edit_organization(id):
    data = request.get_json()
    organization_to_edit = Organization.query.get(id)
    if organization_to_edit is None:
        return jsonify({'message': 'Organization not found'}), 404

    organization_to_edit.name = data.get('name')
    organization_to_edit.address = data.get('address')
    db_session.commit()
    return jsonify({'message': 'Organization edited successfully'})

@app.route('/delete_organization/<int:id>', methods=['DELETE'])
def delete_organization(id):
    organization_to_delete = Organization.query.get(id)
    if organization_to_delete is None:
        return jsonify({'message': 'Organization not found'}), 404

    # Удалите все отзывы, связанные с этой организацией
    Review.query.filter_by(organization_id=id).delete()

    db_session.delete(organization_to_delete)
    db_session.commit()
    return jsonify({'message': 'Organization and its reviews deleted successfully'})


@app.route('/add_review/<int:org_id>', methods=['POST'])
def add_review(org_id):
    data = request.get_json()
    user_id = data.get('user_id')
    rating = data.get('rating')
    review = data.get('review')
    new_review = Review(organization_id=org_id, user_id=user_id, rating=rating, review=review)
    db_session.add(new_review)
    db_session.commit()
    return jsonify({'message': 'Review added successfully'})

@app.route('/get_reviews/<int:org_id>', methods=['GET'])
def get_reviews(org_id):
    reviews = Review.query.filter_by(organization_id=org_id).all()
    return jsonify([{'user_id': rev.user_id, 'rating': rev.rating, 'review': rev.review} for rev in reviews])

if __name__ == '__main__':
    app.run(debug=True)
