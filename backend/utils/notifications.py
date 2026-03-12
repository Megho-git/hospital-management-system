from application.extensions import db
from application.models import Notification


def create_notification(user_id, title, message, type="system", link=None):
    n = Notification(
        user_id=user_id,
        title=title,
        message=message,
        type=type,
        link=link,
        is_read=False,
    )
    db.session.add(n)
    db.session.commit()
    return n

