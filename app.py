from flask import Flask, request, jsonify, render_template, send_from_directory
import sqlite3
import datetime
import uuid 
import os
from werkzeug.utils import secure_filename
import subprocess
import elo
import skill 
import random
import numpy


app = Flask(__name__)
DB_FILE = 'data.db'  # The SQLite database will be saved here


UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'svg'}
MAX_CONTENT_LENGTH = 1 * 1024 * 1024 # 1MB

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

# 1. Helper function to connect to DB and create tables if not exist
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, uuid TEXT, file TEXT)''')
    #c.execute('''CREATE TABLE IF NOT EXISTS selections (id INTEGER PRIMARY KEY AUTOINCREMENT, uuid TEXT, winner TEXT, looser TEXT, selected_date TEXT, voter TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS selections (id INTEGER PRIMARY KEY AUTOINCREMENT, uuid TEXT, option1 TEXT, points1, INTEGER, option2 TEXT, points2 INTEGER, selected_date TEXT, voter TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS polls (id INTEGER PRIMARY KEY AUTOINCREMENT, uuid TEXT UNIQUE, key TEXT , created_at TEXT, title TEXT, question TEXT)''')
    
    conn.commit()
    c.execute("SELECT name FROM sqlite_master WHERE type='table';")
    rows = c.fetchall()
    for r in rows:
        print("table: ", r)
    
    conn.close()


@app.route("/")
def index():
    print("index")
    return render_template("entry.html")

@app.route("/admin/<string:uuid>")
def admink(uuid):
    print("admin kw", uuid)
    key = request.args.get('key')
    # Example: use them to validate or modify behavior
    #if not uuid or not key:
    #    return jsonify({"error": "UUID and key are required"}), 400

    return render_template("admin.html", uuid = uuid, key = key)


@app.route("/poll/<string:uuid>")
def selection(uuid):
    print("poll", uuid)
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("SELECT * FROM polls WHERE uuid == ?", [(uuid)]) 
        rows = c.fetchall()
        conn.close()
        #print(rows)
        return render_template("selection.html", uuid = uuid, title = rows[0][4], question = rows[0][5])
    except Exception as e:
        print("poll error")
        return render_template("selection.html", uuid = uuid, title = "No poll loaded", question = "")

@app.route("/results/<string:uuid>")
def result(uuid):
    print("results", uuid)
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("SELECT * FROM polls WHERE uuid == ?", [(uuid)]) 
        rows = c.fetchall()
        conn.close()
        #print(rows)
        return render_template("results.html", uuid = uuid, title = rows[0][4], question = rows[0][5])
    except Exception as e:
        print("poll error")
        return render_template("results.html", uuid = uuid, title = "No poll loaded", question = "")




## API definitions


@app.route('/api/new_poll', methods=['GET'])
def new_poll():
    print("new_poll")
    now = datetime.datetime.now().isoformat()
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    random_string = str(uuid.uuid4())[:8]
    print("uuid", random_string)

    # Using parameterized queries prevents SQL Injection (Security Best Practice)
    try:
        r = c.execute("""INSERT INTO polls ( 
                    uuid, 
                    key,
                    created_at,
                    title,
                    question) 
                VALUES(  
                    ?,
                    lower(hex(randomblob(16))),
                    ?, 
                    ?,
                    ?)""", (random_string, now, "Poll Titile", "Question"))
        conn.commit()
        c.execute("SELECT uuid, key FROM polls WHERE uuid == ?", [(random_string)])
        rows = c.fetchall()
        if not rows:
            return jsonify({"error": "Creation error"}), 500
        #print("new poll", rows[0][1])

        return jsonify({"id": rows[0][0], "key": rows[0][1]}), 201
    except Exception as e:
        print(e)
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

@app.route('/api/load_poll/<string:uuid>/<string:key>', methods=['GET'])
def load_poll(uuid, key):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    try:
        c.execute("SELECT * FROM polls WHERE uuid == ? and key = ?", [(uuid), (key)]) 
        rows = c.fetchall()
        if not rows:
            return jsonify({"message": "Not enough users to choose from yet."}), 400
        
        results = rows[0][1:]
        conn.close()
        return jsonify(results)
    except Exception as e:
        print(e)
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

@app.route('/api/update_poll', methods=['POST'])
def update_poll():
    data = request.json
    print("update_poll", data)
    title = data.get('title')
    question = data.get('question')
    uuid = data.get('uuid')
    key = data.get('key')

    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    try:
        c.execute("UPDATE polls SET title = ?, question = ? WHERE uuid == ? and key = ?", [(title), (question), (uuid), (key)]) 
        conn.commit()
        return jsonify({"success": True }), 201
    except Exception as e:
        print(e)
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()


def check_permission(uuid, key):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    c.execute("SELECT * FROM polls WHERE uuid == ? and key = ?", [(uuid), (key)]) 
    rows = c.fetchall()
    conn.close()
    if not rows:
        print("no edit rights")
        return False
    
    print("edit rights granted")
    return True


def allowed_file(filename):
    """Validate file extension."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# 2. Endpoint: Create new user
@app.route('/api/create', methods=['POST'])
def create_user():
    print("create")
    #data = request.json
    #print(data)
    #print(request)
    #print(dir(request))
    #for p in request.form:
    #    pass
        #print("p", p)
    #name = data.get('name')
    #email = data.get('email')
    uuid = request.form['uuid']
    key = request.form['key']
    print("uuid", uuid)
    print("key", key)

    if not check_permission(uuid, key):
        return jsonify({"error": "no edit permissions"}), 500



    # Get files from FormData
    files = request.files.getlist('file')
    
    if not files:
        return jsonify({'error': 'No file uploaded'}), 400


    # Create upload directory if not exists
    uploads_dir = os.path.join(app.config['UPLOAD_FOLDER'], uuid)
    os.makedirs(uploads_dir, exist_ok=True)

    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    for file in files:
        print(file.filename)
        if file.filename == '':
            continue
        
        if not allowed_file(file.filename):
            return jsonify({'error': f'Invalid file type: {file.filename}'}), 400
        
        safe_filename = secure_filename(f"{file.filename}")
        filepath = os.path.join(uploads_dir, safe_filename)

        c.execute("SELECT * FROM users WHERE uuid == ? and file = ?", [(uuid), (filepath)]) 
        rows = c.fetchall()
        if rows:
           conn.close()
           return jsonify({'error': f'File already exists: {file.filename}'}), 400

        
        try:
            file.save(filepath)
            #return jsonify({'message': 'Files uploaded', 'count': len(files)}), 201
            c.execute("INSERT INTO users (uuid, file) VALUES (?, ?)", (uuid, filepath))
        except Exception as e:
            print(e)
            app.logger.error(f"Upload error: {str(e)}")
            conn.close()
            return jsonify({'error': str(e)}), 500
    conn.commit()
    conn.close()
    return jsonify({'message': 'Files uploaded', 'count': len(files)}), 201

# 3. Endpoint: Read all users
@app.route('/api/users/<uuid>', methods=['GET'])
def get_users(uuid):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE uuid == ? ORDER BY id DESC", [(uuid)]) # Selects all columns
    rows = c.fetchall()
    conn.close()
    
    results = [{"uuid": r[1], "file": r[2]} for r in rows]
    return jsonify(results)

def get_not_voted(uuid, voterId):
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        if(voterId == None or voterId == ""):
            c.execute("select file from users left join selections on (file == option1 or file == option2 ) and users.uuid == ? where (option1 is NULL or option2 is NULL) and users.uuid == ?;", [(uuid),(uuid)]) # Selects all columns
        else:
            c.execute("select file from users left join selections on (file == option1 or file == option2 ) and users.uuid == ? and voter == ? where (option1 is NULL or option2 is NULL) and users.uuid == ?;", [(uuid), (voterId), (uuid)]) # Selects all columns
        notvoted = c.fetchall()
        #print("not voted:", notvoted)
        conn.close()
        return notvoted
    except Exception as e:
        print(e)
        conn.close()
        return []

# 3. Endpoint: Read all users
@app.route('/api/results/<uuid>', methods=['POST', 'GET'])
def get_results(uuid):
    print("results0", uuid)
    conn = sqlite3.connect(DB_FILE)
    voterId = request.args.get('voteId')
    print("results2", voterId)
    try:
        c = conn.cursor()
        if(voterId == None or voterId == ""):
            c.execute("SELECT option1, points1, option2, points2 FROM selections WHERE uuid == ? ORDER BY id DESC", [(uuid)]) # Selects all columns
        else:
            c.execute("SELECT option1, points1, option2, points2  FROM selections WHERE uuid == ? and voter == ? ORDER BY id DESC", [(uuid), (voterId)]) # Selects all columns
        rows = c.fetchall()
        
        notvoted = get_not_voted(uuid, voterId)
        conn.close()
    except Exception as e:
        print(e)
        conn.close()
        return jsonify({"error": str(e)}), 500
    
    #print(rows)
    table = []
    wins= {}
    losses = {}
    ties = {}
    for r in rows:
        table.append([r[0], r[1], r[3], r[2]])
        wins[r[0]] = 0
        wins[r[2]] = 0
        losses[r[0]] = 0
        losses[r[2]] = 0
        ties[r[0]] = 0
        ties[r[2]] = 0

    print("results3")
    #print(table)
    for r in table:
        #print(r)
        if r[1] > r[2]:
            wins[r[0]] += 1
            losses[r[3]] += 1
        if r[1] < r[2]:
            wins[r[3]] += 1
            losses[r[0]] += 1
        if r[1] == r[2]:
            ties[r[3]] += 1
            ties[r[0]] += 1

    #print("wins", wins)
    #print("losses", losses)
    
    ranks = elo.calc_elo_obj(table)
    #print(ranks)
    ranks_s = skill.calc_skill_obj(table)
    #print(ranks_s)
    #print(ranks_s[0])
    print("====")

    td = {}
    for t in ranks_s:
        td[t.name] = t
    #print(notvoted)

    for r in ranks:
        print(r)
        print(td[r.name].ordinal())
        print(td[r.name])

    resultsfile=f"uploads/{uuid}/results_{voterId}.png"
    ranks_c = ranks_s
    ranks_s = skill.plot(ranks_s, resultsfile)

    results = []
    results += [{"file": resultsfile, "score": 0, "wins" : 1, "losses" : 1, "ties": 1, "mu": 0, "sigma":1, "type": "plot"}]
    results += [{"file": r[0], "score": 0, "wins": 0, "losses": 0, "ties": 0, "mu": 0, "sigma": 0, "type": "notvoted"} for r in notvoted]
    results += [{"file": r.name, "score": round(r.ordinal(),3), "wins": wins[r.name], "losses": losses[r.name], "ties": ties[r.name], "mu": round(r.mu,3), "sigma": round(r.sigma,3), "type": "voted"} for r in ranks_c]
    return jsonify(results)



@app.route('/api/random-select/<uuid>', methods=['GET', 'POST'])
def get_random_users(uuid):
    """Fetches 2 random users"""
    voterId = request.args.get('voterId')
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    print("voter id", voterId)
    try:
        #c.execute("SELECT * FROM users WHERE uuid == ? ORDER BY RANDOM() LIMIT 2", [(uuid)]) 
        count = 0
        numnotvoted = 0
        if voterId is None or voterId == "":
            print("select any")
            #c.execute("SELECT file, COUNT(*) FROM users JOIN selections ON users.file == selections.winner or file == looser WHERE users.uuid == ? GROUP BY file ORDER BY COUNT(*)", [(uuid)]) 
            c.execute("SELECT file, COUNT(*) FROM users LEFT JOIN selections ON users.file == selections.option1 or file == option2 WHERE users.uuid == ? GROUP BY file ORDER BY COUNT(*)", [(uuid)]) 
            rows = c.fetchall()
        else:
            print("select voter")
            c.execute("SELECT file, COUNT(*) FROM users LEFT JOIN selections ON (users.file == selections.option1 or file == option2 ) AND voter == ? WHERE users.uuid == ? GROUP BY file ORDER BY COUNT(*)", [(voterId), (uuid)]) 
            #c.execute("SELECT file, COUNT(*) FROM users LEFT JOIN selections ON users.file == selections.winner or file == looser WHERE users.uuid == ? GROUP BY file ORDER BY COUNT(*)", [(uuid)]) 
            rows = c.fetchall()
            #print("rows", rows)
            print("select count")
            c.execute("SELECT COUNT(*) FROM selections WHERE uuid == ? AND voter == ?", [(uuid), (voterId)]) 
            count = c.fetchall()[0][0]
            print("selected count:", count)
            numnotvoted = len(get_not_voted(uuid, voterId))
            print("not voted count:", numnotvoted)
        print("done selecting")

        print("rows")
        #print(rows)
        if len(rows) < 2:
            return jsonify({"message": "Not enough users to choose from yet."}), 400

        #selection = random.sample(rows, weights=(), k=2)
        total_counts = 0
        random.shuffle(rows)
        selection = []
        for r in rows:
            total_counts += r[1]
            #print(r[1])
            if r[1] <= 1:
                selection.append(r)
                if(len(selection) == 2):
                    break
            
        if(len(selection) != 2):
            print(total_counts)

            prob = []
            for r in rows:
                prob.append(r[1]/total_counts)
            prob.reverse()
            #print(prob)
            sample = numpy.random.choice(len(rows), size=2-len(selection), replace=False, p=prob)
            #print(sample)
            for s in sample:
                selection.append(rows[s])


        results = [{"file": r[0]} for r in selection]
        conn.close()

        return jsonify({"choices": results, "count": count, "notvoted": numnotvoted})
    except Exception as e:
        print(e)
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

# 4. NEW: Save your selection to the new table
@app.route('/api/choose/<uuid>', methods=['POST'])
def save_selection(uuid):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    now = datetime.datetime.now().isoformat()
    print("voting", uuid, now)
    s1 = request.args.get("s1")
    s2 = request.args.get("s2")
    p1 = int(request.args.get("p1"))
    p2 = int(request.args.get("p2"))
    voter = request.args.get("voter")
    if(p1 > 1 or p1 < 0 or p2 > 1 or p2 < 0):
        return jsonify({"error": "invalid Vote"}), 400

    winner, looser  = s1, s2
    if(p1 == 0):
        winner, looser = s2, s1
        p1, p2 = p2, p1
    
    print(uuid, winner, p1, looser, p2, now, voter)
    try:
        # Saving into our new selections table
        c.execute("INSERT INTO selections (uuid, option1, points1, option2, points2, selected_date, voter) VALUES (?, ?, ?, ?, ?, ?, ?)", 
                  (uuid, winner, p1, looser, p2, now, voter))
        conn.commit()
        return jsonify({"success": True, "message": f"You selected user #{s1}"})
    except Exception as e:
        print(e)
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()



@app.route('/uploads/<uuid>/<filename>')
def serve_file(uuid, filename):
    return send_from_directory(os.path.join(app.config['UPLOAD_FOLDER'], uuid), filename)




if __name__ == '__main__':
    init_db() # Ensure DB is ready
    app.run(debug=True, port=2605)

