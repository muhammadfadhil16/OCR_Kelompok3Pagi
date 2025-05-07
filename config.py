class Config:
    SECRET_KEY = 'secret'
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:@localhost/ekstraksiteks'
    SQLALCHEMY_TRACK_MODIFICATIONS = False