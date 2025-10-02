# app.py
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_mysqldb import MySQL
from flask_bcrypt import Bcrypt
from dotenv import load_dotenv
# from openai import OpenAI
import os
import json
import gzip
from datetime import date
import requests


#client = OpenAI()

# Flutterwave API credentials (TEST MODE)
PAYSTACK_PUBLIC_KEY = "pk_test_d1435a1fe37e4d2ee9340f10e455ba037f7b0cc5"
PAYSTACK_SECRET_KEY = "sk_test_fb568f148fb4bd47af7f7c5043c699351cada724"
PAYSTACK_VERIFY_URL = "https://api.paystack.co/transaction/verify/{}"


# ------------------ Load Environment ------------------
#load_dotenv()
# OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
# client = OpenAI(api_key=OPENAI_API_KEY)

app = Flask(__name__)
bcrypt = Bcrypt(app)
app.secret_key = os.getenv("SECRET_KEY", "supersecretkey")

# ------------------ MySQL CONFIG ------------------
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = '1freedom'
app.config['MYSQL_DB'] = 'biteright'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
app.config['MYSQL_CHARSET'] = 'utf8mb4'

mysql = MySQL(app)

db_initialized = False
dataset_loaded = False

# ------------------ Local Nutrition Dataset ------------------
DATASET_PATH = os.path.expanduser(
    "~/.cache/huggingface/hub/datasets--openfoodfacts--ingredient-detection/snapshots"
)
TRAIN_FILE = "ingredient_detection_dataset_train.jsonl.gz"
nutrition_lookup = {}

def load_dataset():
    global nutrition_lookup, dataset_loaded
    if dataset_loaded:
        return
    file_path = None
    for root, dirs, files in os.walk(DATASET_PATH):
        if TRAIN_FILE in files:
            file_path = os.path.join(root, TRAIN_FILE)
            break
    if not file_path:
        print(f"⚠️ Dataset file not found at {TRAIN_FILE}")
        return
    try:
        with gzip.open(file_path, "rt", encoding="utf-8") as f:
            for line in f:
                try:
                    item = json.loads(line)
                    name = item.get("name", "").lower()
                    calories = float(item.get("calories", 0) or 0)
                    protein = float(item.get("protein_g", 0) or 0)
                    fat = float(item.get("fat_g", 0) or 0)
                    if name:
                        nutrition_lookup[name] = {
                            "calories": calories or 100,
                            "protein_g": protein or 5,
                            "fat_g": fat or 5
                        }
                except:
                    continue
        dataset_loaded = True
        print(f"✅ Dataset loaded. {len(nutrition_lookup)} ingredients available.")
    except Exception as e:
        print(f"⚠️ Error loading dataset: {e}")

