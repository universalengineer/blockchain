class DeptService:
    def __init__(self, dept_dao):
        self.dept_dao = dept_dao

    def dept(self, user_id, tweet):
        if len(tweet) > 300:
            return None
        return self.dept_dao.insert_tweet(user_id, tweet)

    def get_timeline(self, user_id):
        return self.dept_dao.get_timeline(user_id)