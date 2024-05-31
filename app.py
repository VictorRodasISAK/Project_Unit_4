from flask import Flask, render_template, redirect, url_for, request, flash
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from datetime import datetime
import os
from helpers import get_user_by_id, get_posts_by_user_id, get_comments_by_post_id, get_followed_users, transform_post_data, db_worker

# Initialize Flask application
app = Flask(__name__)
app.config['SECRET_KEY'] = 'reddit-1234'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////Users/m19-056/PycharmProjects/pythonProject1/Reddit_Project_CS/database.db'
app.config['UPLOAD_FOLDER'] = 'static/images'

# Initialize database and login manager
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.init_app(app)

# User class for authentication
class User(UserMixin):
    def __init__(self, id, username, email, password_hash):
        self.id = id
        self.username = username
        self.email = email
        self.password_hash = password_hash

    @property
    def is_active(self):
        return True

# Check if the uploaded file is allowed
def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Home route - display posts from followed users
@app.route('/')
@login_required
def home():
    followed_user_ids = [str(user['id']) for user in get_followed_users(current_user.id)]
    if not followed_user_ids:
        posts = []
    else:
        followed_user_ids_str = ','.join(followed_user_ids)
        posts_data = db_worker.search(f"""
            SELECT posts.*, 
                   (SELECT COUNT(*) FROM likes WHERE likes.post_id = posts.id) AS like_count
            FROM posts 
            WHERE user_id IN ({followed_user_ids_str}) 
            ORDER BY created_at DESC
        """, multiple=True)

        posts = []
        for post_data in posts_data:
            post = transform_post_data(post_data)
            post['user'] = get_user_by_id(post['user_id'])
            post['comments'] = get_comments_by_post_id(post['id'])
            posts.append(post)

    return render_template('home.html', posts=posts)

# Profile route - display user profile and posts
@app.route('/profile/<int:user_id>', methods=['GET', 'POST'])
@login_required
def profile(user_id):
    user = get_user_by_id(user_id)
    if not user:
        flash('No user found with that id.', 'danger')
        return redirect(url_for('home'))

    posts = get_posts_by_user_id(user_id)
    post_count = len(posts)
    like_count = sum(post['like_count'] for post in posts)
    follower_count = len(get_followed_users(user_id))
    follows = get_followed_users(user_id)

    return render_template('profile.html', user=user, posts=posts, post_count=post_count, like_count=like_count, follower_count=follower_count, follows=follows)

# Subreddit route - display posts by topic
@app.route('/r/<name>')
@login_required
def subreddit(name):
    topic_name = name.upper()
    posts_data = db_worker.search(f"""
        SELECT posts.*, 
               (SELECT COUNT(*) FROM likes WHERE likes.post_id = posts.id) AS like_count
        FROM posts 
        WHERE topic = '{topic_name}'
    """, multiple=True)

    posts = []
    for post_data in posts_data:
        post = transform_post_data(post_data)
        post['user'] = get_user_by_id(post['user_id'])
        post['comments'] = get_comments_by_post_id(post['id'])
        posts.append(post)

    return render_template('subreddit.html', posts=posts, subreddit=name)

# View post route - display a single post and its comments
@app.route('/view_post/<int:post_id>', methods=['GET'])
@login_required
def view_post(post_id):
    post_data = db_worker.search(f"""
        SELECT posts.*, 
               (SELECT COUNT(*) FROM likes WHERE likes.post_id = posts.id) AS like_count
        FROM posts 
        WHERE id = {post_id}
    """)
    if not post_data:
        flash('No post found with that id.', 'danger')
        return redirect(url_for('home'))

    post = transform_post_data(post_data)
    post['user'] = get_user_by_id(post['user_id'])
    post['comments'] = get_comments_by_post_id(post['id'])

    return render_template('view_post.html', post=post)

# Load user for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    user_data = db_worker.search(f"SELECT * FROM users WHERE id = {user_id}")
    if user_data:
        return User(*user_data[:4])
    return None

# Register route - create a new user
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        bio = request.form.get('bio')
        profile_picture = request.files.get('profile_picture')

        user = db_worker.search(f"SELECT * FROM users WHERE username = '{username}' OR email = '{email}'")
        if user:
            flash('Username or email already exists. Please choose a different one.', 'danger')
            return redirect(url_for('register'))

        hashed_password = db_worker.make_hash(password)

        if profile_picture and allowed_file(profile_picture.filename):
            filename = secure_filename(profile_picture.filename)
            profile_picture_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            profile_picture.save(profile_picture_path)
            profile_picture_url = f'static/images/{filename}'
        else:
            profile_picture_url = None

        db_worker.insert(f"""
            INSERT INTO users (username, email, password_hash, bio, profile_picture) 
            VALUES ('{username}', '{email}', '{hashed_password}', '{bio}', '{profile_picture_url}')
        """)

        flash('Your account has been created! You can now log in.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')

