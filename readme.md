# Twitter Trending Topics Scraper

This project is a Python script that uses Selenium to scrape the top 5 trending topics from Twitter's homepage under the "What's Happening" section. Each request to scrape the trending topics is sent from a new IP address using ProxyMesh. The scraped data is stored in a MongoDB database along with a unique ID, the name of the trends, the date and time of the script's execution, and the IP address used.

## Setup Instructions

1. Install the necessary Python packages:
   ```bash
   pip install flask pymongo selenium requests
   ```

2. Make sure you have Chrome browser installed, and download the ChromeDriver for your Chrome version from [here](https://sites.google.com/a/chromium.org/chromedriver/downloads). Add the ChromeDriver executable to your PATH.

3. Create a MongoDB database and collection. Replace the MongoDB URI and collection name in the `fetch_trends.py` file with your own.

4. Sign up for a ProxyMesh account and replace the `PROXYMESH_USERNAME` and `PROXYMESH_PASSWORD` in the `fetch_trends.py` file with your own credentials.

5. Replace the `twitter_username` and `twitter_password` variables in the `combined_app.py` file with your own Twitter account credentials.

6. Run the Flask application:
   ```bash
   python combined_app.py
   ```

7. Navigate to `http://localhost:5000` in your web browser to see the HTML page with a button to run the script.

## Usage

1. Click the "Click here to run the script" button on the webpage to execute the Selenium script.

2. The script will scrape the top 5 trending topics from Twitter's homepage and store them in the MongoDB database.

3. The webpage will display the fetched trending topics, the date and time of the query, the IP address used, and a button to run the script again.

## Demo Image

![Demo](demo.png)

**Note:** This project is for educational purposes only. Make sure to comply with Twitter's terms of service and use responsibly.