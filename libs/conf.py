import json

import socketio
from sqlalchemy import create_engine, URL
from sqlalchemy.orm import sessionmaker, declarative_base

conn_gpt = URL.create("mssql+pyodbc",
                      username="reteller",
                      password="567890",
                      host="idc.venndata.cn",
                      port=30014,
                      database="VennGpt",
                      query={
                          "driver": "ODBC Driver 17 for SQL Server",
                          "Encrypt": "yes",
                          "TrustServerCertificate": "yes",
                      },
                      )

conn_dash = URL.create("mssql+pyodbc",
                       username="reteller",
                       password="567890",
                       host="idc.venndata.cn",
                       port=30014,
                       database="VennDash_test",
                       query={
                           "driver": "ODBC Driver 17 for SQL Server",
                           "Encrypt": "yes",
                           "TrustServerCertificate": "yes",
                       },
                       )

Base = declarative_base()


def get_session(db='gpt'):
    if db == 'gpt':
        engine = create_engine(conn_gpt)
    else:
        engine = create_engine(conn_dash)
    session = sessionmaker(bind=engine)
    return session


sio = socketio.AsyncServer(async_mode='asgi', cors_allowed_origins='*')
