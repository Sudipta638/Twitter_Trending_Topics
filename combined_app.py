from flask import Flask, render_template, jsonify
from selenium import webdriver
from selenium.webdriver import ChromeOptions, Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
import time
import uuid
from datetime import datetime
import pymongo
import requests
import base64

from bson import ObjectId
import json

from dotenv import load_dotenv
import os

# Load the environment variables from the .env file
load_dotenv()

# Now you can access the variables
twitter_username = os.getenv('twitter_username')
twitter_password = os.getenv('twitter_password')
MongoDBUrl = os.getenv('MongoDBUrl')
ProxyMeshUsername = os.getenv('ProxyMeshUsername')
Proxymeshpassword = os.getenv('Proxymeshpassword')

#Credentials


class JSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)
        return super().default(o)


app = Flask(__name__)

# MongoDB setup
client = pymongo.MongoClient(MongoDBUrl)
db = client["twitter_trends"]
collection = db["trends"]

def get_proxymesh_proxy():
    # ProxyMesh Credentials
    PROXYMESH_USERNAME =  ProxyMeshUsername
    PROXYMESH_PASSWORD = Proxymeshpassword
    PROXYMESH_API_URL = "https://proxymesh.com/api/proxies/"

    # Encode the username and password for authentication
    credentials = f"{PROXYMESH_USERNAME}:{PROXYMESH_PASSWORD}"
    encoded_credentials = base64.b64encode(credentials.encode()).decode()

    # Set the headers with the encoded credentials
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Basic {encoded_credentials}",
    }
    
    # Send a request to the ProxyMesh API to get a new proxy IP
    response = requests.get(PROXYMESH_API_URL, headers=headers)

    # Check if the request was successful
    if response.status_code == 200:
        proxy_data = response.json()
        proxy_ip_port = proxy_data['proxies'][0] 
        print(f"ProxyMesh proxy IP: {proxy_ip_port}")
        return proxy_ip_port
    else:
        raise Exception(f"Failed to get proxy from ProxyMesh: {response.text}")

def login_twitter_and_fetch_trending_topics(username: str, password: str, proxy_url: str) -> list:
    options = ChromeOptions()
    options.add_argument("--start-maximized")

    # proxy-server
    options.add_argument("--proxy-server=%s" % proxy_url)

    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    driver = webdriver.Chrome(options=options)

    try:
        # Open the Twitter login page
        url = "https://x.com/i/flow/login"
        driver.get(url)

        # Find and input the username
        username_input = WebDriverWait(driver, 20).until(EC.visibility_of_element_located((By.CSS_SELECTOR, 'input[autocomplete="username"]')))
        username_input.send_keys(username)
        username_input.send_keys(Keys.ENTER)

        # Find and input the password
        password_input = WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.CSS_SELECTOR, 'input[name="password"]')))
        password_input.send_keys(password)
        password_input.send_keys(Keys.ENTER)

        # Wait for a short period - 10 seconds - to ensure the login process completes
        time.sleep(20)

        # Locate the "Trending now" section
        trending_section = WebDriverWait(driver, 20).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, 'div[aria-label="Timeline: Trending now"]'))
        )
        
        # Locate all trending topics within the section
        trends = trending_section.find_elements(By.CSS_SELECTOR, 'div.r-a023e6.r-1bymd8e')
        print(f"Found {len(trends)} trending topics")
        
        trending_topics = []
        for idx, trend in enumerate(trends):
            topic = trend.find_element(By.TAG_NAME, 'span').text
            trending_topics.append(topic)
            print(f"Fetched trending topic {idx + 1}: {topic}")

        return trending_topics
    except Exception as e:
        raise e
    finally:
        driver.quit()

def store_trending_topics(trending_topics: list, run_id: str, end_time: datetime, proxy_ip: str) -> dict:
    # Store the trending topics in a MongoDB collection
    record = {
        "run_id": run_id,
        "end_time": end_time,
        "ip_address": proxy_ip
    }

    for i, trend in enumerate(trending_topics, start=1):
        record[f"trend{i}"] = trend

    collection.insert_one(record)
    print(f"Trending topics stored in MongoDB collection with run_id {run_id}")
    return record

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/run-script', methods=['GET'])
def run_script():
    try:
        # Get a unique run ID
        run_id = str(uuid.uuid4())

        # Get a proxy from ProxyMesh
        proxy_url = get_proxymesh_proxy()

        # Fetch trending topics from Twitter
        trending_topics_list = login_twitter_and_fetch_trending_topics(
            username=twitter_username,
            password=twitter_password,
            proxy_url=proxy_url
        )

        # Check if the data is in the expected format
        if isinstance(trending_topics_list, list) and all(isinstance(topic, str) for topic in trending_topics_list):
            end_time = datetime.now()
            record = store_trending_topics(trending_topics_list, run_id, end_time, proxy_url)
            
            # Convert the MongoDB record to JSON with the custom encoder
            # record_json = json.dumps(record, cls=JSONEncoder)

            # Prepare the data to be returned as JSON
            data: dict[str, any] = {
                'dateTime': str(record['end_time'].strftime('%Y-%m-%d %H:%M:%S')),
                'ipAddress': str(record['ip_address']),
                'trends': [record[f'trend{i}'] for i in range(1, len(trending_topics_list) + 1)],
                }

            print(data)
            return jsonify(data)
        else:
            # If the data is not in the expected format, trigger the fallback condition
            print("Unexpected data format from login_twitter_and_fetch_trending_topics")
    except Exception as e:
        # If an error occurs, fetch the latest record from MongoDB
        latest_record = collection.find_one({}, sort=[('end_time', pymongo.DESCENDING)])
        # latest_record_json = json.dumps(latest_record, default=JSONEncoder)


        if latest_record:
            data = {
                'dateTime': latest_record['end_time'].strftime('%Y-%m-%d %H:%M:%S'),
                'ipAddress': latest_record['ip_address'],
                'trends': [latest_record[f'trend{i}'] for i in range(1, len([trend for trend in latest_record if trend.startswith('trend')]) + 1)],
                # 'jsonExtract': latest_record_json
                }
            return jsonify(data)
        else:
            return jsonify({'error': 'No data available in the database.'}), 500

if __name__ == '__main__':
    twitter_username = twitter_username
    twitter_password = twitter_password
    app.run(debug=True)