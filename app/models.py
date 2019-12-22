from app import db
from app.hotels import Hotel


class Review(db.Model):
  # Reminder: Can add more columns here
  id = db.Column(db.Integer, primary_key=True)
  absoluteUrl = db.Column(db.String(512), index=True, unique=True)
  createdDate = db.Column(db.String(32))
  stayDate = db.Column(db.String(32))
  publishedDate = db.Column(db.String(32))
  rating = db.Column(db.Float)

  username = db.Column(db.String(256))
  userId = db.Column(db.Integer)
  user_hometownId = db.Column(db.Integer)
  user_hometownName = db.Column(db.String(256))

  title = db.Column(db.String(2048))
  text = db.Column(db.String(100000))
  spacyText = db.Column(db.String(500000))

  hotelId = db.Column(db.String(128), db.ForeignKey("hotel.id"))


sentences = db.Table('tags',
    db.Column('unigram_text', db.String(64), db.ForeignKey('unigram.text'), primary_key=True),
    db.Column('sentence_id', db.Integer, db.ForeignKey('sentence.id'), primary_key=True)
)


class Unigram(db.Model):
  text = db.Column(db.String(64), primary_key=True)
  score = db.Column(db.Float)
  sentences = db.relationship("Sentence", secondary=sentences, lazy="subquery",
                              backref=db.backref("unigrams", lazy=True))


class Sentence(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  text = db.Column(db.String(10000))