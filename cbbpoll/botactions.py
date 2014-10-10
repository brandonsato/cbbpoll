from cbbpoll import app, db, bot
from models import User, Team
from decorators import async

def team_by_flair(flair):
    return Team.query.filter_by(flair = flair).first()

@async
def update_flair(user):
    user_flair = bot.get_flair('collegebasketball', user.nickname)
    team_id = None
    if user_flair:
        if user_flair['flair_text']:
            flair_text = user_flair['flair_text']
            team_object = team_by_flair(flair_text)
            #case matched flair
            if team_object:
                #don't need to modify flair that already matches
                if user.flair != team_object.id:
                    print 'new flair!'
                    user.flair = team_object.id
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
