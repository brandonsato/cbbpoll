from cbbpoll import app, db, bot
from models import User, Team
from decorators import async

def team_by_flair(flair):
    return Team.query.filter_by(flair = flair).first()

@async
def update_flair(user, redditor):
    user_flair = None
    for flair in bot.subreddit('collegebasketball').flair(redditor=redditor):
        user_flair = flair

    if user_flair:
        if user_flair['flair_css_class']:
            flair_class = user_flair['flair_css_class']
            flair_text = user_flair['flair_text']
            text_team_object = team_by_flair(flair_text)
            class_team_object = team_by_flair(flair_class)
            #case matched flair text
            if text_team_object:
                #don't need to modify flair that already matches
                if user.flair != text_team_object.id:
                    user.flair = text_team_object.id
                    db.session.add(user)
                    db.session.commit()
            elif class_team_object:
                #don't need to modify flair that already matches
                if user.flair != class_team_object.id:
                    user.flair = class_team_object.id
                    db.session.add(user)
                    db.session.commit()
            #case couldn't match flair
            elif user.flair:
                user.flair = None
                db.session.add(user)
                db.session.commit()     
        #case no flair
        elif user.flair:
            user.flair = None
            db.session.add(user)
            db.session.commit()
