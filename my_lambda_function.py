import requests
import pandas as pd
from bs4 import BeautifulSoup

def lambda_handler(event, context):
    # Fetch a Wikipedia page
    url = "https://en.wikipedia.org/wiki/Web_scraping"
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'lxml')
    
    # Extract titles of the references
    references = soup.find_all('cite', class_='citation')
    titles = [ref.get_text() for ref in references]

    # Convert the titles into a DataFrame
    df = pd.DataFrame(titles, columns=['Reference Titles'])
    
    # Convert the DataFrame to JSON for returning
    result = df.to_json(orient='records')

    return {
        'statusCode': 200,
        'body': result
    }
