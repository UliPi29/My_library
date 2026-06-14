from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models import Book, Review
from extensions import db
from utils import sanitize_md

bp = Blueprint('reviews', __name__)


@bp.route('/book/<int:book_id>/review', methods=['GET', 'POST'])
@login_required
def add_review(book_id):
    if not (current_user.is_admin()
            or current_user.is_moderator()
            or current_user.role.name == 'user'):
        flash('У вас недостаточно прав', 'danger')
        return redirect(url_for('main.index'))

    book = Book.query.get_or_404(book_id)

    if Review.query.filter_by(book_id=book_id,
                               user_id=current_user.id).first():
        flash('Вы уже оставляли рецензию на эту книгу', 'warning')
        return redirect(url_for('main.book_view', book_id=book_id))

    if request.method == 'POST':
        try:
            rating = request.form.get('rating', type=int)
            text = request.form.get('text')
            if rating is None or not text:
                raise ValueError('Заполните все поля')

            review = Review(
                book_id=book_id,
                user_id=current_user.id,
                rating=rating,
                text=sanitize_md(text)
            )
            db.session.add(review)
            db.session.commit()
            flash('Рецензия успешно добавлена', 'success')
            return redirect(url_for('main.book_view', book_id=book_id))

        except Exception:
            db.session.rollback()
            flash('При сохранении данных возникла ошибка', 'danger')
            return render_template('review_form.html', book=book)

    return render_template('review_form.html', book=book)


@bp.route('/review/<int:review_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_review(review_id):
    review = Review.query.get_or_404(review_id)
    if not (current_user.is_admin() or current_user.is_moderator()):
        flash('У вас недостаточно прав для выполнения данного действия', 'danger')
        return redirect(url_for('main.book_view', book_id=review.book_id))

    if request.method == 'POST':
        try:
            rating = request.form.get('rating', type=int)
            text = request.form.get('text')
            if rating is None or not text:
                raise ValueError('Заполните все поля')

            review.rating = rating
            review.text = sanitize_md(text)
            db.session.commit()
            flash('Рецензия обновлена', 'success')
            return redirect(url_for('main.book_view', book_id=review.book_id))

        except Exception:
            db.session.rollback()
            flash('При сохранении данных возникла ошибка', 'danger')
            return render_template('review_edit.html', review=review)

    return render_template('review_edit.html', review=review)


@bp.route('/review/<int:review_id>/delete', methods=['POST'])
@login_required
def delete_review(review_id):
    review = Review.query.get_or_404(review_id)
    if not (current_user.is_admin() or current_user.is_moderator()):
        flash('У вас недостаточно прав для выполнения данного действия', 'danger')
        return redirect(url_for('main.book_view', book_id=review.book_id))

    book_id = review.book_id
    db.session.delete(review)
    db.session.commit()
    flash('Рецензия удалена', 'success')
    return redirect(url_for('main.book_view', book_id=book_id))