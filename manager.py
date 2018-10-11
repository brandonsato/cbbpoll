from flask_script import Manager
from flask_migrate import MigrateCommand
from cbbpoll import app, remind, postcompleted

manager = Manager(app)

manager.add_command('db', MigrateCommand)
manager.add_command('remind', remind.ReminderCommand)

manager.add_command('post', postcompleted.PostCompletedCommand)


if __name__ == '__main__':
    manager.run()
