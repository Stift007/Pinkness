import json
from bottle import route, template, run, request, response, redirect
from models import Msg, User, Token
from requests import get
import profanity


MSG = Msg.msg_route_prefix

def login_required(fn):
    def predicate(user, *args, **kwds):
        if not user:
            response.status = 401
            return login_route()

        return fn(user,*args,**kwds)

    return predicate

def fetch_message(fn):
    def predicate(msg_id, *args, **kwargs):
        msg = Msg.get(id=msg_id)
        if not msg:
            return template("error.html", t=404,message="No such message")
        return fn(msg, *args, **kwargs)

    return predicate

def get_user(fn):
    def wrapper(*args, **kwargs):
        user = User.get_user_by_token(request)
        if user and user.display_name == "NULL":
            user.display_name = user.name
            user.save()
        return fn(user, *args, **kwargs)

    return wrapper

@route("/cdn/user/<user_id:int>")
def usercdn(userid):
    user:User = User.get(id=userid)
    if user.avatar:
        return user.avatar
    return blob_null()
    
@route("/cdn/user/0")
def blob_null():
    return get("https://i.pinimg.com/originals/bd/70/22/bd702201a2b6d8960734f60f34a22754.jpg").content

@route("/")
@get_user
@login_required
def main_route(user:User):
    
    messages = Msg.get_top_levels().limit(7)
    for msg in messages:
        if msg.user.display_name == "NULL":
            msg.user.display_name = msg.user.name
            msg.save()
    return template("main.html", messages=messages, user=user, json=json)

@route(f"/", method="POST")
@get_user
@login_required
def main_route_post(user):
    post_message(user)
    return main_route()

@route(f"{MSG}/<msg_id:int>")
@fetch_message
@get_user
def read_msg(user, msg):

    return template("read_msg.html", user=user, msg=msg, json=json)

@route("/delete/<msg_id:int>")
@get_user
@login_required
def delete_message(user, msg_id):
    msg = Msg.get(id=msg_id, user=user)
    return template("delete_msg.html", user=user, msg=msg, json=json)

@route("/delete/<msg_id:int>", method="post")
@get_user
@login_required
def confirm_delete_message(user, msg_id):
    msg = Msg.get(id=msg_id, user=user)
    if request.forms.msg == msg.delete_hash():
        msg.mark_deleted()
        return "Deleted"
    return "Bad Message Hash"

@route(f"{MSG}/<msg_id:int>", method="POST")
@fetch_message
@get_user
@login_required
def read_msg_post(user, msg):
    reply = post_message(user, msg.id)
    return read_msg(msg.id)

@route("/@/<username>")
@get_user
def profile(user, username):
    try:
        up = User.get(name=username)
        if not up:
            return template("error.html", t=404,message=f"No such User: '@{username}'")

        return template("profile.html", user=up)
    except:
        return template("error.html", t=404,message=f"No such User: '@{username}'")

@route("/settings")
@get_user
@login_required
def settings(user):
    return template("settings.html", user=user)

@route("/settings", method="POST")
@get_user
@login_required
def settings_post(user: User):
    print(vars(request.forms))
    user.settings = json.dumps({
        "censor_profanity":request.forms.censor_prf or ("censor_prf" in vars(request.forms)),
        "embed_links":request.forms.render_links or ("render_links" in vars(request.forms)),
        })
    print(user.settings)
    user.display_name = request.forms.display_name
    user.save()
    return settings()



@route("/login")
def login_route():
    return template("login.html")
 
@route("/postlogin", method="POST")
def login_route_post():
    username = request.forms.username
    password = request.forms.password

    try:
        user_login = User.get(name=username, password=User._hash_password(password))
    except User.DoesNotExist:
        user_login = None

    if user_login:
        token: Token = user_login.generate_token()
        response.set_cookie("token", token.id, expires=token.expires)
        return redirect("/")

    return template("login.html", message="Login or Password incorrect")

def post_message(user, reply_to=None):
    if request.forms.post_text:
        message = (request.forms.post_text)
        return Msg.create(user=user, message=message, reply_to = reply_to)
    return -1

if __name__  == "__main__":
    run(port=8080)