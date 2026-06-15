from datetime import datetime
from werkzeug.security import generate_password_hash
from flask_login import UserMixin
from extensions import db


class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    users = db.relationship('User', backref='role', lazy=True)


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    login = db.Column(db.String(100), nullable=False, unique=True)
    password_hash = db.Column(db.String(255), nullable=False)
    surname = db.Column(db.String(100), nullable=False)
    first_name = db.Column(db.String(100), nullable=False)
    patronymic = db.Column(db.String(100), nullable=True)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'), nullable=False)
    reviews = db.relationship('Review', backref='user', lazy=True)

    def full_name(self) -> str:
        parts = [self.surname, self.first_name, self.patronymic or '']
        return ' '.join(filter(None, parts))

    def is_admin(self):
        return self.role.name == 'admin'

    def is_moderator(self):
        return self.role.name == 'moderator'


class Genre(db.Model):
    __tablename__ = 'genres'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    books = db.relationship('Book', secondary='book_genre', backref='genres')


class Book(db.Model):
    __tablename__ = 'books'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    short_description = db.Column(db.Text, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    publisher = db.Column(db.String(255), nullable=False)
    author = db.Column(db.String(255), nullable=False)
    pages = db.Column(db.Integer, nullable=False)
    cover = db.relationship('Cover', backref='book', uselist=False,
                            cascade='all, delete')
    reviews = db.relationship('Review', backref='book', lazy=True,
                               cascade='all, delete')


class Cover(db.Model):
    __tablename__ = 'covers'
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    mime_type = db.Column(db.String(100), nullable=False)
    md5_hash = db.Column(db.String(32), nullable=False)
    book_id = db.Column(db.Integer,
                        db.ForeignKey('books.id', ondelete='CASCADE'),
                        nullable=False)

class ReviewStatus(db.Model):
    __tablename__ = 'review_statuses'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    reviews = db.relationship('Review', backref='status', lazy=True)


class Review(db.Model):
    __tablename__ = 'reviews'
    id = db.Column(db.Integer, primary_key=True)
    book_id = db.Column(db.Integer,
                        db.ForeignKey('books.id', ondelete='CASCADE'),
                        nullable=False)
    user_id = db.Column(db.Integer,
                        db.ForeignKey('users.id', ondelete='CASCADE'),
                        nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    text = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow,
                           nullable=False)
    status_id = db.Column(db.Integer,
                          db.ForeignKey('review_statuses.id', ondelete='CASCADE'),
                          nullable=False)


book_genre = db.Table(
    'book_genre',
    db.Column('book_id', db.Integer,
              db.ForeignKey('books.id', ondelete='CASCADE'),
              primary_key=True),
    db.Column('genre_id', db.Integer,
              db.ForeignKey('genres.id', ondelete='CASCADE'),
              primary_key=True)
)


def seed_data():
    if not Role.query.first():
        for r in [
            ('admin', 'Администратор (полный доступ)'),
            ('moderator', 'Модератор (редактирование книг и рецензий)'),
            ('user', 'Пользователь (оставление рецензий)')
        ]:
            db.session.add(Role(name=r[0], description=r[1]))
        db.session.commit()

        for g in ['Фантастика', 'Детектив', 'Роман', 'Ужасы', 'Мистика',
                  'Триллер', 'Психологическая драма',
                  'Научная литература', 'История', 'Поэзия']:
            db.session.add(Genre(name=g))
        db.session.commit()

        for s in ['На рассмотрении', 'Одобрена', 'Отклонена']:
            db.session.add(ReviewStatus(name=s))
        db.session.commit()

        admin_role = Role.query.filter_by(name='admin').first()
        mod_role = Role.query.filter_by(name='moderator').first()
        user_role = Role.query.filter_by(name='user').first()

        db.session.add(User(
            login='admin', password_hash=generate_password_hash('admin'),
            surname='Администров', first_name='Админ', patronymic='Админович',
            role_id=admin_role.id
        ))
        db.session.add(User(
            login='moderator', password_hash=generate_password_hash('moderator'),
            surname='Модераторов', first_name='Модератор', patronymic='Модераторович',
            role_id=mod_role.id
        ))
        db.session.add(User(
            login='user', password_hash=generate_password_hash('user'),
            surname='Пользователев', first_name='Пользователь', patronymic='Пользовательевич',
            role_id=user_role.id
        ))
        db.session.commit()