from flask import Flask, request, jsonify
from solve_captcha import main
import requests
import logging

app = Flask(__name__)

logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')

@app.route('/solve_captcha', methods=['POST'])
def solve_captcha():
    try:
        id, token, index = main()
        return jsonify({"result": {
            "id": id,
            "success": "right"
        }, "token": token, "clicks": index }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
