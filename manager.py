from flask.ext.script import Manager
from flask.ext.migrate import MigrateCommand
from cbbpoll import app, remind, postcompleted

manager = Manager(app)

manager.add_command('db', MigrateCommand)
manager.add_command('remind', remind.ReminderCommand)

manager.add_command('post', postcompleted.PostCompletedCommand)


if __name__ == '__main__':
    manager.run()
