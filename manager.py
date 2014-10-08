from flask.ext.script import Manager
from flask.ext.migrate import MigrateCommand
from cbbpoll import app, remind

manager = Manager(app)
manager.add_command('db', MigrateCommand)
manager.add_command('remind', remind.ReminderCommand)


if __name__ == '__main__':
    manager.run()