# Login route - authenticate and login user
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user_data = db_worker.search(f"SELECT * FROM users WHERE username = '{username}'")
        if not user_data:
            flash('No account found with that username. Please register first.', 'danger')
            return redirect(url_for('login'))

        if not db_worker.check_hash(password, user_data[3]):
            flash('Password is incorrect. Please try again.', 'danger')
            return redirect(url_for('login'))

        user = User(*user_data[:4])
        login_user(user)
        flash('You have been logged in!', 'success')
        return redirect(url_for('home'))

    return render_template('login.html')

# Logout route - log out the current user
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out!', 'success')
    return redirect(url_for('login'))

# Create post route - create a new post
@app.route('/create_post', methods=['GET', 'POST'])
@login_required
def create_post():
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        topic = request.form.get('topic')
        image = request.files.get('image')

        if image:
            filename = secure_filename(image.filename)
            image_path = os.path.join('static/images', filename)
            image.save(image_path)
        else:
            image_path = None

        db_worker.insert(f"INSERT INTO posts (user_id, title, content, image_url, topic) VALUES ({current_user.id}, '{title}', '{content}', '{image_path}', '{topic}')")

        flash('Your post has been created!', 'success')
        return redirect(url_for('home'))

    return render_template('create_post.html')

# Edit post route - edit an existing post
@app.route('/edit_post/<int:post_id>', methods=['GET', 'POST'])
@login_required
def edit_post(post_id):
    post_data = db_worker.search(f"""
        SELECT posts.*, 
               (SELECT COUNT(*) FROM likes WHERE likes.post_id = posts.id) AS like_count
        FROM posts 
        WHERE id = {post_id}
    """)
    if not post_data:
        flash('No post found with that id.', 'danger')
        return redirect(url_for('home'))

    post = transform_post_data(post_data)

    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        topic = request.form.get('topic')
        image = request.files.get('image')

        if image:
            filename = secure_filename(image.filename)
            image_path = os.path.join('static/images', filename)
            image.save(image_path)
        else:
            image_path = post['image_url']

        updated_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        db_worker.run_query(f"""
            UPDATE posts 
            SET title = '{title}', content = '{content}', image_url = '{image_path}', topic = '{topic}', updated_at = '{updated_at}'
            WHERE id = {post_id}
        """)

        flash('Your post has been updated!', 'success')
        return redirect(url_for('home'))

    return render_template('edit_post.html', post=post)

# Delete post route - delete an existing post
@app.route('/delete_post/<int:post_id>', methods=['GET', 'POST'])
@login_required
def delete_post(post_id):
    post_data = db_worker.search(f"SELECT * FROM posts WHERE id = {post_id}")
    if not post_data:
        flash('No post found with that id.', 'danger')
        return redirect(url_for('home'))

    if post_data[1] != current_user.id:
        flash('You are not authorized to delete this post.', 'danger')
        return redirect(url_for('home'))

    if request.method == 'POST':
        db_worker.run_query(f"DELETE FROM posts WHERE id = {post_id}")

        flash('Your post has been deleted!', 'success')
        return redirect(url_for('home'))

    return render_template('delete_post.html', post=post_data)

# Like post route - like a post
@app.route('/like_post/<int:post_id>', methods=['POST'])
@login_required
def like_post(post_id):
    like = db_worker.search(f"SELECT * FROM likes WHERE user_id = {current_user.id} AND post_id = {post_id}")
    if like:
        flash('You have already liked this post.', 'info')
        return redirect(url_for('home'))

    db_worker.insert(f"INSERT INTO likes (user_id, post_id) VALUES ({current_user.id}, {post_id})")

    flash('You have liked the post!', 'success')
    return redirect(url_for('home'))

# Unlike post route - unlike a post
@app.route('/unlike_post/<int:post_id>', methods=['POST'])
@login_required
def unlike_post(post_id):
    like = db_worker.search(f"SELECT * FROM likes WHERE user_id = {current_user.id} AND post_id = {post_id}")
    if not like:
        flash('You have not liked this post.', 'info')
        return redirect(url_for('home'))

    db_worker.run_query(f"DELETE FROM likes WHERE user_id = {current_user.id} AND post_id = {post_id}")

    flash('You have unliked the post!', 'success')
    return redirect(url_for('home'))

