To get set up:

    # Install Python dependencies
    pip install -r requirements.txt
    # Copy the sample config file and edit it
    cp config.sample.py config.py
    vim config.py
    # Create MySQL tables with config information from config.py
    python manager.py db upgrade
    # Start praw service for contacting reddit
    praw-multiprocess
    # Start a local server at http://localhost:5000
    python manager.py runserver

To create a migration after a model change:

    python manager.py db migrate -m ["migration comment"]
