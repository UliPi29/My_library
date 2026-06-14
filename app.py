import os
from flask import Flask
from extensions import db, login_manager
from utils import md_to_html, can_edit, can_delete
from models import seed_data


def create_app():
    app = Flask(__name__)
    app.config.from_object('config.Config')

    db.init_app(app)
    login_manager.init_app(app)

    login_manager.login_view = 'auth.login'
    login_manager.login_message = (
        'Для выполнения данного действия необходимо пройти процедуру аутентификации'
    )
    login_manager.login_message_category = 'warning'

    @app.context_processor
    def inject_helpers():
        return dict(can_edit=can_edit, can_delete=can_delete, md=md_to_html)

    from routes import main, auth, books, reviews
    app.register_blueprint(main.bp)
    app.register_blueprint(auth.bp)
    app.register_blueprint(books.bp)
    app.register_blueprint(reviews.bp)

    with app.app_context():
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        db.create_all()
        seed_data()

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)