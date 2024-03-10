from flask import Flask, render_template, request,url_for, session, redirect
import psycopg2
from analyze_news import Analyze_news
from authlib.integrations.flask_client import OAuth
nltk.download('all')

# Connect to PostgreSQL database (replace with your credentials)
db_config = {
    'dbname': 'assignmentpy',
    'user': 'assignmentpy_user',
    'password': '6C1fFcmhXh1Woespyo9B4I3q63ATzvWN',
    'host': 'dpg-cnmmsgen7f5s73d7qngg-a ',
    'port': '5432'
}


conn = psycopg2.connect(**db_config)
cur = conn.cursor()

app = Flask(__name__)

oauth = OAuth(app)

app.config['SECRET_KEY'] = "my_secret_key"
app.config['GITHUB_CLIENT_ID'] = "5bf92ccee8e10ae8ed4e"
app.config['GITHUB_CLIENT_SECRET'] = "3de41e38a867acd352726ff4119b50235287cc92"

github = oauth.register(
    name='github',
    client_id=app.config["GITHUB_CLIENT_ID"],
    client_secret=app.config["GITHUB_CLIENT_SECRET"],
    access_token_url='https://github.com/login/oauth/access_token',
    access_token_params=None,
    authorize_url='https://github.com/login/oauth/authorize',
    authorize_params=None,
    api_base_url='https://api.github.com/',
    client_kwargs={'scope': 'user:email'},
)

# GitHub admin usernames for verification
github_admin_usernames = ["iamritikiit", "atmabodha"]

# Default route
@app.route('/admin_route')
def admin_route():
    is_admin = False
    github_token = session.get('github_token')
    if github_token:
        github = oauth.create_client('github')
        resp = github.get('user').json()
        username = resp.get('login')
        if username in github_admin_usernames:
            is_admin = True
    return render_template('admin_login.html', logged_in=github_token is not None, is_admin=is_admin)


# Github login route
@app.route('/login/github')
def github_login():
    github = oauth.create_client('github')
    redirect_uri = url_for('github_authorize', _external=True)
    return github.authorize_redirect(redirect_uri)

@app.route('/login/github/authorize')
def github_authorize():
    github = oauth.create_client('github')
    token = github.authorize_access_token()
    session['github_token'] = token
    resp = github.get('user').json()
    print(f"\n{resp}\n")

    if 'login' in resp:
        username = resp['login']
        if username in github_admin_usernames:
            analysis_data = fetch_analysis_data()
            return render_template('admin_portal.html', analysis_data=analysis_data)
        else:
            return f'you are not authorized to access this page'
    else:
        return f'Unable to fetch github username'


@app.route('/')
def home():
    return render_template('index.html')

@app.route('/submit_url', methods=['POST','GET']) 
def submit_url():
    if request.method == 'POST':
        url = request.form['url']
        analysis_result = Analyze_news(url)

        if analysis_result:

                # Connect to the database
            conn = psycopg2.connect(**db_config)
            cur = conn.cursor()
        
            # Create a table if it doesn't exist
            cur.execute("""
                CREATE TABLE IF NOT EXISTS analysis(
                    url_given VARCHAR(1000),
                    cleaned_text TEXT,
                    number_of_sentences INTEGER,
                    number_of_words INTEGER,
                    number_of_pos_tags INTEGER,
                    sentiment_analysis TEXT
                )
            """)
            # Store data in database
            cur.execute("INSERT INTO analysis (url_given, cleaned_text, number_of_sentences, number_of_words, number_of_pos_tags,sentiment_analysis) VALUES (%s, %s, %s, %s, %s, %s)",
                        (analysis_result['url'], analysis_result['text'], analysis_result['num_sentences'], analysis_result['num_words'], analysis_result['pos_tags'], analysis_result['sentiment_labels'] ))
            conn.commit()  # Commit changes to database

        return render_template('anlysis_page.html', analysis=analysis_result)  

#admin part
@app.route('/admin_login',methods=['POST','GET'])
def admin_login():
    if request.method == 'POST':
        return render_template('admin_login.html')
    else:
        return f'post method is not there'

@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = psycopg2.connect(**db_config)
        cur = conn.cursor()
        
        cur.execute("SELECT * FROM users WHERE username = %s AND password = %s", (username, password))
        user = cur.fetchone()

    if username == user[0] and password == user[1]:
        analysis_data = fetch_analysis_data()
        return render_template('admin_portal.html', analysis_data=analysis_data)

    return render_template('admin_login.html')  

def fetch_analysis_data():
    """Fetches data from the "analysis" table and returns a list of dictionaries."""
    try:
        conn = psycopg2.connect(**db_config)
        cur = conn.cursor()
        cur.execute("SELECT * FROM analysis")
        rows = cur.fetchall()
        analysis_data = []
        for row in rows:
            
            analysis_dict = {
                "url_given": row[0], 
                "cleaned_text": row[1],  
                "number_of_sentences": row[2], 
                "number_of_words": row[3],
                "number_of_pos_tags": row[4],
                "sentiment_label" : row[5]
            }

            analysis_data.append(analysis_dict)
        return analysis_data
    except Exception as e:
        print(f"Error fetching data: {e}")
        return []  # Return an empty list on error


if __name__ == "__main__":
    app.run(debug=True)
