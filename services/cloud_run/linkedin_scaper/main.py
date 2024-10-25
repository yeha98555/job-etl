from flask import Flask, jsonify, abort
import requests
from bs4 import BeautifulSoup
import urllib.parse
import math
import time
import random
import re
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

app = Flask(__name__)

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

def create_session():
    session = requests.Session()
    retries = Retry(total=5,
                    backoff_factor=0.1,
                    status_forcelist=[429, 500, 502, 503, 504])
    session.mount('https://', HTTPAdapter(max_retries=retries))
    return session

def make_request(url, session, max_retries=3, delay=10):
    for attempt in range(max_retries):
        try:
            response = session.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            if isinstance(e, requests.exceptions.HTTPError) and e.response.status_code == 429:
                wait_time = delay * (2 ** attempt)  # Exponential backoff
                app.logger.warning(f"Rate limited. Waiting for {wait_time} seconds before retrying.")
                time.sleep(wait_time)
            else:
                app.logger.error(f"Error fetching URL: {e}")
                if attempt == max_retries - 1:
                    raise
    raise Exception("Max retries reached")

@app.route('/scrape/<location>/<time_range>')
def scrape_linkedin(location, time_range):
    base_url = "https://www.linkedin.com/jobs/search"
    params = {
        "location": location,
        "f_TPR": time_range,
        "trk": "public_jobs_jobs-search-bar_search-submit",
        "position": 1,
        "pageNum": 0
    }
    url = f"{base_url}?{urllib.parse.urlencode(params)}"
    
    session = create_session()
    
    try:
        response = make_request(url, session)
        soup = BeautifulSoup(response.text, 'html.parser')

        total_jobs = soup.find('span', class_='results-context-header__job-count')
        if total_jobs is None:
            app.logger.warning("Could not find total job count. LinkedIn may have changed their HTML structure.")
            return jsonify({"error": "Could not retrieve job information"}), 404

        numbers = re.findall(r'\d+', total_jobs.text)
        if not numbers:
            app.logger.warning(f"Could not extract job count from text: {total_jobs.text}")
            return jsonify({"error": "Could not parse job count"}), 404
        
        total_jobs_count = int(numbers[0])
        page_count = math.ceil(total_jobs_count / 25)

        jobs_list = []
        for page in range(min(page_count, 2)):  # Limit to 2 pages to reduce likelihood of rate limiting
            params['pageNum'] = page
            url = f"{base_url}?{urllib.parse.urlencode(params)}"

            response = make_request(url, session)
            soup = BeautifulSoup(response.text, 'html.parser')

            job_cards = soup.find_all('div', class_='base-card')
            
            for job in job_cards:
                job_data = {}
                job_data['job_title'] = job.find('h3', class_='base-search-card__title').text.strip() if job.find('h3', class_='base-search-card__title') else 'N/A'
                job_data['company_name'] = job.find('h4', class_='base-search-card__subtitle').text.strip() if job.find('h4', class_='base-search-card__subtitle') else 'N/A'
                job_data['location'] = job.find('span', class_='job-search-card__location').text.strip() if job.find('span', class_='job-search-card__location') else 'N/A'
                job_data['link'] = job.find('a', class_='base-card__full-link')['href'] if job.find('a', class_='base-card__full-link') else 'N/A'

                jobs_list.append(job_data)

            time.sleep(random.uniform(5, 10))  # Longer random delay between requests

        return jsonify(jobs_list)

    except Exception as e:
        app.logger.error(f"Error scraping data: {e}")
        abort(500, description="Error scraping LinkedIn data")


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080)