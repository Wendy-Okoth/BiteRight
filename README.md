# 🥗 BiteRight

**BiteRight** is a diet and nutrition tracking app that helps users monitor their meals, drinks, and overall health goals.  
It offers free and subscription-based plans, with premium features such as **AI-powered diet assistance**.

---

## 🚀 Features
- ✅ Track meals & drinks
- ✅ Three subscription tiers:
  - **Free Plan** – Track up to **5 meals/drinks per week**
  - **Basic Plan ($7/month)** – Track up to **18 meals per day**, includes basic reports
  - **Premium Plan ($20/month)** – Unlimited tracking, AI diet assistant, advanced reports
- ✅ User authentication (Login/Signup)
- ✅ Integrated payment system
- ✅ Responsive UI

---

## 🛠️ Tech Stack
- **Backend:** Flask (Python)
- **Frontend:** HTML5, CSS3, Jinja2 Templates
- **Database:** MySQL (default, easy setup)
- **Payments:** Payment checkout integration (Flask routes)
- **Deployment:** GitHub + Python environment

---

## 📂 Project Structure
BiteRight/
 - app.py # Main Flask application
- templates/ # HTML templates (index, login, signup, base)
- static/ # CSS, JS, images
- venv/ # Virtual environment
- README.md # Project documentation

Copy code

---

## ⚙️ Installation & Setup
1. Clone the repo:
   ```bash
   git clone https://github.com/Wendy-Okoth/BiteRight.git
   cd BiteRight
Create a virtual environment:

bash
Copy code
python -m venv venv
source venv/bin/activate   # Mac/Linux
venv\Scripts\activate      # Windows
Install dependencies:

bash
Copy code
pip install -r requirements.txt
Run the app:

bash
Copy code
flask run
💳 Subscription Plans
Plan	Price	Features
Free	$0	Track up to 5 meals/drinks weekly
Basic	$7/month	Track 18 meals/day + basic reports
Premium	$20/month	Unlimited tracking + AI chatbot + advanced reports

🤝 Contributing
Contributions are welcome!

Fork the repository

Create a feature branch

Submit a Pull Request

📜 License
This project is licensed under the MIT License.
