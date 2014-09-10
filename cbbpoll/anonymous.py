from flask.ext.login import AnonymousUserMixin

class Anonymous(AnonymousUserMixin):
    def is_admin(self):
        return False