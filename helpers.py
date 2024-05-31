
from datetime import datetime
from library import DatabaseWorker

db_worker = DatabaseWorker('database.db')

def get_user_by_id(user_id):
    user_data = db_worker.search(f"SELECT * FROM users WHERE id = {user_id}")
    if user_data:
        return {
            'id': user_data[0],
            'username': user_data[1],
            'email': user_data[2],
            'profile_picture': user_data[5],
            'bio': user_data[6]
        }
    return None

def get_posts_by_user_id(user_id):
    posts_data = db_worker.search(f"""
        SELECT posts.*, 
               (SELECT COUNT(*) FROM likes WHERE likes.post_id = posts.id) AS like_count
        FROM posts 
        WHERE user_id = {user_id}
    """, multiple=True)

    posts = []
    for post_data in posts_data:
        post = transform_post_data(post_data)
        post['user'] = get_user_by_id(post['user_id'])
        post['comments'] = get_comments_by_post_id(post['id'])
        posts.append(post)
    return posts

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

def transform_post_data(post_data):
    created_at = post_data[4]
    updated_at = post_data[5]

    if created_at is not None:
        created_at = datetime.strptime(created_at, '%Y-%m-%d %H:%M:%S')
    if updated_at is not None:
        updated_at = datetime.strptime(updated_at, '%Y-%m-%d %H:%M:%S')

    return {
        'id': post_data[0],
        'user_id': post_data[1],
        'title': post_data[2],
        'content': post_data[3],
        'created_at': created_at,
        'updated_at': updated_at,
        'image_url': post_data[6],
        'topic': post_data[7],
        'like_count': post_data[8] if len(post_data) > 8 else 0
    }



def get_followed_users(user_id):
    follows_data = db_worker.search(f"""
        SELECT users.id, users.username, users.email, users.profile_picture, users.bio
        FROM follows
        JOIN users ON follows.followed_user_id = users.id
        WHERE follows.follower_id = {user_id}
    """, multiple=True)
    return [
        {
            'id': follow[0],
            'username': follow[1],
            'email': follow[2],
            'profile_picture': follow[3],
            'bio': follow[4]
        }
        for follow in follows_data
    ]


