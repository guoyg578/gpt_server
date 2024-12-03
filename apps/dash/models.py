from sqlalchemy import Column, String, Integer, select, Boolean, DateTime

from libs.conf import Base


class Users(Base):
    __tablename__ = 'dash_users'

    username = Column(String, primary_key=True)
    password = Column(String, nullable=True)
    roleId = Column(Integer, nullable=True)


class Message(Base):
    __tablename__ = 'dash_messages'

    id = Column(Integer, autoincrement=True, primary_key=True)
    role = Column(String, nullable=True)
    content = Column(String, nullable=True)
    creator = Column(String, nullable=True)
    createTime = Column(String, nullable=True)


class Recommend(Base):
    __tablename__ = 'dash_recommend'

    pk = Column(Integer, autoincrement=True, primary_key=True)
    content = Column(String, nullable=True)
    params = Column(String, nullable=True)
    creator = Column(String, nullable=True)
    createTime = Column(String, nullable=True)


class Cate(Base):
    __tablename__ = 'dash_cate'

    cateId = Column(Integer, autoincrement=True, primary_key=True)
    subjectId = Column(Integer)
    cateLabelCn = Column(String, nullable=True)
    cateLabelEn = Column(String, nullable=True)
    cateLevel = Column(Integer, nullable=True)
    cateName = Column(String, nullable=True)
    flag = Column(Boolean, nullable=True)


class Channel(Base):
    __tablename__ = 'dash_channel'

    channelId = Column(Integer, autoincrement=True, primary_key=True)
    channelLabelCn = Column(String, nullable=True)
    channelLabelEn = Column(String, nullable=True)
    channelName = Column(String, nullable=True)
    flag = Column(Boolean, nullable=True)


class Page(Base):
    __tablename__ = 'aa_chart_page'

    pageId = Column(Integer, primary_key=True)
    level = Column(Integer, nullable=True)
    url = Column(String, nullable=True)
    label = Column(String, nullable=True)
    pageType = Column(String, nullable=True)
    template = Column(String, nullable=True)
    titleSuffix = Column(String, nullable=True)
    key = Column(String, nullable=True)
    usage = Column(String, nullable=True)
    major_dimension = Column(String, nullable=True)
    minor_dimension = Column(String, nullable=True)
    columns = Column(String, nullable=True)
    rows = Column(String, nullable=True)
    total = Column(String, nullable=True)
    single = Column(String, nullable=True)
    compare = Column(String, nullable=True)
    filter = Column(String, nullable=True)


class Measure(Base):
    __tablename__ = 'dash_button'

    buttonId = Column(String, nullable=True, primary_key=True)
    buttonLabelCn = Column(String, nullable=True)
    buttonValue = Column(String, nullable=True)


class Issue(Base):
    __tablename__ = 'dash_issue'

    pk = Column(String, nullable=True, primary_key=True)
    content = Column(String, nullable=True)
    params = Column(String, nullable=True)
    parentId = Column(Integer, nullable=True)


class DashLogsLogin(Base):
    __tablename__ = 'dash_logs_login'

    createTime = Column(DateTime, nullable=True, primary_key=True)
    username = Column(String, nullable=True)


class DashLogsQues(Base):
    __tablename__ = 'dash_logs_ques'

    _index = Column(String, nullable=True)
    question = Column(String, nullable=True)
    complete = Column(Boolean, nullable=True)
    love = Column(Boolean, nullable=True)
    memo = Column(String, nullable=True)
    sid = Column(String, nullable=True)
    username = Column(String, nullable=True)
    json_pivot = Column(String, nullable=True)
    data_pivot = Column(String, nullable=True)
    chart_text = Column(String, nullable=True)
    json_fix = Column(String, nullable=True)
    total_time = Column(Integer, nullable=True)
    error = Column(String, nullable=True)
    createTime = Column(DateTime, nullable=True, primary_key=True)
