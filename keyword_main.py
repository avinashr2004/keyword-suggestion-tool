import requests
from bs4 import BeautifulSoup
from sklearn.feature_extraction.text import TfidfVectorizer
import nltk
from nltk.corpus import stopwords
import re
import os # <-- IMPORT OS
from dotenv import load_dotenv # <-- IMPORT DOTENV

# --- LOAD KEYS FROM .env FILE ---
load_dotenv() # This loads the .env file
API_KEY = os.getenv("API_KEY")
SEARCH_ENGINE_ID = os.getenv("SEARCH_ENGINE_ID")
# ---------------------------------

# This line downloads the stopwords list
nltk.download('stopwords')

def fetch_blog_text(url):
    """Fetches and extracts all paragraph text from a blog URL."""
    print(f"Fetching blog content from: {url}")
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status() 
        soup = BeautifulSoup(response.text, 'html.parser')
        paragraphs = soup.find_all('p')
        text = ' '.join(p.get_text() for p in paragraphs)
        return text
    except requests.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return "" 

def extract_keywords(text, top_n=20):
    """Extracts top N keywords from text using TF-IDF."""
    text = re.sub('[^a-zA-Z ]', '', text).lower()
    stop_words = stopwords.words('english')
    
    if not text.strip():
        return [] 
        
    try:
        vectorizer = TfidfVectorizer(stop_words=stop_words, ngram_range=(1,2))
        tfidf_matrix = vectorizer.fit_transform([text])
        feature_names = vectorizer.get_feature_names_out()
        scores = tfidf_matrix.toarray()[0]
        keywords = sorted(zip(feature_names, scores), key=lambda x: x[1], reverse=True)
        return [kw for kw, score in keywords[:top_n]]
    except ValueError as e:
        print(f"Warning: Could not extract keywords. {e}")
        return []

def fetch_blog_title(url):
    """Fetches the <title> tag text from a URL."""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        title = soup.find('title').get_text() if soup.find('title') else ''
        return title
    except requests.RequestException as e:
        print(f"Error fetching title from {url}: {e}")
        return "" 

def get_top_google_results(query, num_results=10):
    """Gets top N Google search results using the official API."""
    print(f"Searching Google for: {query}")
    
    url = "https://www.googleapis.com/customsearch/v1"
    
    params = {
        'key': API_KEY,
        'cx': SEARCH_ENGINE_ID,
        'q': query,
        'num': num_results
    }
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        
        if 'items' in data:
            return [item['link'] for item in data['items']]
        else:
            print("Warning: Google API returned no items.")
            return []
            
    except requests.RequestException as e:
        print(f"Error during Google API search: {e}")
        if response:
            print("Response text:", response.text)
        return []

def suggest_new_keywords(existing_keywords, related_blogs_keywords):
    """Compares keyword lists and suggests new ones."""
    existing_set = set(existing_keywords)
    all_related = set()
    
    for kw_list in related_blogs_keywords:
        all_related.update(kw_list)
        
    new_keywords = all_related - existing_set
    return list(new_keywords)

def main():
    """Main function to run the keyword suggestion process."""
    
    if not API_KEY or not SEARCH_ENGINE_ID:
        print("!!! ERROR: API_KEY or SEARCH_ENGINE_ID not found.")
        print("Please make sure you have a .env file with your keys.")
        return
        
    blog_url = input("Enter the blog URL: ")
    
    blog_text = fetch_blog_text(blog_url)
    if not blog_text:
        print("Could not fetch content from the URL. Exiting.")
        return
        
    existing_keywords = extract_keywords(blog_text)
    print("\n--- Existing Keywords in your blog ---")
    print(existing_keywords)
    
    blog_topic = fetch_blog_title(blog_url)
    if not blog_topic:
        print("Could not fetch blog title. Using a fallback query.")
        blog_topic = "related topics for " + blog_url
        
    print("\n--- Detected blog topic/title ---")
    print(blog_topic)
    
    related_blog_urls = get_top_google_results(blog_topic)
    print("\n--- Top related blog URLs from Google ---")
    for url in related_blog_urls:
        print(url)
        
    related_keywords_all = []
    print("\n--- Analyzing competitor blogs... ---")
    for url in related_blog_urls:
        if url == blog_url:
            print(f"Skipping original blog URL: {url}")
            continue 
            
        try:
            text = fetch_blog_text(url)
            if len(text.strip()) < 100: 
                print(f"Skipping {url} due to insufficient content")
                continue
            kws = extract_keywords(text)
            related_keywords_all.append(kws)
        except Exception as e:
            print(f"Skipping {url} due to error: {e}")
            
    new_suggestions = suggest_new_keywords(existing_keywords, related_keywords_all)
    print("\n==========================================")
    print("--- 💡 Suggested New Keywords for your blog ---")
    print("==========================================")
    if new_suggestions:
        print(new_suggestions)
    else:
        print("No new keywords found.")

if __name__ == '__main__':
    main()