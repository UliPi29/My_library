import os
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from models import Book, Genre, Cover
from extensions import db
from utils import sanitize_md, allowed_file, file_md5, can_edit, can_delete

bp = Blueprint('books', __name__)


@bp.route('/book/add', methods=['GET', 'POST'])
@login_required
def book_add():
    if not can_edit(current_user):
        flash('У вас недостаточно прав для выполнения данного действия', 'danger')
        return redirect(url_for('main.index'))

    genres = Genre.query.order_by(Genre.name).all()

    if request.method == 'POST':
        try:
            title = request.form.get('title')
            desc = request.form.get('short_description')
            year = request.form.get('year', type=int)
            publisher = request.form.get('publisher')
            author = request.form.get('author')
            pages = request.form.get('pages', type=int)
            sel_genres = request.form.getlist('genres', type=int)
            cover_file = request.files.get('cover')

            if not all([title, desc, year, publisher, author, pages]):
                raise ValueError('Заполните все обязательные поля')

            book = Book(
                title=title,
                short_description=sanitize_md(desc),
                year=year,
                publisher=publisher,
                author=author,
                pages=pages
            )
            if sel_genres:
                book.genres = Genre.query.filter(
                    Genre.id.in_(sel_genres)
                ).all()

            db.session.add(book)
            db.session.flush()

            if cover_file and cover_file.filename:
                if not allowed_file(cover_file.filename):
                    raise ValueError('Недопустимый формат обложки')

                md5 = file_md5(cover_file)
                existing = Cover.query.filter_by(md5_hash=md5).first()

                if existing:
                    cover = Cover(
                        filename=existing.filename,
                        mime_type=existing.mime_type,
                        md5_hash=md5,
                        book_id=book.id
                    )
                    db.session.add(cover)
                else:
                    ext = cover_file.filename.rsplit('.', 1)[1].lower()
                    cover = Cover(
                        filename='temp',
                        mime_type=cover_file.content_type or 'image/jpeg',
                        md5_hash=md5,
                        book_id=book.id
                    )
                    db.session.add(cover)
                    db.session.flush()

                    fname = f"{cover.id}.{ext}"
                    cover.filename = fname
                    fpath = os.path.join(current_app.config['UPLOAD_FOLDER'], fname)
                    cover_file.save(fpath)

            db.session.commit()
            flash('Книга успешно добавлена', 'success')
            return redirect(url_for('main.book_view', book_id=book.id))

        except Exception:
            db.session.rollback()
            flash(
                'При сохранении данных возникла ошибка. '
                'Проверьте корректность введённых данных.',
                'danger'
            )
            return render_template(
                'book_form.html', genres=genres, book=None,
                edit_mode=False, form_data=request.form
            )

    return render_template(
        'book_form.html', genres=genres, book=None, edit_mode=False
    )


@bp.route('/book/<int:book_id>/edit', methods=['GET', 'POST'])
@login_required
def book_edit(book_id):
    if not can_edit(current_user):
        flash('У вас недостаточно прав для выполнения данного действия', 'danger')
        return redirect(url_for('main.index'))

    book = Book.query.get_or_404(book_id)
    genres = Genre.query.order_by(Genre.name).all()

    if request.method == 'POST':
        try:
            book.title = request.form.get('title')
            book.short_description = sanitize_md(
                request.form.get('short_description')
            )
            book.year = request.form.get('year', type=int)
            book.publisher = request.form.get('publisher')
            book.author = request.form.get('author')
            book.pages = request.form.get('pages', type=int)

            sel_genres = request.form.getlist('genres', type=int)
            book.genres = Genre.query.filter(
                Genre.id.in_(sel_genres)
            ).all() if sel_genres else []

            db.session.commit()
            flash('Книга успешно обновлена', 'success')
            return redirect(url_for('main.book_view', book_id=book.id))

        except Exception:
            db.session.rollback()
            flash(
                'При сохранении данных возникла ошибка. '
                'Проверьте корректность введённых данных.',
                'danger'
            )
            return render_template(
                'book_form.html', genres=genres, book=book, edit_mode=True
            )

    return render_template(
        'book_form.html', genres=genres, book=book, edit_mode=True
    )


@bp.route('/book/<int:book_id>/delete', methods=['POST'])
@login_required
def book_delete(book_id):
    if not can_delete(current_user):
        flash('У вас недостаточно прав для выполнения данного действия', 'danger')
        return redirect(url_for('main.index'))

    book = Book.query.get_or_404(book_id)

    try:
        if book.cover:
            dupes = Cover.query.filter(
                Cover.filename == book.cover.filename,
                Cover.id != book.cover.id
            ).count()
            if dupes == 0:
                fpath = os.path.join(
                    current_app.config['UPLOAD_FOLDER'], book.cover.filename
                )
                if os.path.exists(fpath):
                    os.remove(fpath)

        db.session.delete(book)
        db.session.commit()
        flash('Книга успешно удалена', 'success')
    except Exception:
        db.session.rollback()
        flash('Ошибка при удалении книги', 'danger')

    return redirect(url_for('main.index'))