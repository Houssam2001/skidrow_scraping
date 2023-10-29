import csv
from flask_cors import CORS  # Import the CORS class

from flask import Flask, jsonify
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# chrome_service = ChromeService("./chromedriver.exe")
# chrome_options = Options()
# chrome_options.headless = False
# driver = webdriver.Chrome(service=chrome_service, options=chrome_options)


def extract_about_game_section(post_details_text):
    about_game_start_index = post_details_text.find("ABOUT THE GAME :") + len("ABOUT THE GAME :")
    about_game_end_index = post_details_text.find("Title:")
    about_game_section = post_details_text[about_game_start_index:about_game_end_index].strip() if about_game_start_index != -1 and about_game_end_index != -1 else ""

    # Split the about game section into key-value pairs
    about_game_lines = about_game_section.splitlines()
    about_game_data = {}
    current_key = None
    for line in about_game_lines:
        if line and ':' in line:
            current_key, current_value = map(str.strip, line.split(':', 1))
            about_game_data[current_key] = current_value
        elif current_key:
            about_game_data[current_key] += '\n' + line

    return about_game_data

# Function to extract information from a post
def extract_post_info(post):
    title = post.find_element(By.TAG_NAME, "h2").text.strip()
    date = post.find_element(By.CLASS_NAME, "meta").text.strip().split(" in ")[0]
    category = post.find_element(By.CLASS_NAME, "meta").find_element(By.TAG_NAME, "a").text.strip()
    image_url = post.find_element(By.CLASS_NAME, "aligncenter").get_attribute("src")
    post_url = post.find_element(By.CLASS_NAME, "more-link").get_attribute("href")
    comments_count = post.find_element(By.CLASS_NAME, "comments-link").text.strip().split()[0]

    # Make a request to the post URL and get the response
    response_post = requests.get(post_url)
    soup_post = BeautifulSoup(response_post.content, "html.parser")

    # Extract all text content within the post details section
    post_details_element = soup_post.find('div', class_='post-extended')  # Adjust the selector as needed
    post_details_text = post_details_element.get_text(separator='\n').strip() if post_details_element else ""
    about_game_header = soup_post.find("h5", string="ABOUT THE GAME :")

    # Initialize about_game variable to store extracted text
    about_game = ""

    # If the header is found, find all <p> tags that appear after it
    if about_game_header:
        about_game_paragraphs = about_game_header.find_all_next("p")

        # Extract text from the <p> tags and join them
        about_game = "\n".join(paragraph.text.strip() for paragraph in about_game_paragraphs)

    # Extract other relevant information similarly
    genre = soup_post.find("strong", string="Genre:").next_sibling.strip() if soup_post.find("strong", string="Genre:") else ""
    developer = soup_post.find("strong", string="Developer:").next_sibling.strip() if soup_post.find("strong", string="Developer:") else ""
    publisher = soup_post.find("strong", string="Publisher:").next_sibling.strip() if soup_post.find("strong", string="Publisher:") else ""
    release_date = soup_post.find("strong", string="Release Date:").next_sibling.strip() if soup_post.find("strong", string="Release Date:") else ""

    # Example: Extract NFO information (assuming it follows a specific pattern)
    nfo_header = soup_post.find("strong", string="NFO:")
    nfo = nfo_header.find_next("div").text.strip() if nfo_header else ""

    # Example: Extract minimum system requirements
    minimum_requirements_header = soup_post.find("strong", string="Minimum:")
    minimum_requirements = minimum_requirements_header.find_next("ul", class_="bb_ul").text.strip() if minimum_requirements_header else ""

    # Example: Extract recommended system requirements
    recommended_requirements_header = soup_post.find("strong", string="Recommended:")
    recommended_requirements = recommended_requirements_header.find_next("ul", class_="bb_ul").text.strip() if recommended_requirements_header else ""


    torrent_url = ""
    magnet_url = ""
    torrent_links = soup_post.find_all("a", href=True, target="_blank")
    for link in torrent_links:
        if "magnet" in link["href"]:
            magnet_url = link["href"]
        elif "pixeldrain" in link["href"]:
            torrent_url = link["href"]
            break


    return title, date, category, image_url, post_url, comments_count, post_details_text, about_game, genre, developer, publisher, release_date, minimum_requirements, recommended_requirements, nfo, magnet_url, torrent_url



