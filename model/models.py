# coding: utf-8
from sqlalchemy import BigInteger, Column, DateTime, ForeignKey, ForeignKeyConstraint, Index, Integer, Numeric, String, Table, Text
from sqlalchemy.schema import FetchedValue
from sqlalchemy.orm import relationship
from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()


class Member(db.Model):
    __tablename__ = 'member'
    __table_args__ = {'mysql_collate': 'utf8_general_ci'}

    MEMBER_ID = db.Column(db.BigInteger, primary_key=True)
    USERNAME = db.Column(db.String(128), nullable=False, unique=True)
    PASSWORD = db.Column(db.String(60), nullable=False)
    SOCIAL_ID = db.Column(db.BigInteger, index=True)
    PROFILE_IMG = db.Column(db.String(80))
    GENDER = db.Column(db.String(1))
    BIRTHDAY = db.Column(db.String(8))
    PHONE = db.Column(db.String(30))
    INTRO = db.Column(db.String(250))
    REMARKS = db.Column(db.String(80))
    ENABLED = db.Column(db.Integer, nullable=False, server_default=db.FetchedValue())
    DIV_CODE = db.Column(db.String(3))
    CODE_NO = db.Column(db.String(4))
    RESV_FIELD1 = db.Column(db.String(80))
    RESV_FIELD2 = db.Column(db.String(250))
    MEMBER_NAME = db.Column(db.String(128), nullable=False)
    NICK_NAME = db.Column(db.String(128), nullable=False, unique=True)
    FIND_ACCOUNT_QUESTION = db.Column(db.BigInteger)
    FIND_ACCOUNT_ANSWER = db.Column(db.String(250))
    HOMEPAGE = db.Column(db.String(250))
    BLOG = db.Column(db.String(250))
    ALLOW_MAILING = db.Column(db.String(1), nullable=False, server_default=db.FetchedValue())
    ALLOW_MESSAGE = db.Column(db.String(1), nullable=False, server_default=db.FetchedValue())
    DENIED = db.Column(db.String(1), server_default=db.FetchedValue())
    LIMIT_DATE = db.Column(db.String(14))
    REGDATE = db.Column(db.String(14), nullable=False)
    LAST_LOGIN = db.Column(db.String(14))
    CHANGE_PASSWORD_DATE = db.Column(db.String(14))
    IS_ADMIN = db.Column(db.String(1), server_default=db.FetchedValue())
    DESCRIPTION = db.Column(db.Text)
    LIST_ORDER = db.Column(db.BigInteger, nullable=False, index=True)
    D_FLAG = db.Column(db.Integer, nullable=False, server_default=db.FetchedValue())
