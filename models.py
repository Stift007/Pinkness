from email.policy import default
import hashlib
import secrets
from peewee import BlobField, CharField, DateTimeField, BooleanField, DeferredForeignKey, ForeignKeyField, SqliteDatabase, Model, TextField
import datetime
import json

import settings

db = SqliteDatabase("./data/app.db", pragmas={"journal_mode":"wal"})

class BaseModel(Model):
    class Meta:
        database = db
        SCHEMA_VERSION = 0

class User(BaseModel):
    name = CharField(unique=True, index=True)
    password = TextField(default="")
    display_name = TextField(default="NULL")
    avatar = BlobField(null=True)
    settings = TextField(default=json.dumps({
        "censor_profanity":True,
        "embed_links":True
    }))

    @staticmethod
    def _hash_password(password):
        return hashlib.scrypt(bytes(password, encoding="utf-8"), salt=settings.SITE_KEY, n=16384, r=8, p=1).hex()

    def set_password(self, password):
        self.password = User._hash_password(password)
        self.save()

    def generate_token(self):
        new_token = Token.create(user=self)
        return new_token

    @staticmethod
    def get_user_by_token(request):
        token = request.cookies.token
        if not token:
            return None
        try:
            token = Token.get(id=token)
        except Token.DoesNotExist:
            return None

        if token.expires <= datetime.datetime.now():
            token.delete_instance()
            return None

        return token.user



class Msg(BaseModel):
    user = ForeignKeyField(User, backref="msgs")
    message = TextField()
    date = DateTimeField(default = datetime.datetime.now())
    reply_to = DeferredForeignKey("Msg", null=True)
    deleted_on = DateTimeField(null=True, index=True)

    msg_route_prefix = "/comments"

    def mark_deleted(self):
        self.deleted_on = datetime.datetime.now()
        self.save()

    def delete_link(self):
        return f'<a href="/delete/{self.id}"><button>Delete!</button></a>'

    def confirm_delete(self):
        return f'<form method="POST" action="/delete/{self.id}"><button type="submit">Yes, delete this Post!</button><input type="hidden" name="msg" value="{self.delete_hash()}"></form>'

    def delete_hash(self):
        m = hashlib.sha1()
        m.update(bytes(f"{self.user.id}|{self.id}", "utf-8"))
        return m.hexdigest()

    def undelete(self):
        self.deleted_on = None
        self.save()

    @property
    def link(self):
        return f"{self.msg_route_prefix}/{self.id}"

    @classmethod
    def get_live_posts(cls):
        return cls.select().where(cls.deleted_on.is_null())

    @classmethod
    def get_top_levels(cls):
        return cls.get_live_posts().where(cls.reply_to.is_null()).order_by(cls.date.desc())

    def replies(self):
        return Msg.get_live_posts().where(Msg.reply_to == self).order_by(Msg.date.desc())



class Token(BaseModel):
    id = TextField(primary_key=True, default=lambda: secrets.token_hex(32))
    user = ForeignKeyField(User, backref="tokens")
    expires = DateTimeField(
        default=lambda: datetime.datetime.now() + datetime.timedelta(days=7), index=True
    )