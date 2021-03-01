import os
import secrets
import urllib
from PIL import Image
from flask import render_template, url_for, flash, redirect, request, abort, jsonify, session
from website.forms import RegistrationForm, LoginForm, AccountUpdateForm, RequestResetForm, ResetPasswordForm, SuggestionForm, PostForm, HelpForm, QuestionForm, AnswerForm
from website import app, db, bcrypt, mail, oauth, google
from website.models import User, Post, Feedback, Question, Answer
from flask_login import login_user, current_user, logout_user, login_required
from flask_mail import Message
from requests import get
from flask_msearch import Search
search = Search()
search.init_app(app)


@app.route("/")
@app.route("/home")
def home():
    return render_template('home.html', title='Home Page')


@app.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(name=form.username.data, email=form.email.data, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash(
            f"Your account has been successfully been created for {form.username.data}. Now you can LogIN!!!", 'success')
        return redirect(url_for('login'))
    return render_template('register.html', form=form, title="User Registration")


@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            if next_page:
                print(next_page)
                list1 = next_page.split("/")
                print(list1)
                return redirect(url_for(list1[1]))
            flash("You have been logged in successfully", 'success')
            return redirect(url_for('home'))
        else:
            flash("You cannot be logged in!!!!", "danger")
    return render_template('login.html', form=form, title='Login Page')


@app.route("/google")
def google_login():
    google = oauth.create_client('google')
    redirect_uri = url_for('authorize', _external=True)
    return google.authorize_redirect(redirect_uri)


@app.route('/authorize')
def authorize():
    google = oauth.create_client('google')
    token = google.authorize_access_token()
    resp = google.get('userinfo')
    userinfo = resp.json()
    print(userinfo)
    session['email'] = userinfo['email']
    # do something with the token and profile
    user = User.query.filter_by(email=userinfo['email']).first()
    if user:
        login_user(user)
        next_page = request.args.get('next')
        if next_page:
            print(next_page)
            list1 = next_page.split("/")
            print(list1)
            return redirect(url_for(list1[1]))
        flash("You have been logged in successfully", 'success')
        return redirect(url_for('home'))
    else:
        user = User(name=userinfo['name'], email=userinfo['email'], password=secrets.token_hex(16))
        db.session.add(user)
        db.session.commit()
        login_user(user)
        next_page = request.args.get('next')
        if next_page:
            print(next_page)
            list1 = next_page.split("/")
            print(list1)
            return redirect(url_for(list1[1]))
        flash("You have been logged in successfully", 'success')
        return redirect(url_for('home'))


@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out successfully!!!!", "success")
    return redirect(url_for('home'))


def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(app.root_path, 'static/profile_pics', picture_fn)
    output_size = (125, 125)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)
    return picture_fn


@app.route("/account", methods=['GET', 'POST'])
@login_required
def account():
    image_file = url_for('static', filename='profile_pics/'+current_user.image_file)
    form = AccountUpdateForm()
    if form.validate_on_submit():
        if form.picture.data:
            picture_file = save_picture(form.picture.data)
            current_user.image_file = picture_file
        current_user.name = form.username.data
        current_user.email = form.email.data
        db.session.commit()
        flash("Your account has been updated successfully!!!", 'success')
        return redirect(url_for('account'))
    elif request.method == 'GET':
        form.username.data = current_user.name
        form.email.data = current_user.email
    return render_template("account.html", title="Profile Page", image_file=image_file, form=form)


def send_reset_email(user):
    token = user.get_reset_token()
    msg = Message("Password Reset Email", sender="noreply@demo.com", recipients=[user.email])
    msg.body = f'''
        To reset your password visit the following link.
        {url_for('reset_token',token=token,_external=True)}
        If you did not make the change request please ignore it.
        Nothing will be changed!!!
    '''
    mail.send(msg)


@app.route("/reset_password", methods=['GET', 'POST'])
def reset_request():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    form = RequestResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        send_reset_email(user)
        flash('An email has been sent with the instructions to reset password!', 'info')
        return redirect(url_for('login'))
    return render_template('reset_request.html', title='Reset Password', form=form)


