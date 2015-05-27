import logging
import os
import sqlite3


class SavedSubmissions:

    def __init__(self):
        self.__conn = sqlite3.connect(os.path.dirname(os.path.realpath(__file__))+'/reddit.db')
        self.__cursor = self.__conn.cursor()

    def find_duplicate(self, submission_id):
        """
        Do a simple query to determin if there are records already in the db for the given id
        :param id: the unique id to search for
        :return: boolean representing if the duplicate was found
        """
        found = False

        params = (submission_id,)
        self.__cursor.execute("select * from submissions where id=?", params)

        result = self.__cursor.fetchone()
        if result is not None:
            logging.debug("Submission seen before...skipping")
            found = True

        return found

    def save_submission(self, submission_id, title):
        """
        Save a simple record into the database.
        :param submission_id: the unique id to save
        :param title: plain title
        :return:
        """
        params = (submission_id, title, )
        self.__cursor.execute("INSERT INTO submissions (id, name) VALUES(?,?)", params)
        self.__conn.commit()

    def __del__(self):
        self.__cursor.close()
        self.__conn.close()