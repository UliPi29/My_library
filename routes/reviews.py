from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models import Book, Review, ReviewStatus
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
    approved_status = ReviewStatus.query.filter_by(name='Одобрена').first()
    pending_status = ReviewStatus.query.filter_by(name='На рассмотрении').first()
    
    has_active = Review.query.filter(
        Review.book_id == book_id,
        Review.user_id == current_user.id,
        Review.status_id.in_([approved_status.id, pending_status.id])
    ).first()

    if has_active:
        flash('Вы уже оставляли рецензию на эту книгу', 'warning')
        return redirect(url_for('main.book_view', book_id=book_id))

    if request.method == 'POST':
        try:
            rating = request.form.get('rating', type=int)
            text = request.form.get('text')
            if rating is None or not text:
                raise ValueError('Заполните все поля')

            pending = ReviewStatus.query.filter_by(name='На рассмотрении').first()
            review = Review(
                book_id=book_id,
                user_id=current_user.id,
                rating=rating,
                text=sanitize_md(text),
                status_id=pending.id
            )
            db.session.add(review)
            db.session.commit()
            flash('Рецензия отправлена на рассмотрение', 'success')
            return redirect(url_for('main.book_view', book_id=book_id))

        except Exception:
            db.session.rollback()
            flash('При сохранении данных возникла ошибка', 'danger')
            return render_template('review_form.html', book=book)

    return render_template('review_form.html', book=book)


@bp.route('/my_reviews')
@login_required
def my_reviews():
    if current_user.role.name != 'user':
        flash('У вас недостаточно прав', 'danger')
        return redirect(url_for('main.index'))

    reviews = Review.query.filter_by(user_id=current_user.id)\
                          .order_by(Review.created_at.desc()).all()
    return render_template('my_reviews.html', reviews=reviews)


@bp.route('/moderation')
@login_required
def moderation():
    if not (current_user.is_admin() or current_user.is_moderator()):
        flash('У вас недостаточно прав', 'danger')
        return redirect(url_for('main.index'))

    page = request.args.get('page', 1, type=int)
    pending = ReviewStatus.query.filter_by(name='На рассмотрении').first()
    
    reviews = Review.query.filter_by(status_id=pending.id)\
                          .order_by(Review.created_at.asc())\
                          .paginate(page=page, per_page=10, error_out=False)
    return render_template('moderation.html', reviews=reviews)


@bp.route('/review/<int:review_id>/moderate')
@login_required
def moderate_review(review_id):
    if not (current_user.is_admin() or current_user.is_moderator()):
        flash('У вас недостаточно прав', 'danger')
        return redirect(url_for('main.index'))

    review = Review.query.get_or_404(review_id)
    return render_template('review_moderate.html', review=review)


@bp.route('/review/<int:review_id>/approve', methods=['POST'])
@login_required
def approve_review(review_id):
    if not (current_user.is_admin() or current_user.is_moderator()):
        flash('У вас недостаточно прав', 'danger')
        return redirect(url_for('main.index'))

    review = Review.query.get_or_404(review_id)
    approved = ReviewStatus.query.filter_by(name='Одобрена').first()
    review.status_id = approved.id
    db.session.commit()
    flash('Рецензия одобрена', 'success')
    return redirect(url_for('reviews.moderation'))


@bp.route('/review/<int:review_id>/reject', methods=['POST'])
@login_required
def reject_review(review_id):
    if not (current_user.is_admin() or current_user.is_moderator()):
        flash('У вас недостаточно прав', 'danger')
        return redirect(url_for('main.index'))

    review = Review.query.get_or_404(review_id)
    rejected = ReviewStatus.query.filter_by(name='Отклонена').first()
    review.status_id = rejected.id
    db.session.commit()
    flash('Рецензия отклонена', 'success')
    return redirect(url_for('reviews.moderation'))