@app.route("/reset_password/<token>", methods=['GET', 'POST'])
def reset_token(token):
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    user = User.verified_reset_token(token)
    if user is None:
        flash("The token is invalid or expired", "warning")
        return redirect(url_for('reset_request'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user.password = hashed_password
        db.session.commit()
        flash(f"Your password has been changed! Now You will be able to login!!! ", "success")
        return redirect(url_for('login'))
    return render_template('reset_token.html', title='Reset Password', form=form)


def send_suggestion_email(user, form):
    msg = Message(form.title.data, sender=user.email, recipients=['vedantjolly2001@gmail.com'])
    msg.body = f'The suggestion by the user is that {form.content.data}'
    mail.send(msg)


@app.route("/suggestions", methods=['GET', 'POST'])
@login_required
def suggestions():
    form = SuggestionForm()
    if form.validate_on_submit():
        send_suggestion_email(current_user, form)
        flash('Thank you for your valuable feedback !!! We will surely try to improve', 'info')
        return redirect(url_for('home'))
    return render_template('suggestion.html', title='Suggestion Page', form=form)


@app.route("/detect")
@login_required
def detect_posture():
    return render_template('index.html')


@app.route("/post/new", methods=['GET', 'POST'])
@login_required
def new_post():
    form = PostForm()
    if form.validate_on_submit():
        if form.picture.data:
            picture_file = save_picture(form.picture.data)
            print(picture_file)
            post = Post(title=form.title.data, content=form.content.data,
                        author=current_user, image_file=picture_file)
            db.session.add(post)
            db.session.commit()
        else:
            print("yess")
            post = Post(title=form.title.data, content=form.content.data, author=current_user)
            db.session.add(post)
            db.session.commit()
        flash("Your post has been successfully created!!!", 'success')
        return redirect(url_for('all_posts'))
    return render_template('create_post.html', title='New Post', form=form, legend="New Post")


@app.route("/post/<int:post_id>")
def post(post_id):
    post = Post.query.get_or_404(post_id)
    return render_template('post.html', title=post.title, post=post)


@app.route("/post/<int:post_id>/update", methods=['GET', 'POST'])
@login_required
def update_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)
    form = PostForm()
    if form.validate_on_submit():
        post.title = form.title.data
        post.content = form.content.data
        db.session.commit()
        flash("Your post has been updated!!", 'success')
        return redirect(url_for('post', post_id=post.id))
    if request.method == "GET":
        form.title.data = post.title
        form.content.data = post.content
    return render_template('create_post.html', title='Update Post', form=form, legend="Update Post")


@app.route("/post/<int:post_id>/delete", methods=['POST'])
@login_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)
    db.session.delete(post)
    db.session.commit()
    flash("Your post has been deleted", "success")
    return redirect(url_for("all_posts"))


@app.route("/posts")
@login_required
def all_posts():
    page = request.args.get('page', 1, type=int)
    posts = Post.query.order_by(Post.date_posted.desc()).paginate(page=page, per_page=2)
    return render_template('allPosts.html', posts=posts)


@app.route("/user/<string:username>")
def user_posts(username):
    page = request.args.get('page', 1, type=int)
    user = User.query.filter_by(name=username).first_or_404()
    posts = Post.query.filter_by(author=user).order_by(
        Post.date_posted.desc()).paginate(page=page, per_page=2)
    return render_template('user_posts.html', posts=posts, user=user)


@app.route("/question/new", methods=['GET', 'POST'])
@login_required
def new_question():
    form = QuestionForm()
    if form.validate_on_submit():
        print("yess")
        question = Question(title=form.title.data, content=form.content.data, author=current_user)
        db.session.add(question)
        db.session.commit()
        flash("Your question has been successfully created!!!", 'success')
        return redirect(url_for('all_questions'))
    return render_template('create_question.html', title='New Question', form=form, legend="New Question")


@app.route("/question/<int:question_id>")
def question(question_id):
    question = Question.query.get_or_404(question_id)
    return render_template('question.html', title=question.title, post=question)


@app.route("/question/<int:question_id>/update", methods=['GET', 'POST'])
@login_required
def update_question(question_id):
    question = Question.query.get_or_404(question_id)
    if question.author != current_user:
        abort(403)
    form = QuestionForm()
    if form.validate_on_submit():
        question.title = form.title.data
        question.content = form.content.data
        db.session.commit()
        flash("Your question has been updated!!", 'success')
        return redirect(url_for('question', question_id=question.id))
    if request.method == "GET":
        form.title.data = question.title
        form.content.data = question.content
    return render_template('create_question.html', title='Update Question', form=form, legend="Update Question")


@app.route("/question/<int:question_id>/delete", methods=['POST'])
@login_required
def delete_question(question_id):
    question = Question.query.get_or_404(question_id)
    if question.author != current_user:
        abort(403)
    db.session.delete(question)
    db.session.commit()
    flash("Your question has been deleted", "success")
    return redirect(url_for("all_questions"))


@app.route("/questions")
@login_required
def all_questions():
    page = request.args.get('page', 1, type=int)
    questions = Question.query.order_by(Question.date_posted.desc()).paginate(page=page, per_page=5)
    return render_template('allQuestions.html', posts=questions)


@app.route("/user/questions/<string:username>")
def user_questions(username):
    page = request.args.get('page', 1, type=int)
    user = User.query.filter_by(name=username).first_or_404()
    questions = Question.query.filter_by(author=user).order_by(
        Question.date_posted.desc()).paginate(page=page, per_page=5)
    return render_template('user_questions.html', posts=questions, user=user)


@app.route("/search")
def w_search():
    keyword = request.args.get('inputEmail4')
    # results = Post.query.msearch(keyword, fields=['title'], limit=20).filter(...)
    # # or
    # results = Post.query.filter(...).msearch(keyword, fields=['title'], limit=20).filter(...)
    # # elasticsearch
    # keyword = "title:book AND content:read"
    # # more syntax please visit https://www.elastic.co/guide/en/elasticsearch/reference/current/query-dsl-query-string-query.html
    page = request.args.get('page', 1, type=int)
    results = Question.query.msearch(keyword, limit=20).order_by(
        Question.date_posted.desc()).paginate(page=page, per_page=5)
    return render_template('allQuestions.html', posts=results)
