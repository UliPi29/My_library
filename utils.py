import hashlib
import bleach
import markdown
from flask_login import current_user

ALLOWED_TAGS = list(bleach.ALLOWED_TAGS) + [
    'p', 'br', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
    'img', 'pre', 'code', 'hr', 'blockquote'
]

ALLOWED_ATTRS = {
    **bleach.ALLOWED_ATTRIBUTES,
    'img': ['src', 'alt', 'title'],
    'a': ['href', 'title'],
    'code': ['class'],
}


def sanitize_md(text: str) -> str:
    return bleach.clean(text, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRS, strip=True)


def md_to_html(text: str) -> str:
    return markdown.markdown(sanitize_md(text), extensions=['nl2br', 'fenced_code'])


def allowed_file(fname: str) -> bool:
    return '.' in fname and fname.rsplit('.', 1)[1].lower() in {
        'png', 'jpg', 'jpeg', 'gif', 'webp'
    }


def file_md5(file_stream) -> str:
    file_stream.seek(0)
    h = hashlib.md5()
    while chunk := file_stream.read(8192):
        h.update(chunk)
    file_stream.seek(0)
    return h.hexdigest()


def can_edit(user) -> bool:
    if not user.is_authenticated:
        return False
    return user.is_admin() or user.is_moderator()


def can_delete(user) -> bool:
    if not user.is_authenticated:
        return False
    return user.is_admin()