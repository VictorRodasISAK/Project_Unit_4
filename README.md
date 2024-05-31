# Developing a Reddit Webpage
# Criteria C: Development
## Existing tools

| Libraries      |
|----------------|
| Flask          |
| SQLAlchemy     |
| werkzeug.utils |
| datetime       |
| os             |
| sqlite 3       |
| passlib.hash   |

## References

- [Flask Documentation](https://flask.palletsprojects.com/en/2.0.x/) To learn how to use Flask
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/en/14/) To learn how to use SQLAlchemy
- [Jinja2 Documentation](https://jinja.palletsprojects.com/en/3.0.x/) To learn how to use Jinja2 and get part of the code that I used in the project
- [Flask-Login Documentation](https://flask-login.readthedocs.io/en/latest/) To learn how to use Flask-Login
- [Flask-WTF Documentation](https://flask-wtf.readthedocs.io/en/stable/) To learn how to use Flask-WTF
- [Werkzeug Documentation](https://werkzeug.palletsprojects.com/en/2.0.x/) To learn how to use Werkzeug
- [Python Documentation](https://docs.python.org/3/) To learn how to use certain functions in Python
- [W3Schools](https://www.w3schools.com/) To learn web development and find easier ways to do certain actions
- [MDN Web Docs](https://developer.mozilla.org/en-US/) To learn web development
- [Real Python](https://realpython.com/) To learn new techniques or refresh my knowledge with different techniques.
- [Corey Schafer's Flask Tutorial](https://www.youtube.com/watch?v=QnDWIZuWYW0) To learn how to use Flask
- [Corey Schafer's Flask Blog Tutorial](https://www.youtube.com/watch?v=3mwFC4SHY-Y) To learn how to use Flask
- [GitHub Copilot](https://copilot.github.com/) To help with code problems that I couldn't understand, and get references or advices on things that I could make better.

*Disclaimer* I didn't use it to write the code, I used it to get some ideas on how to solve some problems.
- [ChatGPT](https://chat.openai.com/) To help with code problems that I couldn't understand, and get references or advices on things that I could make better.

*Disclaimer* I didn't use it to write the code, I used it to get some ideas on how to solve some problems.

## List of techniques used in the code
1) Object-Oriented Programming(OOP)
2) Object Relation Mapping(ORM): SQLAlchemy
3) Flask Library/Routes
4) HTML
5) CSS Styling
6) For loops for showing posts
7) if statements
8) Password Hashing
9) Interacting with Databases
10) Arrays and Lists 
11) Text Formatting


## Development

### Database Operations with SQLAlchemy and Custom Queries
```.py
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
```

From this part of the code, I want to make emphasis on the following:

`followed_user_ids = [str(user['id']) for user in get_followed_users(current_user.id)]` - This line of code is used to get the ids of the users that the current user is following. The `get_followed_users` function is a custom function that returns a list of dictionaries with the user ids and other user information. The `current_user.id` is the id of the current user that is logged in.

Then, if we continue with the code, in the 'if/else' statement, we can see that the `followed_user_ids` are used to get the posts of the users that the current user is following. The `followed_user_ids_str` is a string that contains the ids of the users that the current user is following. This string is used in the SQL query to get the posts of the users that the current user is following.

The SQL Query that I develop is a nested one, which I use to get the like count. The like count is the number of likes that a post has. This is done by counting the number of rows in the `likes` table that have the `post_id` equal to the `id` of the post. This is done in the following line of code:
`(SELECT COUNT(*) FROM likes WHERE likes.post_id = posts.id) AS like_count`

Finally, the posts are transformed into a list of dictionaries that contain the post information, the user information, and the comments of the post. This will display the posts in the home page of the user.


### User authentication and authorization with Flask-Login
```.py
@login_manager.user_loader
def load_user(user_id):
    user_data = db_worker.search(f"SELECT * FROM users WHERE id = {user_id}")
    if user_data:
        return User(*user_data[:4])
    return None

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
```

From this part of the code, I want to make emphasis on the following:

`@login_manager.user_loader` - This is a decorator that is used to load the user from the database. This function is used to get the user data from the database and create a User object with the user data. This function is used by Flask-Login to get the user data from the database.
Because of the design of my database, I only get the first 4 columns of the user data. This is because the User object only has 4 attributes: id, username, email, and password.


In the `login` function, I get the username and password from the form that the user submits. Then, I get the user data from the database using the username. If the user data is not found, I flash a message that says that there is no account found with that username. If the password is incorrect, I flash a message that says that the password is incorrect. If the username and password are correct, I create a User object with the user data and log in the user using the `login_user` function. Finally, I flash a message that says that the user has been logged in and redirect the user to the home page.


Besides that, I have the `db_worker.check_hash` function that is used to check if the password that the user submits is correct. This function is used to check if the password that the user submits is the same as the password that is stored in the database. This is done by hashing the password that the user submits and comparing it with the hashed password that is stored in the database.


### File Upload Security
```.py
def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

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
        file_url = f'images/{filename}'

        db_worker.run_query(f"""
            UPDATE users 
            SET profile_picture = '{file_url}' 
            WHERE id = {current_user.id}
        """)

        flash('Your profile picture has been updated!', 'success')
        return redirect(url_for('profile', user_id=current_user.id))
```

From this part of the code, I want to make emphasis on the following:

I try to filter the files that the user uploads to make sure that they are safe. Using `secure_filename` avoiding directory transversal attacks and other security issues.

`def allowed_file(filename)` - This function is used to check if the file that the user uploads is allowed. The allowed file extensions are 'png', 'jpg', 'jpeg', and 'gif'. This function is used to check if the file extension of the file that the user uploads is in the allowed file extensions. This is done by splitting the filename and getting the file extension. Then, the file extension is checked if it is in the allowed file extensions.

In the `upload_image` function, I check if the file is in the request files. If the file is not in the request files, I flash a message that says that there is no file part. If the file is in the request files, I check if the filename is empty. If the filename is empty, I flash a message that says that there is no selected file. If the file is not empty and the file is allowed, I save the file in the upload folder and update the profile picture of the user in the database. Finally, I flash a message that says that the profile picture has been updated and redirect the user to the profile page.


### Handling User Relationships and Interactions
```.py
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
```

From this part of the code, I want to make emphasis on the following:

Here I manage that control of following/unfollowing users, this involves a logic that is explained below.

In the `follow_user` function, I check if the current user is trying to follow themselves. If the current user is trying to follow themselves, I flash a message that says that the user cannot follow themselves. If the current user is not trying to follow themselves, I check if the current user is already following the user that they are trying to follow. If the current user is already following the user that they are trying to follow, I flash a message that says that the user is already following this user. If the current user is not already following the user that they are trying to follow, I insert a new row in the `follows` table with the `follower_id` and `followed_user_id` of the current user and the user that they are trying to follow. Finally, I flash a message that says that the user is now following the user and redirect the user to the home page.

Moreover, I decided to implement the following logic in the database, so I have a table called `follows` that has the `follower_id` and `followed_user_id` columns. This table is used to store the relationships between the users. When a user follows another user, a new row is inserted in the `follows` table with the `follower_id` and `followed_user_id` of the users. When a user unfollows another user, the row is deleted from the `follows` table. This is done to keep track of the relationships between the users. So then is easier to display the information that every user has, including posts.


### Comment Management and Hierarchical Data
```.py
def get_comments_by_post_id(post_id):
    comments_data = db_worker.search(f"SELECT * FROM comments WHERE post_id = {post_id}", multiple=True)
    comments = []
    for comment_data in comments_data:
        comment = {
            'id': comment_data[0],
            'post_id': comment_data[1],
            'user_id': comment_data[2],
            'content': comment_data[3],
            'created_at': comment_data[4],
            'updated_at': comment_data[5]
        }
        comment['user'] = get_user_by_id(comment['user_id'])
        comments.append(comment)
    return comments
```

These codes are in the `helpers.py` file. This file contains the functions that will get all the information from the database, making it easier for me to get the data from the database. Besides that, it helps to decrease the lines of code in the main file, because I needed to get the information independently, leading to a more unorganized code.

From this part of the code, I want to make emphasis on the following:

e.g. `get_comments_by_post_id` - This function is used to get the comments of a post by the post id. This function is used to get the comments of a post from the database. The comments are stored in the `comments` table in the database. The comments are stored with the `post_id` of the post that they belong to. This function is used to get the comments of a post by the `post_id`. The comments are transformed into a list of dictionaries that contain the comment information and the user information. This will display the comments of the post in the post page.

The same happens with the other functions that I develop on that file. I put the information that I need in a dictionary, so is easier to handle the information. 

The only one that changes a little bit is with `transform_post_data` function, because I put another column that is not in the database, exactly this one `'like_count': post_data[8] if len(post_data) > 8 else 0`. As the name says, it gets the like count of the post, but if the post doesn't have likes, it will return 0. This is because I use this function to transform the post data and display it in the home page of the user.

### Dynamic Content Rendering with Jinja2

```.html
{% for post in posts %}
    <div class="card mb-3">
        <div class="card-header">
            <div class="d-flex justify-content-between">
                <div>
                    <img src="{{ url_for('static', filename=post.user.profile_picture) }}" class="rounded-circle" width="40" height="40">
                    <span class="ml-2">{{ post.user.username }}</span>
                </div>
                <div>
                    <small>{{ post.created_at.strftime('%Y-%m-%d %H:%M:%S') }}</small>
                </div>
            </div>
        </div>
        <div class="card-body">
            <p class="card-text">{{ post.content }}</p>
            <img src="{{ url_for('static', filename=post.image) }}" class="img-fluid" alt="Post Image">
        </div>
        <div class="card-footer">
            <div class="d-flex justify-content-between">
                <div>
                    <a href="{{ url_for('post', post_id=post.id) }}" class="card-link">View Post</a>
                    <a href="{{ url_for('profile', user_id=post.user.id) }}" class="card-link">View Profile</a>
                </div>
                <div>
                    <small>{{ post.like_count }} likes</small>
                    <small>{{ post.comments|length }} comments</small>
                </div>
            </div>
        </div>
    </div>
{% endfor %}
```

The function of this is render a dynamic list of posts in the home page of the user. This is done by using a for loop in the Jinja2 template. The posts are displayed in a card format with the user profile picture, username, created at date, content, image, view post link, view profile link, like count, and comment count. This is done by using the post data that is passed to the template from the view function. The post data is a list of dictionaries that contain the post information, the user information, and the comments of the post. This will display the posts in the home page of the user.
During this part is essential to be careful when combining loops and conditionals to render complex data. This could lead to some problems if not done correctly.

### Form Handling and Validation
```.html
<div class="form-container">
    <form method="post" action="{{ url_for('create_post') }}" enctype="multipart/form-data">
        <label for="title">Title:</label>
        <input type="text" name="title" id="title" required>

        <label for="content">Content:</label>
        <textarea name="content" id="content" required></textarea>

        <label for="image">Upload Image:</label>
        <input type="file" name="image" id="image">

        <label for="topic">Topic:</label>
        <select name="topic" id="topic" required>
            <option value="BADMINTON">BADMINTON</option>
            <option value="CARS">CARS</option>
            <option value="CYBERSECURITY">CYBERSECURITY</option>
        </select>

        <button type="submit">Create Post</button>
    </form>
</div>
```

This is the form that the user uses to create a post. The form contains the title, content, image, and topic fields. The title and content fields are required, so the user has to fill them out. The image field is not required, so the user can choose to upload an image or not. The topic field is a select field with the options 'BADMINTON', 'CARS', and 'CYBERSECURITY'. The user has to select one of the options. This is done by using the required attribute in the input fields. This will validate the form and make sure that the user fills out the required fields.

### Base Template and Template Inheritance

For this I created an HTML named `base.html` that contains the basic structure of the webpage. This file contains the header, navbar, and footer of the webpage. This file is used as the base template for the other templates. The other templates extend the base template and override the blocks that they need to change. This is done by using the `{% extends 'base.html' %}` and `{% block content %}` tags in the other templates. This will inherit the base template and override the content block with the content of the other templates.
This helps to save time and make the code more organized, because I don't have to repeat the same code in every template. I only have to create the base template and extend it in the other templates.

e.g. `base.html`
```.html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}Reddit Webpage{% endblock %}</title>
    <link rel="stylesheet" href="{{ url_for('static', filename='styles.css') }}">
</head>
<body>
    <!-- Rest of the code -->
</body>
</html>
```

e.g. `home.html`
```.html
{% extends 'base.html' %}

{% block title %}Home - Reddit Webpage{% endblock %}

{% block content %}
    <!-- Content of the home page -->
{% endblock %}
```

# Criteria D: Functionality

[Link for the video](https://youtu.be/RMYuy-wQx2s)

# Criteria E: Evaluation
## Evaluation by Client


| Criteria                                                                                            | Met? | Feedback                                                                                                                                                                                                                                                                                    |
|-----------------------------------------------------------------------------------------------------|------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| The platform includes a login and registration system with input validation and secure data storage | Yes  | The login (`login` function) and registration (`register` function) systems are well-implemented with input validation and secure password hashing (`make_hash` function).                                                                                                                  |
| Access to specific features is restricted to logged-in users                                        | Yes  | Access control is properly enforced using Flask-Login decorators (`@login_required`), ensuring that only logged-in users can access certain features.                                                                                                                                       |
| The platform supports a posting system with image, title, content, and date                         | Yes  | The posting system allows users to create posts with images, titles, content, and timestamps effectively (`create_post` function).                                                                                                                                                          |
| The platform provides a like and comment system                                                     | Yes  | The platform supports liking (`like_post` function) and commenting (`add_comment` function) on posts, but the ability to edit and delete comments is not specified in the provided code.                                                                                                    |
| An interactive feed displays posts from followed users                                              | Yes  | The interactive feed dynamically displays posts from followed users, including like counts and comments (`home` function).                                                                                                                                                                  |
| Users have a profile page where they can update their bio and profile picture                       | Yes  | Profile pages allow users to update their bio and profile picture (`profile` function), view their posts, likes, and followers.                                                                                                                                                             |
| The platform allows users to follow/unfollow other users                                            | Yes  | The follow (`follow_user` function) and unfollow (`unfollow_user` function) functionalities are implemented, enabling users to manage their social connections.                                                                                                                             |
| The webpage allows to submit pictures                                                               | Yes  | The platform allows users to upload images when creating posts (`create_post` function) and updating their profile picture (`upload_image` function). However, ensure that file validation is robust (`allowed_file` function) and file paths are securely handled using `secure_filename`. |


The client is very satisfies with the result of the project. The website meets all the success criteria given by the user, these success criterias are shown in one email (See Appendix 1). During beta testing, the client suggested to develop in a further way the visual part of the webpage (See Appendix 4), this request was taken into account and the final product was delivered with the changes requested by the user (See Appendix 5).
After the visual changes were made, the user was very satisfied with the final product (See Appendix 6).

## Evaluation by Peer

My peer is very satisfied with the product, with the website meeting all the success criteria. Overall, the project demonstrates a solid implementation of a social media platform similar to Reddit, featuring user authentication, dynamic content rendering, and interactive functionalities such as posting, liking, commenting, and following. The code effectively uses Flask for routing and user session management, and SQLite for data storage, with secure practices like password hashing and input validation. To further enhance the platform's user experience and scalability, it is recommended to implement real-time updates using WebSockets. This would allow for instant updates to posts, comments, and likes without requiring page reloads, significantly improving the interactivity and responsiveness of the application. Additionally, migrating to a more robust database system like PostgreSQL would enhance the platform's ability to handle larger volumes of data and concurrent users more efficiently.

## Extensibility
The client was very satisfied with the final result, as it met all of his requirements. After some additional discussion, we concluded that the following future extensions could be added:

1. **Real-time Updates**: Implement real-time updates using WebSockets to provide instant updates to posts, comments, and likes without requiring page reloads. This would significantly improve the interactivity and responsiveness of the application.
2. **Database Migration**: Migrate to a more robust database system like PostgreSQL to enhance the platform's ability to handle larger volumes of data and concurrent users more efficiently.
3. **User Notifications**: Implement a notification system to alert users of new likes, comments, and followers, enhancing user engagement and interaction.
4. **User Search Functionality**: Add a search feature to allow users to search for other users, posts, or topics, improving the platform's usability and discoverability.
5. **Post Sorting and Filtering**: Implement post sorting and filtering options to allow users to view posts based on different criteria such as date, likes, and topics.

# Appendix

![Email1.png](static%2FImages_rep%2FEmail1.png)

*Fig.1:* User asking for the webpage development

![Email2.png](static%2FImages_rep%2FEmail2.png)

*Fig.2:* Developer answering the user

![Email3.png](static%2FImages_rep%2FEmail3.png)

*Fig.3:* Developer giving the first draft of the webpage

![Email4.png](static%2FImages_rep%2FEmail4.png)

*Fig.4:* User asking for some changes in the webpage

![Email5.png](static%2FImages_rep%2FEmail5.png)

*Fig.5:* Developer giving the final product

![Email6.png](static%2FImages_rep%2FEmail6.png)

*Fig.6:* User thanking the developer