app = Flask(__name__)
CORS(app)
def scrape_data_from_page(page_number):
    chrome_service = ChromeService("./chromedriver.exe")
    chrome_options = Options()
    chrome_options.headless = False
    driver = webdriver.Chrome(service=chrome_service, options=chrome_options)

    base_url = f"https://www.skidrow-games.com/page/{page_number}/"
    driver.get(base_url)
    WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.CLASS_NAME, "post")))
    posts = driver.find_elements(By.CLASS_NAME, "post")

    scraped_data = []
    for post in posts:
        try:
            # Extract data from post using existing logic
            title, date, category, image_url, post_url, comments_count, post_details_text, about_game, genre, developer, publisher, release_date, minimum_requirements, recommended_requirements, nfo, magnet_url, torrent_url = extract_post_info(post)

            # Construct a dictionary with the extracted data
            post_data = {
                "Title": title,
                "Date": date,
                "Category": category,
                "Image_URL": image_url,
                "Post_URL": post_url,
                "Comments_Count": comments_count,
                "Post_Details": post_details_text,
                "About_the_Game_Title": about_game,
                "Genre": genre,
                "Developer": developer,
                "Publisher": publisher,
                "Release Date": release_date,
                "Minimum Requirements": minimum_requirements,
                "Recommended Requirements": recommended_requirements,
                "NFO": nfo,
                "Magnet_URL": magnet_url,
                "Torrent_URL": torrent_url
            }
            scraped_data.append(post_data)
        except Exception as e:
            print(f"Error processing post: {e}")

    driver.quit()
    return scraped_data
def extract_data_from_post(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')

    # Extract data from the post page using appropriate HTML tags and classes
    title = soup.find('h2').text.strip()
    date = soup.find('div', class_='meta').text.strip().split(' in ')[0]
    category = soup.find('div', class_='meta').find('a').text.strip()
    image_url = soup.find('img', class_='aligncenter')['src']
    about_game = soup.find('h5', string='ABOUT THE GAME :').find_next('p').text.strip()

    # Extract other relevant information similarly

    # Example: Extract magnet URL
    magnet_url = soup.find('a', href=True, target='_blank', attrs={'href': lambda x: 'magnet' in x})['href']

    # Example: Extract torrent URL
    torrent_url = soup.find('a', href=True, target='_blank', attrs={'href': lambda x: 'pixeldrain' in x})['href']

    # Construct a dictionary with the extracted data
    post_data = {
        "Title": title,
        "Date": date,
        "Category": category,
        "Image_URL": image_url,
        "Post_URL": url,
        "About_the_Game_Title": about_game,
        "Magnet_URL": magnet_url,
        "Torrent_URL": torrent_url
        # Add more data as needed
    }

    return post_data

@app.route('/api/post/<string:post_url>', methods=['GET'])
def get_scraped_data(post_url):
    try:
        base_url = f"https://www.skidrow-games.com/{post_url}/"
        print(base_url)

        scraped_data2 = extract_data_from_post(base_url)
        print(scraped_data2)
        return jsonify({"success": True, "data": scraped_data2})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/scraped_data/<int:page_number>', methods=['GET'])
def get_scraped_data2(page_number):
    try:
        scraped_data = scrape_data_from_page(page_number)
        return jsonify({"success": True, "data": scraped_data})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})
# @app.route('/api/post/<string:page_url>', methods=['GET'])
# def get_post_by_title(page_url):
#     try:
#
#         # Logic to find the post URL based on the provided title
#         # You can implement your own logic to search for the post URL in your data source
#         # For example, you can search in the 'scraped_data' list
#         # Placeholder logic:
#         post_url = f"https://www.skidrow-games.com/scene-investigators-tenoke/"
#
#         if post_url:
#             # Scrape data from the post URL
#             scraped_data = scrape_data_from_post_url(page_url)
#             print(scraped_data)
#             return jsonify({"success": True, "data": scraped_data})
#         else:
#             return jsonify({"success": False, "error": "Post not found"})
#     except Exception as e:
#         return jsonify({"success": False, "error": str(e)})


if __name__ == '__main__':
    app.run(debug=True)