from flask import Flask, render_template, url_for, redirect, flash
from flask_sqlalchemy import SQLAlchemy
from forms import TaskEntry, RegisterForm, LoginForm, MessageForm
from flask_bootstrap import Bootstrap5
from flask_login import UserMixin, login_user, LoginManager, current_user, logout_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.orm import relationship
from flask_ckeditor import CKEditor
import os

# TODO secure sensitive information
ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL")
ADMIN_PASS = os.environ.get("ADMIN_PASS")

app = Flask(__name__)
# modal = Modal(app)
app.config['SECRET_KEY'] = os.environ.get("FLASK_KEY")

app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DB_URI", "sqlite:///tasks.db")

db = SQLAlchemy()
db.init_app(app)
Bootstrap5(app)
ckeditor = CKEditor(app)

login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)


class Task(db.Model):
    __tablename__ = "tasks"
    id = db.Column(db.Integer, primary_key=True)
    entry = db.Column(db.String(250), nullable=False)
    due_date = db.Column(db.Date, nullable=True)
    active = db.Column(db.Boolean, nullable=False, default=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user_accounts.id"))
    user = relationship("User", back_populates="tasks")

    def to_dict(self):
        return {column.name: getattr(self, column.name) for column in self.__table__.columns}

    def change_status(self):
        self.active = False
        db.session.commit()


class User(UserMixin, db.Model):
    __tablename__ = "user_accounts"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(250), nullable=False)
    email = db.Column(db.String(250), unique=True, nullable=False)
    password = db.Column(db.String(250), nullable=False)
    tasks = relationship("Task", back_populates="user")


# class Tasklist(db.Model):
#     __tablename__ = "task_lists"
#     id = db.Column(db.Integer, primary_key=True)
#     title = db.Column(db.String(250), nullable=False)
#     user_id = db.Column(db.Integer, db.ForeignKey("user_accounts.id"))
#     user = relationship("User", back_populates="lists")
#     tasks = relationship("Task", back_populates="task_list")


with app.app_context():
    db.create_all()


@app.route('/', methods=["GET", "POST"])
def home():
    task_list = []
    admin = db.session.execute(db.select(User).where(User.email == ADMIN_EMAIL)).scalar()
    if admin:
        result = db.session.execute(db.select(Task).where(Task.user_id == admin.id))
        all_tasks = result.scalars()
        task_list = [task.to_dict() for task in all_tasks]
    else:
        admin_pass = generate_password_hash(
            password=ADMIN_PASS,
            method="pbkdf2:sha256",
            salt_length=8)
        admin = User(name="admin", email=ADMIN_EMAIL, password=admin_pass)
        db.session.add(admin)
        db.session.commit()

    # registration form
    r_form = RegisterForm()
    l_form = LoginForm()

    # new tasks
    task_form = TaskEntry()
    if task_form.validate_on_submit():
        new_task = Task(
            entry=task_form.entry.data,
            due_date=task_form.due_date.data,
            user_id=admin.id
        )
        db.session.add(new_task)
        db.session.commit()
        return redirect(url_for('home'))
    return render_template('index.html', form=task_form, tasks=task_list, r_form=r_form, login_form=l_form)


@app.route('/completed/<task_id>')
def complete_task(task_id):
    completed_task = db.session.execute(db.select(Task).where(Task.id == task_id)).scalar()
    completed_task.change_status()
    return redirect(url_for('home'))


@app.route('/completed/<user_id>/<task_id>')
def complete_user_task(user_id, task_id):
    completed_task = db.session.execute(db.select(Task).where(Task.id == task_id)).scalar()
    completed_task.change_status()
    return redirect(url_for('user_home', userid=user_id))


