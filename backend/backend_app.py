from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_swagger_ui import get_swaggerui_blueprint
from datetime import datetime
import json

app = Flask(__name__)
CORS(app)  # This will enable CORS for all routes

SWAGGER_URL = "/api/docs"
API_URL = "/static/masterblog.json"

swagger_ui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL,
    config={
        "app_name": "Masterblog API"
    }
)

app.register_blueprint(
    swagger_ui_blueprint,
    url_prefix=SWAGGER_URL
)

def load_posts():
    try:
        with open("posts.json", "r", encoding="utf-8") as file:
            return json.load(file)
    except FileNotFoundError:
        return []
    except json.JSONDecodeError:
        return []

def save_posts(posts):
    with open("posts.json", "w", encoding="utf-8") as file:
        json.dump(posts, file, indent=4, ensure_ascii=False)


def is_valid_date(date_string):
    try:
        datetime.strptime(date_string, '%Y-%m-%d')
        return True
    except ValueError:
        return False

@app.route('/api/posts', methods=['GET'])
def get_posts():
    sort = request.args.get('sort')
    direction = request.args.get('direction')

    if sort and sort not in ['title', 'content', 'author', 'date']:
        return jsonify({"error": "Invalid sort field"}), 400

    if direction and direction not in ['asc', 'desc']:
        return jsonify({"error": "Invalid sort direction"}), 400

    posts = load_posts()

    if sort:
        reverse = direction == 'desc'
        if sort == 'date':
            posts.sort(
                key=lambda post: datetime.strptime(post['date'], '%Y-%m-%d'),
                reverse=reverse
            )
        else:
            posts.sort(
                key=lambda post: post[sort].lower(),
                reverse=reverse
            )

    return jsonify(posts), 200

@app.route('/api/posts/search', methods=['GET'])
def search_posts():
    search = request.args.get('search')

    posts = load_posts()

    if not search:
        return jsonify(posts), 200

    results = []

    for post in posts:
        if (
            search.lower() in post['title'].lower()
            or search.lower() in post['content'].lower()
            or search.lower() in post['author'].lower()
            or search.lower() in post['date'].lower()
        ):
            results.append(post)

    return jsonify(results), 200
@app.route('/api/posts', methods=['POST'])
def add_post():
    data = request.get_json()

    if not data or 'title' not in data:
        return jsonify({"error": "Title is required"}), 400

    if 'content' not in data:
        return jsonify({"error": "Content is required"}), 400

    if 'author' not in data:
        return jsonify({"error": "Author is required"}), 400

    if 'date' not in data:
        return jsonify({"error": "Date is required"}), 400

    if not is_valid_date(data['date']):
        return jsonify({
            "error": "Invalid date format. Use YYYY-MM-DD"
        }), 400

    # Read existing posts from posts.json
    posts = load_posts()

    new_id = max((post['id'] for post in posts), default=0) + 1

    new_post = {
        "id": new_id,
        "title": data['title'],
        "content": data['content'],
        "author": data['author'],
        "date": data['date']
    }

    # Add the new post to the list
    posts.append(new_post)

    # Save the updated list in posts.json
    save_posts(posts)

    return jsonify(new_post), 201

@app.route('/api/posts/<int:post_id>', methods=['DELETE'])
def delete_post(post_id):
    posts = load_posts()

    for post in posts:
        if post['id'] == post_id:
            posts.remove(post)
            save_posts(posts)

            return jsonify({
                "message": f"Post with id {post_id} has been deleted successfully."
            }), 200

    return jsonify({"error": "Post not found"}), 404

@app.route('/api/posts/<int:post_id>', methods=['PUT'])
def update_post(post_id):
    data = request.get_json()

    if 'date' in data and not is_valid_date(data['date']):
        return jsonify({
            "error": "Invalid date format. Use YYYY-MM-DD"
        }), 400

    posts = load_posts()

    for post in posts:
        if post['id'] == post_id:
            post['title'] = data.get('title', post['title'])
            post['content'] = data.get('content', post['content'])
            post['author'] = data.get('author', post['author'])
            post['date'] = data.get('date', post['date'])

            save_posts(posts)

            return jsonify(post), 200

    return jsonify({"error": "Post not found"}), 404


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5002, debug=True)
