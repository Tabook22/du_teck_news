import os
import requests
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def search_news(query, num_results=10, restrict_timeframe=None):
    # Fetching Google API key and Search Engine ID from environment variables
    api_key = os.getenv("GOOGLE_API_KEY")
    search_engine_id = os.getenv("SEARCH_ENGINE_ID")
    
    # Construct the Google Custom Search API URL
    url = f"https://www.googleapis.com/customsearch/v1?q={query}&num={num_results}&key={api_key}&cx={search_engine_id}"
    
    # If we want to restrict the search based on the selected timeframe
    if restrict_timeframe:
        url += f"&dateRestrict={restrict_timeframe}"

    # Making the request to the API
    response = requests.get(url)
    
    # Debugging: Print the API URL and response status
    print(f"Request URL: {url}")
    print(f"API Response Status Code: {response.status_code}")
    print(f"API Response Content: {response.text}")

    if response.status_code == 200:
        results = response.json()

        # Check if 'items' exists in the response
        if 'items' not in results:
            print("No 'items' found in the response.")
            return []

        # Extract news items
        news_items = []
        for item in results['items']:
            # Extract general information like title, summary, and fallback link
            news = {
                'title': item.get('title', 'No Title'),
                'image_url': item.get('pagemap', {}).get('cse_image', [{}])[0].get('src', 'No Image'),
                'summary': item.get('snippet', 'No Summary'),
                'link': item.get('link', 'No Link')  # Fallback link
            }

            # Try to find a more specific article URL from metatags or other structured data in 'pagemap'
            metatags = item.get('pagemap', {}).get('metatags', [{}])
            if metatags:
                specific_url = metatags[0].get('og:url') or metatags[0].get('twitter:url')
                if specific_url:
                    news['link'] = specific_url  # Use specific URL if available

            # Debugging: Print the final link
            print(f"Final News Link: {news['link']}")

            # Add to the list of news items
            news_items.append(news)

        return news_items
    else:
        print(f"Failed to fetch news data. Status code: {response.status_code}")
        return []
