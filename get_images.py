import ConfigParser
import os
from urlparse import urlparse
import logging
import urllib

from PIL import Image
import praw
from slugify import slugify
from image_fetcher import ImageFetcher

from imgur_wrapper import ImgurWrapper
from saved_submissions import SavedSubmissions

config = ConfigParser.SafeConfigParser()
config.read('settings.cfg')

sr_name = config.get('reddit', 'subreddit_name')
client_id = config.get('imgur', 'imgur_client_id')
client_secret = config.get('imgur', 'imgur_client_secret')
directory = config.get('store', 'store_directory')
min_width = config.getint('store', 'min_width')
min_height = config.getint('store', 'min_height')
thread_count = config.getint('store', 'thread_count')

image_suffixes = ('.jpg', '.png', '.gif')


def main():
    logging.basicConfig(format='%(asctime)s: %(levelname)s: %(message)s', filename='wallpapers.log', level=logging.INFO)
    logging.info("************************************ Script Starting *********************************************")

    saved_submissions = SavedSubmissions()

    imgur_wrapper = ImgurWrapper(client_id, client_secret)
    image_fetcher = ImageFetcher(thread_count, min_width, min_height)

    r = praw.Reddit("Omnibot-Wallpaper Fetcher")
    subreddit = r.get_subreddit(sr_name)

    submissions = subreddit.get_hot(limit=100)

    # Main block of processing for all images
    for submission in submissions:

        url = urlparse(submission.url)
        logging.debug("Processing url: "+submission.url)

        if saved_submissions.find_duplicate(submission.name):
            logging.debug("Submission seen before...skipping")
            continue

        saved_submissions.save_submission(submission.name, submission.title)

        # Let's see if it is an image directly
        if url.path.endswith(image_suffixes):
            name = slugify(submission.title)+'-'+submission.name+get_suffix(submission.url)
            image_fetcher.queue_image(submission.url, directory+name)
        elif imgur_wrapper.is_imgur(url):
            logging.info("Found an imgur url")
            images = imgur_wrapper.get_image_list(url)
            for image in images:
                logging.debug("Processing image: %s" % image.title)

                # Title is blank back up to reddit title
                if image.title is None:
                    filename = slugify(submission.title)+"-"+image.id + get_suffix(image.link)
                else:
                    filename = slugify(image.title)+"-"+image.id + get_suffix(image.link)

                logging.info("Getting imgur file: " + image.link)
                image_fetcher.queue_image(image.link, directory+filename)

        else:  # Non-imgur link without an extension. Cannot determine
            logging.info("non image non imgur. Skip permanently")

    image_fetcher.wait_to_finish()

def get_suffix(imagename):
    return imagename[imagename.rfind('.'):]



if __name__ == "__main__":
    main()
