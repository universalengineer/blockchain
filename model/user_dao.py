from sqlalchemy import text


class UserDao:
    def __init__(self, session):
        self.db = session

    def commit(self):
        self.db.commit()

    def rollback(self):
        self.db.rollback()

    def insert_user(self, user):
        sql = """
            INSERT INTO users (
                name,
                email,
                profile,
                hashed_password
            ) VALUES (
                :name,
                :email,
                :profile,
                :password
            )
            """
        return self.db.execute(text(sql), user).lastrowid

    def get_user_id_and_password(self, email):
        row = self.db.execute(text("""
            SELECT
                id,
                hashed_password
            FROM users
            WHERE email = :email
        """), {'email': email}).fetchone()

        return {
            'id': row['id'],
            'hashed_password': row['hashed_password']
        } if row else None


    #
    # def get_user_id_and_password(self, jos, jos2):
    #     sql = """
    #         SELECT * FROM member
    #         WHERE USERNAME = :id and PASSWORD = :pw
    #         """
    #     row = self.db.execute(text(sql), {"id": jos, "pw": jos2}).fetchone()
    #     return {
    #         'aaa': row['NICK_NAME'],
    #         'bbb': row['MEMBER_NAME']
    #     } if row else None
