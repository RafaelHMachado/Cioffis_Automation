import os
import csv
import openpyxl
import pandas as pd
from datetime import datetime, timezone, timedelta
from dateutil import tz
import pytz
import tzlocal
import time

class csvDataSelector():
    """
        ** Contains one function that grabs all the data from a CSV file. **

        :param:
        :return:
    """
    def __init__(self, filename):
        """
            ** Writes a page of information to a CSV file. **

            :param: filename - Name of the CSV file
            :return:
        """
        with open(filename, 'r') as f_input:
            csv_input = csv.reader(f_input)
            self.details = list(csv_input)

            #for row in csv_input:
            #   self.details.join(row)

    def csv_standalone():
        with open('Stop_Report_10_27_2020.csv') as stop_report:
            stop_report = stop_report.read()

class csvDataPlacer():
    """
        ** Contains one function that writes a page of information to a CSV file. **

        :param:
        :return:
    """
    def __init__(self, filename, information):
        """
            ** Writes a page of information to a CSV file. **

            :param: filename - Name of the CSV file
                    information - The information to write to the CSV file
            :return:
        """
        with open(filename, 'w') as f_input:
            csv_input = csv.writer(f_input, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
            csv_input.writerow(information)

class fromXL():
    """
        ** Contains a couple functions that grab data from XLSX files. **

        :param:
        :return:
    """
    def select_column(self, description, sheet, column):
        """
            ** Selects a specific column from the XLSX file. **

            :param: description - Name of the XLSX file
                    sheet - The specific sheet specified to pull the column from
                    column - The specific column to get
            :return: df - returns a data frame with the column data pulled
        """
        xlsx = pd.read_excel('%s.xlsx' % description, sheet_name=sheet, usecols=column)
        df = pd.DataFrame(xlsx)
        return df

    def extract_info(self, data, remove_string, replace_string):
        """
            ** Gets specific data from a DataFrame, removing a string. **

                Takes the data from a Data Frame inserted and then applies it to its own standalone Data Frame. Then
                cycles through each value, looking for the string and replacing it with nothing.

            :param: data - The Data Frame on which to take the string out of the values.
                    remove_string - The single section of string that matches this variable is removed from the values.
            :return: list - Returns the list of values with the string removed.
        """
        if type(data) is str:
            df = data
            list = []
            for i in df:
                for j in i:
                    j = j.replace(remove_string, replace_string)
                    list.append(j)
        else:
            df = data.values
            list = []
            for i in df:
                for j in i:
                    j = j.replace(remove_string,replace_string)
                    list.append(j)
        return list

    def list_to_string(self, list):
        """
            ** Getting a list of strings and concatenates them. **

                Takes the data from a Data Frame inserted and then applies it to its own standalone Data Frame. Then
                cycles through each value, looking for the string and replacing it with nothing.

            :param: list - (list) The list to concatenate
            :return: string - (string) the concatenated list as a string
        """
        string = ''.join(list)
        return string


class time_handler():
    def day_start(self):
        """
            ** Gives current day start. **

                Grabs todays date in Unix UTC time mode, than converts it to our time zone and into a human readable
                format.

            :param: No input. (TODO: Could change this to select a date to report and return that)
            :return: readable_time - (string) is the start of the day converted to human understanding
        """
        # Get Today's full day time
        today = tzlocal.get_localzone().localize(datetime.now())
        day_start = tzlocal.get_localzone().localize(datetime(today.year, today.month, today.day))
        utc_dt = day_start.astimezone(pytz.utc)
        unixtime = int(time.mktime(utc_dt.timetuple()))
        readable_time = day_start.strftime('%Y-%m-%d %H:%M:%S')
        return unixtime

    def current_time(self):
        """
            ** Gives current time. **

                Gets the current time in Unix UTC time. Then converts it to our timezone and changes the format to a
                human readable time.

            :param: No input.
            :return: readable_time - (string) is the current time converted to human readable time
        """
        # Get Current time
        current_time = tzlocal.get_localzone().localize(datetime.now())
        utc_dt = current_time.astimezone(pytz.utc)
        unixtime = int(time.mktime(utc_dt.timetuple()))
        readable_time = current_time.strftime('%Y-%m-%d %H:%M:%S')
        return unixtime

    def human_time(self, time_stamp):
        """
            ** Translates second time to human readability down to seconds. **

                Grabs the time-stamp that is sent in (Unix UTC time). It then translates the time to our time zone
                (subtract 8 hours, 28800 seconds) and gives back the human readable time. This function is used widely
                throught this project.

            :param: time_stamp - (integer) takes in the Unix UTC time wanted to be converted
            :return: readable_time - (string) gives the human readable time in '%Y-%m-%d %H:%M:%S'
        """
        readable_time = tzlocal.get_localzone().localize(datetime.fromtimestamp(time_stamp)).strftime('%Y-%m-%d %H:%M:%S')
        return readable_time

    def human_date(self, time_stamp):
        """
            ** Translates second time to human readability down to day. **

                Grabs the time-stamp that is sent in (Unix UTC time). It then translates the time to our time zone
                (subtract 8 hours, 28800 seconds) and gives back the human readable time. This function is used widely
                throught this project.

            :param: time_stamp - (integer) takes in the Unix UTC time wanted to be converted
            :return: readable_time - (string) gives the human readable time in '%Y-%m-%d'
        """
        readable_time = tzlocal.get_localzone().localize(datetime.fromtimestamp(time_stamp)).strftime('%Y-%m-%d')
        return readable_time

    def unix_time(self, time_stamp):
        """
            ** Takes the Unix UTC time stamp and converts it to Unix Pacific time zone **

                Grabs the time-stamp that is sent in (Unix UTC time). It then translates the time to our time zone.

            :param: time_stamp - (integer) takes in the Unix UTC time wanted to be converted
            :return: unix_timestamp - (integer) gives the Unix Pacific time in seconds
        """
        unixtime = int(tzlocal.get_localzone().localize(time.mktime(time_stamp.timetuple())))
        print(unixtime)
        return unixtime

    def seconds_to_time_conv(self, time_stamp):
        """
            ** Translates second time to human readability. **

                Grabs the time-stamp that is represented in seconds, sent in (Unix UTC time). It takes the seconds and
                gives back the human readable time.

            :param: time_stamp - (integer) takes in the Unix UTC time in seconds wanted to be converted
            :return: readable_time - (string) gives the human readable time in '%Y-%m-%d %H:%M:%S'
        """
        readable_time = timedelta(seconds = time_stamp)
        return readable_time

if __name__ == "__csv_handling__":
    csv_standalone()