@app.route('/register', methods=["POST", "GET"])
def register():
    admin = db.session.execute(db.select(User).where(User.email == ADMIN_EMAIL)).scalar()
    result = db.session.execute(db.select(Task).where(Task.user_id == admin.id))
    # order_by(Task.due_date))
    all_tasks = result.scalars()
    task_list = [task.to_dict() for task in all_tasks]
    task_form = TaskEntry()
    l_form = LoginForm()
    # registration
    r_form = RegisterForm()
    if r_form.validate_on_submit():
        name = r_form.name.data
        email = r_form.email.data
        hashed_password = generate_password_hash(
            password=r_form.password.data,
            method="pbkdf2:sha256",
            salt_length=8)
        new_user = User(name=name, email=email, password=hashed_password)
        existing_user = db.session.execute(db.select(User).where(User.email == email)).scalar()
        if existing_user:
            flash("That account already exists. Please login instead.")
            return redirect(url_for('login'))
        else:
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user)
            return redirect(url_for('user_home', userid=new_user.id))
    return render_template('index.html', form=task_form, tasks=task_list, r_form=r_form, login_form=l_form)


@app.route('/login', methods=["POST", "GET"])
def login():
    admin = db.session.execute(db.select(User).where(User.email == ADMIN_EMAIL)).scalar()
    result = db.session.execute(db.select(Task).where(Task.user_id == admin.id))
    # order_by(Task.due_date))
    all_tasks = result.scalars()
    task_list = [task.to_dict() for task in all_tasks]

    task_form = TaskEntry()
    # registration
    r_form = RegisterForm()
    # login
    l_form = LoginForm()
    if l_form.validate_on_submit():
        email = l_form.email.data
        password = l_form.password.data
        user_account = db.session.execute(db.select(User).where(User.email == email)).scalar()
        if user_account:
            hashed_password = user_account.password
            if check_password_hash(pwhash=hashed_password, password=password):
                login_user(user_account)
                return redirect(url_for('user_home', userid=user_account.id))
            else:
                flash("The password is incorrect. Please try again.")
                return redirect(url_for('login'))
        else:
            flash("This account doesn't exist, please register.")
            return redirect(url_for('register'))
    return render_template('index.html', form=task_form, tasks=task_list, r_form=r_form, login_form=l_form)


@login_required
@app.route('/<userid>', methods=["POST", "GET"])
def user_home(userid):
    user = db.session.execute(db.select(User).where(User.id == userid)).scalar()
    result = db.session.execute(db.select(Task).where(Task.user_id == user.id))
    # order_by(Task.due_date))
    all_tasks = result.scalars()
    task_list = [task.to_dict() for task in all_tasks]

    # new tasks
    task_form = TaskEntry()
    if task_form.validate_on_submit():
        new_task = Task(
            entry=task_form.entry.data,
            due_date=task_form.due_date.data,
            user_id=user.id
        )
        db.session.add(new_task)
        db.session.commit()
        return redirect(url_for('user_home', userid=userid))
    return render_template("user.html", tasks=task_list, form=task_form, user=user)


@app.route('/delete')
def delete_samples():
    admin = db.session.execute(db.select(User).where(User.email == ADMIN_EMAIL)).scalar()
    result = db.session.execute(db.select(Task).where(Task.user_id == admin.id))
    delete_list = result.scalars()
    for entry in delete_list:
        db.session.delete(entry)
        db.session.commit()
    return redirect(url_for('home'))


@app.route('/logout')
def logout():
    admin = db.session.execute(db.select(User).where(User.email == ADMIN_EMAIL)).scalar()
    result = db.session.execute(db.select(Task).where(Task.user_id == admin.id))
    delete_list = result.scalars()
    for entry in delete_list:
        db.session.delete(entry)
        db.session.commit()
    logout_user()
    return redirect(url_for('home'))


@app.route("/about", methods=["POST","GET"])
def about():
    r_form = RegisterForm()
    l_form = LoginForm()
    message_form = MessageForm()
    if message_form.validate_on_submit():
        name = message_form.name.data
        email = message_form.email.data
        message = message_form.message.data
        flash("Thank you! Message has been sent.")
        return redirect(url_for('about'))
    return render_template("about.html", m_form=message_form, r_form=r_form, login_form=l_form)


if __name__ == "__main__":
    app.run(debug=True)
