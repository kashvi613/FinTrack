from flask import Flask, render_template

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True)

# from flask import Flask: Flask library se Flask class import kar rahe hain.
# app = Flask(__name__): ye hamara web application object banata hai. __name__ 
# Flask ko batata hai ki project ki files (templates, static) kahan hain.
# @app.route("/"): ye decorator hai. Matlab: jab koi browser / (home page) khole, 
# neeche wala function chalao. Isi ko route kehte hain.
# def home(): aur return "...": ye function browser ko jo text return karega 
# wahi screen pe dikhega.
# if __name__ == "__main__":: ye tab True hota hai jab tum file ko seedha 
# python app.py se chalao. Kisi aur file se import hone par server automatically 
# start nahi hoga.
# app.run(debug=True): server start karta hai. debug=True se code save karte hi 
# server auto-reload hota hai aur error browser mein dikhta hai. Ye sirf development ke 
# liye hai, production mein kabhi on nahi rakhte.

# python app.py
#  * Serving Flask app 'app'
#  * Debug mode: on
# WARNING: This is a development server. Do not use it in a production deployment. Use a production WSGI server instead.
#  * Running on http://127.0.0.1:5000
# Press CTRL+C to quit
#  * Restarting with stat
#  * Debugger is active!
#  * Debugger PIN: 255-243-657
# 127.0.0.1 - - [14/Nov/2026 16:42:01] "GET / HTTP/1.1" 200 -
# 127.0.0.1 - - [14/Nov/2026 16:42:01] "GET /favicon.ico HTTP/1.1" 404 -

# Debug mode: on: debug=True ki wajah se. Code save karte hi server restart hoga.
# Running on http://127.0.0.1:5000: 127.0.0.1 tumhara apna computer hai (localhost), 
# aur 5000 port number hai. Matlab server sirf tumhare laptop pe chal raha hai, 
# internet pe nahi.
# Restarting with stat: Flask file changes pe nazar rakhta hai aur auto-reload karta hai.
# Debugger PIN: browser mein error aaye toh interactive debugger khulta hai, 
# ye PIN uske liye hai. Ise kisi ke saath share nahi karte.

# render_template ko import kiya. Ye templates/ folder se HTML file uthata hai 
# aur browser ko bhejta hai.
# home() ab seedha text return karne ke bajay index.html return karta hai.
