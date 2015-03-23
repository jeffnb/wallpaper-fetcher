import ConfigParser
import datetime
import os
from urlparse import urlparse
from PIL import Image
from imgurpython.helpers.error import ImgurClientError
import praw
from slugify import slugify
import sqlite3
import logging
from imgurpython import ImgurClient
import urllib


config = ConfigParser.ConfigParser()
config.read('settings.cfg')

sr_name = config.get('reddit', 'subreddit_name')
client_id = config.get('imgur', 'imgur_client_id')
client_secret = config.get('imgur', 'imgur_client_secret')
directory = config.get('store', 'store_directory')
min_width = config.get('store', 'min_width')
min_height = config.get('store', 'min_height')


def main():

    #Set up sqlite
    conn = sqlite3.connect(os.path.dirname(os.path.realpath(__file__))+'/reddit.db')
    cursor = conn.cursor()

    client = ImgurClient(client_id, client_secret)

    r = praw.Reddit("Omnibot-Parsing for natual language")
    subreddit = r.get_subreddit(sr_name)
    logging.basicConfig(format='%(asctime)s: %(levelname)s: %(message)s', filename='wallpapers.log', level=logging.INFO)
    logging.info("************************************************** Script Starting ********************************************************")
    submissions = subreddit.get_hot(limit=100)

    for submission in submissions:

        url = urlparse(submission.url)
        logging.debug("Processing url: "+submission.url);

        #pull submission id
        params = (submission.name,)
        cursor.execute("select * from submissions where id=?", params)

        #Look to see if we have already gotten a submission
        result = cursor.fetchone()
        if result is not None:
            logging.debug("Submission seen before...skipping")
            continue

        #store the fact we have looked at the submission
        now = datetime.datetime.now()
        params = (submission.name, now.strftime("%c"), 'false')
        cursor.execute("INSERT INTO submissions VALUES(?,?,?)", params)
        conn.commit()

        #quickly get if imgur is involved
        is_imgur = 'imgur.com' in url.hostname

        #Let's see if it is an image directly
        if getSuffix(url.path) in ['.jpg', '.png', '.gif']:
            name = slugify(submission.title)+'-'+submission.name+getSuffix(submission.url)
            save_and_check_image(submission.url, name)
        elif is_imgur and '/a/' not in url.path:#imgur link without an extention
            logging.info("Extention missing on an imgur picture...adding")
            image_id = url.path[url.path.rfind('/')+1:]
            try:
                image = client.get_image(image_id)
            except ImgurClientError as e:
                logging.error("Status Code: " + e.status_code + " Error: " + e.error_message)
                continue
            link = image.link
            suffix = getSuffix(link)


            name = slugify(submission.title)+'-'+submission.name+suffix
            logging.info("Slugified name: " + name)

            save_and_check_image(link, name)
        elif not is_imgur: #non-imgur link without an extension
            logging.info("non image non imgur. Skip permanently")
        elif '/a/' in url.path: #Imgur album
            logging.info("found an album")
            album_id = url.path[url.path.rfind('/')+1:]

            try:
                images = client.get_album_images(album_id)
            except ImgurClientError as e:
                logging.error("Status Code: " + e.status_code + " Error: " + e.error_message)

            for image in images:
                filename = ""

                #Title is blank back up to reddit title
                if image.title is None:
                    filename = slugify(submission.title)+"-"+image.id + getSuffix(image.link)
                else:
                    filename = slugify(image.title)+"-"+image.id + getSuffix(image.link)

                logging.info("Getting album file: " + image.link)
                save_and_check_image(image.link, filename)
    conn.close()


def getSuffix(imagename):
    return imagename[-4:]

def filter_image_size(location):
    """
    Simple method to make sure small images are not saved.
    """
    img = Image.open(location)
    (width, height) = img.size

    if width < 1400 or height < 900:
        logging.info("File saved then removed due to size:" + location)
        os.remove(location)


def save_and_check_image(url, name):
    """
    Pulls the image down and calls out to check the image size
    """
    location = directory+name
    try:
        urllib.urlretrieve(url, location)
        filter_image_size(location)
    except Exception as e:
        logging.error(e.error_message)


if __name__ == "__main__":
    main()