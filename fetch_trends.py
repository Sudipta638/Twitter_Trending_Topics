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


# MongoDB setup
client = pymongo.MongoClient("mongodb+srv://sudiptadas2303:95939896@cluster0.iaf3m7m.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
db = client["twitter_trends"]
collection = db["trends"]


def get_proxymesh_proxy():
    # ProxyMesh Credentials
    PROXYMESH_USERNAME = "Sudipta462"
    PROXYMESH_PASSWORD = "Sudipta@462"
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
        # proxy_ip, proxy_port = proxy_data['proxies'][0].split(':')
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

    # try:
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

    # except Exception as e:
    #     raise e
    # finally:
    #     driver.quit()

def store_trending_topics(trending_topics: list, run_id: str, end_time: datetime, proxy_ip: str) -> None:
    # Store the trending topics in a MongoDB collection
    record = {
        "run_id": run_id,
        "end_time": end_time,
        "ip_address": proxy_ip
    }

    for i, trend in enumerate(trending_topics, start=1):
        record[f"trend{i}"] = trend

    collection.insert_one(record)
    
    # Trending topics does not always contain 5 topics, so we need to check if the list size is 5 or less
    # record = {
    #     "run_id": run_id,
    #     "trend1": trending_topics[0],
    #     "trend2": trending_topics[1],
    #     "trend3": trending_topics[2],
    #     "trend4": trending_topics[3],
    #     "trend5": trending_topics[4],
    #     "end_time": end_time,
    #     "ip_address": proxy_ip
    # }

    print(f"Trending topics stored in MongoDB collection with run_id {run_id}")
    return record

def fetch_all_trending_topics():
    for doc in collection.find():
        print(doc)


    

if __name__ == "__main__":
    twitter_username = "@das638461"
    twitter_password = "Sudipta@638"

    try:
        # Get a unique run ID
        run_id = str(uuid.uuid4())

        # Get a proxy from ProxyMesh
        proxy_url = get_proxymesh_proxy()

        # Fetch trending topics from Twitter
        trending_topics_list = login_twitter_and_fetch_trending_topics(username=twitter_username, password=twitter_password, proxy_url=proxy_url)
        end_time = datetime.now()
        store_trending_topics(trending_topics_list, run_id, end_time, proxy_url)
        

        # # Wait for 15 seconds before fetching trending topics from MongoDB - TESTING
        # time.sleep(15)
        # fetch_all_trending_topics()
      
    except Exception as e:
        print(f"An error occurred: {e}")
