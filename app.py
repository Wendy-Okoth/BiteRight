# app.py
from flask import Flask, render_template, request, redirect, url_for, session, flash
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
FLW_PUBLIC_KEY = "9cdad2c1-a9e8-439c-a1bc-32b3d57020d5"
FLW_SECRET_KEY = "q1cp4vxcSdf1TEMFkIFnGOzZ9Xh6lk88"
FLW_ENCRYPTION_KEY = "8QadcNctW1gTG+4PKLnyljfhAt0P2CIwNYSP9oz7fWs="
FLW_BASE_URL = "https://api.flutterwave.com/v3"



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

# ------------------ FLUTTERWAVE PAYMENT ROUTES ------------------
@app.route("/checkout", methods=["GET", "POST"])
def checkout():
    if "user_id" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        amount = request.form.get("amount")
        email = request.form.get("email")
        name = session.get("username", "User")

        headers = {
            "Authorization": f"Bearer {FLW_SECRET_KEY}",
            "Content-Type": "application/json"
        }

        data = {
            "tx_ref": f"biteright-{session['user_id']}-{date.today()}",
            "amount": amount,
            "currency": "KES",  # You can switch to USD, NGN, etc.
            "redirect_url": url_for("payment_callback", _external=True),
            "customer": {
                "email": email,
                "name": name
            },
            "customizations": {
                "title": "BiteRight Premium",
                "description": "Support our app & unlock extra features 🎉"
            }
        }

        response = requests.post(f"{FLW_BASE_URL}/payments", headers=headers, json=data)
        result = response.json()

        if result.get("status") == "success":
            return redirect(result["data"]["link"])
        else:
            flash("⚠️ Payment initialization failed.", "danger")
            return redirect(url_for("checkout"))

    return render_template("checkout.html")


@app.route("/payment_callback")
def payment_callback():
    status = request.args.get("status")
    tx_ref = request.args.get("tx_ref")
    transaction_id = request.args.get("transaction_id")

    if status == "successful":
        # Verify payment with Flutterwave
        headers = {"Authorization": f"Bearer {FLW_SECRET_KEY}"}
        verify_url = f"{FLW_BASE_URL}/transactions/{transaction_id}/verify"
        response = requests.get(verify_url, headers=headers)
        result = response.json()

        if result.get("status") == "success":
            flash("✅ Payment successful! Thank you for supporting BiteRight.", "success")
        else:
            flash("⚠️ Payment verification failed.", "danger")
    else:
        flash("❌ Payment was not completed.", "danger")

    return redirect(url_for("index"))

# ------------------ RUN APP ------------------
if __name__ == "__main__":
    app.run(debug=True)

      