# ------------------ Initialize Database ------------------
def init_db():
    global db_initialized
    if db_initialized:
        return
    try:
        cur = mysql.connection.cursor()
        # Users table
        cur.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(100) UNIQUE NOT NULL,
                email VARCHAR(100) UNIQUE NOT NULL,
                password VARCHAR(255) NOT NULL
            )
        ''')
        # Meals table
        cur.execute('''
            CREATE TABLE IF NOT EXISTS meals (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT,
                food_item VARCHAR(255) NOT NULL,
                calories DECIMAL(10,2),
                protein DECIMAL(10,2),
                fat DECIMAL(10,2),
                suggestion VARCHAR(255),
                log_date DATE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        ''')
        # Drinks table
        cur.execute('''
            CREATE TABLE IF NOT EXISTS drinks (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT,
                drink_name VARCHAR(255) NOT NULL,
                volume_ml DECIMAL(10,2),
                calories DECIMAL(10,2),
                sugar_g DECIMAL(10,2),
                log_date DATE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        ''')
        mysql.connection.commit()
        cur.close()
        db_initialized = True
        print("✅ Database initialized successfully.")
    except Exception as e:
        print(f"⚠️ Error initializing database: {e}")

@app.before_request
def before_every_request():
    init_db()
    load_dataset()

# ------------------ AUTH ROUTES ------------------
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form["username"]
        email = request.form["email"]
        password = bcrypt.generate_password_hash(request.form["password"]).decode("utf-8")
        try:
            cur = mysql.connection.cursor()
            cur.execute(
                "INSERT INTO users (username, email, password) VALUES (%s, %s, %s)",
                (username, email, password)
            )
            mysql.connection.commit()
            cur.close()
            flash("✅ Account created! Please log in.", "success")
            return redirect(url_for("login"))
        except Exception as e:
            flash(f"⚠️ Error: {e}", "danger")
    return render_template("signup.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        cur = mysql.connection.cursor()
        cur.execute("SELECT id, username, password FROM users WHERE email = %s", [email])
        user = cur.fetchone()
        cur.close()
        if user and bcrypt.check_password_hash(user["password"], password):
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            flash("✅ Login successful!", "success")
            return redirect(url_for("index"))
        else:
            flash("⚠️ Invalid email or password.", "danger")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("login"))

# ------------------ NUTRITION + DRINKS ------------------
def get_nutritional_data(food_item):
    return nutrition_lookup.get(food_item.lower(), {"calories": 100, "protein_g": 5, "fat_g": 5})

def suggest_alternative(food_item):
    suggestions = {
        "fries": "Try baked sweet potato fries 🍠 (lower fat, higher fiber).",
        "soda": "Switch to sparkling water with lemon 🍋 (zero sugar).",
        "burger": "Opt for a grilled chicken sandwich 🥪 (less fat).",
        "pizza": "Try a thin-crust veggie pizza 🍕 (fewer calories).",
        "ice cream": "Go for frozen yogurt 🍦 (lighter option)."
    }
    return suggestions.get(food_item.lower(), "Looks good! 👍")

# AI-powered daily suggestion
#def ai_daily_tip(meals, drinks):
   # try:
        #meal_text = ", ".join([m["food_item"] for m in meals]) or "nothing"
        #drink_text = ", ".join([d["drink_name"] for d in drinks]) or "nothing"
        #prompt = f"""
        #User consumed today:
        #Meals: {meal_text}
        #Drinks: {drink_text}
        #Give practical tips to improve nutrition, hydration, and reduce sugar/alcohol intake.
        #"""

        #response = client.chat.completions.create(
           # model="gpt-3.5-turbo",  # or gpt-4 if you have access
           # messages=[
           #     {"role": "system", "content": "You are a helpful nutrition assistant."},
            #    {"role": "user", "content": prompt}
           # ],
           # temperature=0.7,
           # max_tokens=150
        #)
       # return response.choices[0].message.content.strip()
    #except Exception as e:
       # print(f"⚠️ AI suggestion error: {e}")
       # return "Keep tracking your meals and drinks for a healthier day!"

# ------------------ MAIN APP ROUTES ------------------
@app.route("/")
def index():
    if "user_id" not in session:
        return redirect(url_for("login"))

    cur = mysql.connection.cursor()
    # Meals today
    cur.execute(
        """SELECT food_item, calories, protein, fat, suggestion, log_date
           FROM meals WHERE user_id = %s AND log_date = %s""",
        (session["user_id"], date.today())
    )
    meals = cur.fetchall()

    # Drinks today
    cur.execute(
        """SELECT drink_name, volume_ml, calories, sugar_g, log_date
           FROM drinks WHERE user_id = %s AND log_date = %s""",
        (session["user_id"], date.today())
    )
    drinks = cur.fetchall()
    cur.close()

    total_calories = sum(m["calories"] for m in meals) + sum(d["calories"] for d in drinks)
    total_protein = sum(m["protein"] for m in meals)
    total_fat = sum(m["fat"] for m in meals)

    #daily_tip = ai_daily_tip(meals, drinks)

    return render_template(
        "index.html",
        meals=meals,
        drinks=drinks,
        total_calories=round(total_calories, 2),
        total_protein=round(total_protein, 2),
        total_fat=round(total_fat, 2),
        username=session["username"],
        #daily_tip=daily_tip
    )

# ------------------ Log Meal ------------------
@app.route("/log_meal", methods=["POST"])
def log_meal():
    if "user_id" not in session:
        return redirect(url_for("login"))

    food_item = request.form.get("food_item")
    if food_item:
        nutrition = get_nutritional_data(food_item)
        calories = nutrition["calories"]
        protein = nutrition["protein_g"]
        fat = nutrition["fat_g"]
        suggestion = suggest_alternative(food_item)

        try:
            cur = mysql.connection.cursor()
            cur.execute(
                """INSERT INTO meals (user_id, food_item, calories, protein, fat, suggestion, log_date)
                   VALUES (%s, %s, %s, %s, %s, %s, NOW())""",
                (session["user_id"], food_item, calories, protein, fat, suggestion)
            )
            mysql.connection.commit()
            cur.close()
        except Exception as e:
            print(f"⚠️ Error logging meal: {e}")
    return redirect(url_for("index"))

# ------------------ Log Drink ------------------
@app.route("/log_drink", methods=["POST"])
def log_drink():
    if "user_id" not in session:
        return redirect(url_for("login"))

    drink_name = request.form.get("drink_name")
    volume_ml = float(request.form.get("volume_ml") or 0)
    calories = float(request.form.get("calories") or 0)
    sugar_g = float(request.form.get("sugar_g") or 0)

    if drink_name:
        try:
            cur = mysql.connection.cursor()
            cur.execute(
                """INSERT INTO drinks (user_id, drink_name, volume_ml, calories, sugar_g, log_date)
                   VALUES (%s, %s, %s, %s, %s, NOW())""",
                (session["user_id"], drink_name, volume_ml, calories, sugar_g)
            )
            mysql.connection.commit()
            cur.close()
        except Exception as e:
            print(f"⚠️ Error logging drink: {e}")
    return redirect(url_for("index"))

# ------------------ PAYSTACK PAYMENT ROUTES -----------------
@app.route("/checkout", methods=["GET", "POST"])
def checkout():
    if "user_id" not in session:
        return redirect(url_for("login"))

    # If subscription button posts amount/email to /checkout, render checkout with those values
    if request.method == "POST":
        amount = request.form.get("amount", 0)
        email = request.form.get("email") or session.get("email") or f"{session.get('username','user')}@example.com"
        try:
            # normalize amount to number (frontend will multiply by 100 later)
            amount = float(amount)
        except Exception:
            amount = 500.0
        return render_template(
            "checkout.html",
            PAYSTACK_PUBLIC_KEY=PAYSTACK_PUBLIC_KEY,
            amount=amount,
            email=email
        )

    # GET -> show checkout (default values)
    return render_template(
        "checkout.html",
        PAYSTACK_PUBLIC_KEY=PAYSTACK_PUBLIC_KEY,
        amount=500,
        email=session.get("email") or f"{session.get('username','user')}@example.com"
    )


@app.route("/verify-payment", methods=["POST"])
def verify_payment():
    """
    Called by frontend after Paystack returns a reference.
    Expects JSON: { "reference": "<paystack_reference>" }
    """
    data = request.get_json() or {}
    reference = data.get("reference")
    if not reference:
        return jsonify({"status": "error", "message": "missing reference"}), 400

    headers = {"Authorization": f"Bearer {PAYSTACK_SECRET_KEY}"}
    url = PAYSTACK_VERIFY_URL.format(reference)

    try:
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
        payload = resp.json()
    except requests.RequestException as e:
        return jsonify({"status": "error", "message": f"verification request failed: {e}"}), 502

    # Paystack returns payload['status'] True and payload['data']['status'] == 'success'
    ok = payload.get("status") is True and payload.get("data", {}).get("status") == "success"
    if ok:
        # Optionally: save payment/upgrade plan in DB here.
        # Example:
        # cur = mysql.connection.cursor()
        # cur.execute("INSERT INTO payments (user_id, reference, amount, status) VALUES (%s, %s, %s, %s)",
        #             (session['user_id'], reference, payload['data']['amount']/100, 'success'))
        # mysql.connection.commit()
        return jsonify({"status": "success", "data": payload.get("data")})
    else:
        return jsonify({"status": "failed", "data": payload}), 400


# ------------------ RUN APP ------------------
if __name__ == "__main__":
    app.run(debug=True)

      