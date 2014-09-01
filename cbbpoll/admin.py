from flask import redirect, url_for, flash
from flask.ext import admin
from flask.ext.admin import expose
from flask.ext.admin.contrib import sqla
from flask.ext.login import current_user

from cbbpoll import app, db
from models import User

class AdminModelView(sqla.ModelView):
    def is_accessible(self):
        return current_user.is_admin()

class MyAdminIndexView(admin.AdminIndexView):
    @expose('/')
    def index(self):
        if not current_user.is_admin():
            return redirect(url_for('index'))
        return super(MyAdminIndexView, self).index()


class UserAdmin(AdminModelView):
    column_display_pk = True
    form_columns = ['nickname', 'email', 'role']
    column_list = ['id', 'nickname', 'email', 'role']
    column_searchable_list = ('nickname', 'email')



# Create admin
admin = admin.Admin(app, 'Simple Models', index_view=MyAdminIndexView())
admin.add_view(UserAdmin(User, db.session))