# Follow user route - follow another user
@app.route('/follow_user/<int:user_id>', methods=['POST'])
@login_required
def follow_user(user_id):
    if current_user.id == user_id:
        flash('You cannot follow yourself.', 'info')
        return redirect(url_for('home'))

    follow = db_worker.search(f"SELECT * FROM follows WHERE follower_id = {current_user.id} AND followed_user_id = {user_id}")
    if follow:
        flash('You are already following this user.', 'info')
        return redirect(url_for('home'))

    db_worker.insert(f"INSERT INTO follows (follower_id, followed_user_id) VALUES ({current_user.id}, {user_id})")

    flash('You are now following the user!', 'success')
    return redirect(url_for('home'))

# Unfollow user route - unfollow another user
@app.route('/unfollow_user/<int:user_id>', methods=['POST'])
@login_required
def unfollow_user(user_id):
    if current_user.id == user_id:
        flash('You cannot unfollow yourself.', 'info')
        return redirect(url_for('home'))

    follow = db_worker.search(f"SELECT * FROM follows WHERE follower_id = {current_user.id} AND followed_user_id = {user_id}")
    if not follow:
        flash('You are not following this user.', 'info')
        return redirect(url_for('home'))

    db_worker.run_query(f"DELETE FROM follows WHERE follower_id = {current_user.id} AND followed_user_id = {user_id}")

    flash('You have unfollowed the user!', 'success')
    return redirect(url_for('home'))

# Upload image route - upload a profile picture
@app.route('/upload_image', methods=['POST'])
@login_required
def upload_image():
    if 'file' not in request.files:
        flash('No file part', 'info')
        return redirect(request.url)
    file = request.files['file']

    if file.filename == '':
        flash('No selected file', 'info')
        return redirect(request.url)

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        file_url = f'static/images/{filename}'

        db_worker.run_query(f"""
            UPDATE users 
            SET profile_picture = '{file_url}' 
            WHERE id = {current_user.id}
        """)

        flash('Your profile picture has been updated!', 'success')
        return redirect(url_for('profile', user_id=current_user.id))

# Add comment route - add a comment to a post
@app.route('/add_comment/<int:post_id>', methods=['POST'])
@login_required
def add_comment(post_id):
    content = request.form.get('content')
    if not content:
        flash('Comment cannot be empty', 'danger')
        return redirect(url_for('view_post', post_id=post_id))

    db_worker.run_query(f"""
        INSERT INTO comments (post_id, user_id, content, created_at)
        VALUES ({post_id}, {current_user.id}, '{content}', '{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}')
    """)

    flash('Your comment has been added!', 'success')
    return redirect(url_for('view_post', post_id=post_id))

# Edit comment route - edit an existing comment
@app.route('/edit_comment/<int:comment_id>', methods=['GET', 'POST'])
@login_required
def edit_comment(comment_id):
    comment_data = db_worker.search(f"SELECT * FROM comments WHERE id = {comment_id}")
    if not comment_data:
        flash('No comment found with that id.', 'danger')
        return redirect(url_for('home'))

    if comment_data[2] != current_user.id:
        flash('You are not authorized to edit this comment.', 'danger')
        return redirect(url_for('home'))

    if request.method == 'POST':
        content = request.form.get('content')
        updated_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        db_worker.run_query(f"UPDATE comments SET content = '{content}', updated_at = '{updated_at}' WHERE id = {comment_id}")
        flash('Your comment has been updated!', 'success')
        return redirect(url_for('view_post', post_id=comment_data[1]))

    return render_template('edit_comment.html', comment=comment_data)

# Delete comment route - delete an existing comment
@app.route('/delete_comment/<int:comment_id>', methods=['POST'])
@login_required
def delete_comment(comment_id):
    comment_data = db_worker.search(f"SELECT * FROM comments WHERE id = {comment_id}")
    if not comment_data:
        flash('No comment found with that id.', 'danger')
        return redirect(url_for('home'))

    if comment_data[2] != current_user.id:
        flash('You are not authorized to delete this comment.', 'danger')
        return redirect(url_for('home'))

    db_worker.run_query(f"DELETE FROM comments WHERE id = {comment_id}")
    flash('Your comment has been deleted!', 'success')
    return redirect(url_for('view_post', post_id=comment_data[1]))

# Run the application
if __name__ == '__main__':
    app.run(debug=True)
