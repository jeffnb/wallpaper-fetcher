import logging
from imgurpython import ImgurClient
from imgurpython.helpers.error import ImgurClientError


class ImgurWrapper:
    def __init__(self, client_id, client_secret):
        self.__client = ImgurClient(client_id, client_secret)

    @staticmethod
    def is_imgur(url):
        """
        Simple check to see if url is an imgur url
        :param url: ParsedUrl of the
        :return: boolean if it is a imagr or not
        """
        return "imgur.com" in url.hostname

    @staticmethod
    def is_album(url):
        if "/a/" not in url.path:
            return False
        else:
            return True

    def get_image_list(self, url):
        """
        This call is intended to take the url and return a list of all images associated with it.  It will parse
        the image without extension or parse all images.
        :param url: parsed url object
        :return: list of images
        """
        image_list = []
        if self.is_album(url):
            image_list = self.get_album_images(url)
        else:
            image = self.get_image(url)
            if image is not None:
                image_list.append(image)

        return image_list

    def get_image(self, url):
        """
        Get a single image from a url
        :param url: parsed url
        :return: an image or None if exception raised
        """
        image_id = url.path[url.path.rfind("/") + 1 :]
        try:
            image = self.__client.get_image(image_id)
        except ImgurClientError as e:
            logging.error(
                "Status Code: " + e.status_code + " Error: " + e.error_message
            )
            image = None

        return image

    def get_album_images(self, url):
        """
        Gets all the images in an album as a list of image objects
        :param url: parsed url
        :return: Either a list of images or an empty list
        """
        album_id = url.path[url.path.rfind("/") + 1 :]
        image_list = []

        try:
            images = self.__client.get_album_images(album_id)
        except ImgurClientError as e:
            logging.error(
                "Status Code: " + str(e.status_code) + " Error: " + e.error_message
            )
        else:
            image_list = images

        return image_list
