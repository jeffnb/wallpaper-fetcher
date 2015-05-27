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
from imgur_wrapper import ImgurWrapper
from saved_submissions import SavedSubmissions

config = ConfigParser.ConfigParser()
config.read('settings.cfg')

sr_name = config.get('reddit', 'subreddit_name')
client_id = config.get('imgur', 'imgur_client_id')
client_secret = config.get('imgur', 'imgur_client_secret')
directory = config.get('store', 'store_directory')
min_width = config.get('store', 'min_width')
min_height = config.get('store', 'min_height')

image_suffixes = ('.jpg', '.png', '.gif')

def main():
    logging.basicConfig(format='%(asctime)s: %(levelname)s: %(message)s', filename='wallpapers.log', level=logging.INFO)
    logging.info("************************************ Script Starting *********************************************")

    saved_submissions = SavedSubmissions()

    imgur_wrapper = ImgurWrapper(client_id, client_secret)

    r = praw.Reddit("Omnibot-Parsing for natual language")
    subreddit = r.get_subreddit(sr_name)

    submissions = subreddit.get_hot(limit=100)

    # Main block of processing for all images
    for submission in submissions:

        url = urlparse(submission.url)
        logging.debug("Processing url: "+submission.url);

        if saved_submissions.find_duplicate(submission.name):
            logging.debug("Submission seen before...skipping")
            continue

        saved_submissions.save_submission(submission.name, submission.title)

        # Let's see if it is an image directly
        if url.path.endswith(image_suffixes):
            name = slugify(submission.title)+'-'+submission.name+getSuffix(submission.url)
            save_and_check_image(submission.url, name)
        elif imgur_wrapper.is_imgur(url):
            logging.info("Found an imgur url")
            images = imgur_wrapper.get_image_list(url)
            for image in images:
                logging.debug("Processing image: %s" % image.title)
                filename = ""

                # Title is blank back up to reddit title
                if image.title is None:
                    filename = slugify(submission.title)+"-"+image.id + getSuffix(image.link)
                else:
                    filename = slugify(image.title)+"-"+image.id + getSuffix(image.link)

                logging.info("Getting album file: " + image.link)
                save_and_check_image(image.link, filename)

        else: # Non-imgur link without an extension. Cannot determine
            logging.info("non image non imgur. Skip permanently")


def getSuffix(imagename):
    return imagename[imagename.rfind('.'):]

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
    except Exception as e:
        logging.error(e.error_message)
    else:
        filter_image_size(location)



if __name__ == "__main__":
    main()