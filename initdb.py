import pathlib
import contextlib

stdout = open("debug.log", "w")

with contextlib.redirect_stderr(stdout):
    pathlib.Path("./data/app.db").unlink(missing_ok=True)

    from models import db, User, Msg, Token

    db.connect()
    db.create_tables([User, Msg, Token])
    

    users =  [{
        "name":"StormedJane",
        "display_name":"StormedJane",
        "password":"mfnmO.1858"
    },
    {
        "name":"EIJwasofoi",
        "password":"iorndfgferhg098ehjr9oh90",
        "display_name":"EIJwasofoi"
    }]

    msgs = [{
        "user":"StormedJane", "message":"Bro wtf this works lmao",
    },
    {
        "user":"StormedJane", "message":"Bro lmao even replies are here gg",
        "replies":[
            {"user":"StormedJane", "message":"Lmao true"},
            {"user":"StormedJane", "message":"I could do this all day"},
            {"user":"StormedJane", "message":"Test test test test"},
        ]
    },
    {
        "user":"StormedJane", "message":"Peepee poopoo yaou cant read dis",
        "replies":[
            {"user":"EIJwasofoi", "message":"Pff, yes I can"},
            {"user":"EIJwasofoi", "message":"It says [Deleted]"},
        ],
        "deleted":True
    }
    ]
    
    def make_message(msg, reply_to=None):
        new_msg = Msg.create(user=User.get(name=msg["user"]), message=msg["message"])

        if msg.get("deleted"):
            new_msg.mark_deleted()

        if reply_to:
            new_msg.reply_to = reply_to
            new_msg.save()
        

        if "replies" in msg:
            for r in msg["replies"]:
                make_message(r, new_msg)

        return new_msg

    for user in users:
        new_user = User.create(**user)
        new_user.set_password(user.get("password", "1234"))

    for msg in msgs:
        new_msg = make_message(msg)

    for msg in Msg.select():
        print(f"{msg.user.display_name}: {msg.message} > {msg.reply_to}")