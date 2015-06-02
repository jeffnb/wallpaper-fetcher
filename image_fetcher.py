from Queue import Queue
import logging
import os
from threading import Thread
import urllib
from PIL import Image


class ImageFetcher:

    __queue = Queue(1000)

    def __init__(self, thread_count, min_width, min_height):
        """
        Set up all the defaults for the fetcher and then kick off threads to start monitoring the queue
        :param thread_count: How many threads should be created to process the images
        :param min_width: minimum width for images to remanin after download
        :param min_height: minimum height for image to remain after download
        :return: void
        """
        self.__min_width = min_width
        self.__min_height = min_height
        self.__setup_threads(thread_count)

    def __download_image(self, thread_name):
        """
        Main execution method for image downloading
        :param thread_name:
        :return:
        """
        while True:
            logging.debug("%s: Looking for next image" % thread_name)
            url, destination = self.__queue.get()
            logging.debug("%s: Getting image %s" % (thread_name, destination))
            self.save_and_check_image(url, destination)
            self.__queue.task_done()
            logging.debug("%s: Task complete" % thread_name)

    def __setup_threads(self, thread_count):
        """
        Simply spins up the requested number of threads to process the queue of images
        :param thread_count: total number of threads to create
        :return:
        """
        for i in xrange(0, thread_count):
            worker = Thread(target=self.__download_image, args=("Thread-%d" % i,))
            worker.daemon = True
            worker.start()

    def wait_to_finish(self):
        """ Simple passthrough method to abstract out waiting for the queue """
        logging.debug("Waiting for threads to finish")
        self.__queue.join()

    def queue_image(self, url, destination):
        """
        Simple passthrough method to put a tuple onto the queue for processing and downloads
        :param url: url to fetch
        :param destination: path and filename for where to store the image
        :return:
        """
        self.__queue.put((url, destination))
        logging.debug("Added to queue making total: %d" % self.__queue.qsize())

    def filter_image_size(self, location):
        """
        Simple method to make sure small images are not saved.
        :param location: path and filename of the image location
        :return:
        """
        img = Image.open(location)
        (width, height) = img.size

        if width < self.__min_width or height < self.__min_height:
            logging.info("File saved then removed due to size:" + location)
            os.remove(location)

    def save_and_check_image(self, url, destination):
        """
        Pulls the image down and calls out to check the image size
        :param url: http location to fetch
        :param destination: directory/filename location to save file
        :return:
        """
        try:
            urllib.urlretrieve(url, destination)
        except Exception as e:
            logging.error(e.message)
        else:
            self.filter_image_size(destination)
