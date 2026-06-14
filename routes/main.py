from flask import Blueprint, render_template, request, send_from_directory, current_app, session
from flask_login import current_user
from models import Book, Genre, Review
from extensions import db
from utils import md_to_html

bp = Blueprint('main', __name__)


@bp.route('/')
def index():
    if request.args.get('clear'):
        session.pop('filters', None)

    has_filters = any(k in request.args for k in ['title', 'author', 'genre', 'year', 'pages_from', 'pages_to'])

    if has_filters:
        session['filters'] = {
            'title': request.args.get('title', ''),
            'author': request.args.get('author', ''),
            'genre': request.args.getlist('genre', type=int),
            'year': request.args.getlist('year', type=int),
            'pages_from': request.args.get('pages_from', ''),
            'pages_to': request.args.get('pages_to', ''),
        }
        f_title = request.args.get('title', '')
        f_genres = request.args.getlist('genre', type=int)
        f_years = request.args.getlist('year', type=int)
        f_pf = request.args.get('pages_from', '')
        f_pt = request.args.get('pages_to', '')
        f_author = request.args.get('author', '')
    elif session.get('filters'):
        saved = session['filters']
        f_title = saved.get('title', '')
        f_genres = saved.get('genre', [])
        f_years = saved.get('year', [])
        f_pf = saved.get('pages_from', '')
        f_pt = saved.get('pages_to', '')
        f_author = saved.get('author', '')
    else:
        f_title = ''
        f_genres = []
        f_years = []
        f_pf = ''
        f_pt = ''
        f_author = ''

    page = request.args.get('page', 1, type=int)

    q = Book.query

    if f_title:
        q = q.filter(Book.title.ilike(f'%{f_title}%'))
    if f_author:
        q = q.filter(Book.author.ilike(f'%{f_author}%'))
    if f_genres:
        q = q.filter(Book.genres.any(Genre.id.in_(f_genres)))
    if f_years:
        q = q.filter(Book.year.in_(f_years))
    if f_pf:
        q = q.filter(Book.pages >= int(f_pf))
    if f_pt:
        q = q.filter(Book.pages <= int(f_pt))

    books = q.order_by(Book.year.desc(), Book.id.desc()).paginate(
        page=page, per_page=10, error_out=False
    )

    all_years = [y[0] for y in db.session.query(Book.year).distinct()
                 .order_by(Book.year.desc()).all()]
    all_genres = Genre.query.order_by(Genre.name).all()

    return render_template(
        'index.html', books=books,
        all_years=all_years, all_genres=all_genres,
        f_title=f_title, f_genres=f_genres, f_years=f_years,
        f_pf=f_pf, f_pt=f_pt, f_author=f_author
    )


@bp.route('/book/<int:book_id>')
def book_view(book_id):
    book = Book.query.get_or_404(book_id)
    reviews = Review.query.filter_by(book_id=book_id)\
                          .order_by(Review.created_at.desc()).all()

    user_review = None
    if current_user.is_authenticated:
        user_review = Review.query.filter_by(
            book_id=book_id, user_id=current_user.id
        ).first()

    can_review = (
        current_user.is_authenticated
        and not user_review
        and (current_user.is_admin()
             or current_user.is_moderator()
             or current_user.role.name == 'user')
    )

    avg = db.session.query(db.func.avg(Review.rating))\
                    .filter_by(book_id=book_id).scalar()
    cnt = Review.query.filter_by(book_id=book_id).count()

    return render_template(
        'book_view.html', book=book, reviews=reviews,
        user_review=user_review, can_review=can_review,
        avg_rating=round(avg, 2) if avg else None,
        review_count=cnt, md=md_to_html
    )


@bp.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(current_app.config['UPLOAD_FOLDER'], filename)