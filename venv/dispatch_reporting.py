import os
import json
import xlsxwriter
import pandas as pd
import math

from datetime import datetime, timezone
from dateutil import tz
import csv

from nero import neroApi
from environment_handling import fromXL, time_handler

class DispatchReportingFolderSetup():
    """
        ** Sets up the folder system for dispatch reporting and the required data. **

        -> Dispatch Reporting
            -> Nero_Data
            -> Report_CSV
            -> Email_List
        :param:
        :return:
    """
    def __init__(self):
        """
            ** Initializes Folder Hierarchy **
                Checks to see if each file already exists; then creates all missing folders. Specifically it creates a
                folder for Dispatch Reporting, Nero Data, CSV Reporting and Email List.

            :return:
        """
        os.chdir('../venv')
        path = os.getcwd()
        if os.path.isdir(path + '/' + 'Dispatch_Reporting'):
            print('Dispatch Reporting folder already created')
            os.chdir(path + '/' + 'Dispatch_Reporting')
            path = os.getcwd()
            if os.path.isdir(path + '/' + 'Nero_Data'):
                print('Nero Data folder is already created')
            else:
                self.create_nero_data_folder()
            if os.path.isdir(path + '/' + 'Report_CSV'):
                print('Report_CSV folder already created')
            else:
                self.create_report_csv_folder()
            if os.path.isdir(path + '/' + 'Email_List'):
                print('Email_List folder already created')
            else:
                self.create_email_list_folder()
        else:
            self.create_dispatch_reporting_folder(path)

    def create_dispatch_reporting_folder(self, path):
        """
            ** Dispatch Reporting Folder Creation **

                Creates the Dispatch_Reporting upper level folder and then creates all of the sub-folders.

        :param path:
        :return:
        """
        try:
            os.mkdir('Dispatch_Reporting')
        except OSError:
            print('Failed to create Dispatch_Reporting folder')
        else:
            print('Successfully created the Dispatch_Reporting directory')
            os.chdir(path + '/' + 'Dispatch_Reporting')
            self.create_nero_data_folder()
            self.create_report_csv_folder()
            self.create_email_list_folder()

    def create_nero_data_folder(self):
        """
            ** Creates Nero_Data folder **

                Stores the data that is pulled from Nero.

            :return:
        """
        try:
            os.mkdir('Nero_Data')
        except OSError:
            raise('Creating Nero_Data failed.')
        else:
            print('Successfully created Nero_Data folder.')

    def create_report_csv_folder(self):
        """
            ** Creates Report_CSV folder **

                Stores the data that is sorted into CSV files.

            :return:
        """
        try:
            os.mkdir('Report_CSV')
        except OSError:
            raise('Creating Report_CSV failed.')
        else:
            print('Successfully created Report_CSV folder.')

    def create_email_list_folder(self):
        """
            ** Creates Email_List folder **

                Stores the contact/email list that the reports should be sent to.

            :return:
        """
        try:
            os.mkdir('Email_List')
        except OSError:
            raise('Creating Email_List failed.')
        else:
            print('Successfully created Email_List folder.')

class ReportConstruction():
    """
        ** Contains the functions which will construct the Dispatch Reporting XLSX/CSV. **

        TODO: CLEAN!!!

        :param:
        :return:
    """
    def __init__(self):
        """
            ** Pieces together and grabs the specific parts of the report. All the data is grabbed from already saved
                CSV/XLSX/JSON files (This could be modified by utalizing temp files so that space isn't an issue). **

            TODO: CLEAN!!!

            :param:
            :return:
        """
        # Load times
        # Stop times for trucks that moved today
        # Run times for trucks that moved today

        # Future report ideas:
        # Longevity report
        # Location Related time

        os.chdir('../Nero_Data')

        # Grab vehicle list
        xlsx_name = 'vehicle_list'
        sheet = 'Data_Columns'
        column = 'A'
        vehicle_dataframe = fromXL().select_column(xlsx_name, sheet, column)
        remove_string = 'https://nero.contigo.com/dex/08/1/dept/6162/vehicle/'
        replace_string = ''
        vehicle_list = fromXL.extract_info(self, vehicle_dataframe, remove_string, replace_string)

        # Grab vehicle name
        xlsx_name = 'vehicle_list'
        sheet = 'Data_Columns'
        column = 'B'
        vehicle_namelist = neroApi.name_extraction(self, xlsx_name, sheet, column)

        os.chdir('../Report_CSV')
        workbook = xlsxwriter.Workbook('Driver_Report.xlsx')
        worksheet = workbook.add_worksheet('Stop_Times')

        row = 0
        col = 0

        count = 0
        for vehicleID, vehicleName in zip(vehicle_list, vehicle_namelist):
            os.chdir('../Nero_Data')
            # Create new DataFrame
            df = pd.DataFrame(columns=[vehicleID, 'networkTs', 'landmark', 'address'])

            json_name = 'events' + str(vehicleName)

            with open('%s.json' % json_name) as f:
                data_json = json.load(f)

            os.chdir('../Report_CSV')

            # Write the Vehicle Name
            worksheet.write(row, col, vehicleName)
            row += 1

            # The headers to a spreadsheet
            worksheet.write(row, col, 'networkTs')
            worksheet.write(row, col + 1, 'Time Spent')
            # worksheet.write(row, col + 2, 'Speed')
            worksheet.write(row, col + 3, 'Landmark')
            # worksheet.write(row, col + 4, 'Address')
            # worksheet.write(row, col + 4, 'Latitude')
            # worksheet.write(row, col + 5, 'Longitude')

            row += 1
            col = 0
            event_num = 0
            prev_time = 0

            for event in data_json['eventList']:
                count = count + 1

                time_stamp = int(event['networkTs'])
                readable_time = time_handler.human_time(self, time_stamp)

                if event_num == 0:
                    init_time = time_handler.day_start(self)
                    diff_time = time_stamp - init_time
                    diff_time = time_handler.seconds_to_time_conv(self, diff_time)
                else:
                    diff_stamp = time_stamp - prev_time
                    diff_time = time_handler.seconds_to_time_conv(self, diff_stamp)

                prev_time = time_stamp

                # Converting time string into an integer
                diff_seconds = diff_time.seconds

                # Checking Stop times over 15 min
                speed = int(event['speed'])
                if speed == 0 and diff_seconds >= 900:
                    #Landmark Location Check
                    os.chdir('../Nero_Data')
                    vehicle_lat = str(event['lat'])
                    vehicle_lon = str(event['lon'])

                    landmark_file = 'landmark_csv.csv'
                    remove_string = '['
                    remove_string2 = ']'
                    replace_string = ''
                    with open(landmark_file, 'r') as read_obj:
                        csv_reader = csv.reader(read_obj, delimiter=',')
                        header_check = 0
                        landmark_df = pd.DataFrame(columns = ['landmark', 'lon', 'lat', 'meters'])
                        for row_line in csv_reader:
                            if header_check != 0:
                                landmark = fromXL.extract_info(self, row_line[1], remove_string, replace_string)
                                landmark = fromXL.list_to_string(self, landmark)
                                landmark = fromXL.extract_info(self, landmark, remove_string2, replace_string)
                                landmark = fromXL.list_to_string(self, landmark)
                                lon = fromXL.extract_info(self, row_line[8], remove_string, replace_string)
                                lon = fromXL.list_to_string(self, lon)
                                lon = fromXL.extract_info(self, lon, remove_string2, replace_string)
                                lon = fromXL.list_to_string(self, lon)
                                lon = fromXL.extract_info(self, lon, '\'', replace_string)
                                lon = fromXL.list_to_string(self, lon)
                                lat = fromXL.extract_info(self, row_line[9], remove_string, replace_string)
                                lat = fromXL.list_to_string(self, lat)
                                lat = fromXL.extract_info(self, lat, remove_string2, replace_string)
                                lat = fromXL.list_to_string(self, lat)
                                lat = fromXL.extract_info(self, lat, '\'', replace_string)
                                lat = fromXL.list_to_string(self, lat)
                                meters = float(self.distance_of_two_points_on_sphere(float(lat), float(lon), event['lat'], event['lon']))
                                landmark_info = [{'landmark':landmark, 'lon':lon, 'lat':lat, 'meters':meters}]
                                if meters <= 200:
                                    landmark_df = landmark_df.append(landmark_info)
                            header_check += 1
                        if landmark_df.empty:
                            0
                            stopped_at_landmark = ""
                        else:
                            closest_landmark =  landmark_df[landmark_df['meters'] == landmark_df['meters'].min()]
                            stopped_at_landmark = closest_landmark['landmark'].get(0,1)
                    os.chdir('../Report_CSV')

                    # Add Row of information to XLSX sheet
                    """ TODO fix date/time based on timezone/saving lights time """
                    worksheet.write(row, col, str(readable_time))
                    """ TODO fix spend time considering loading time """
                    worksheet.write(row, col + 1, str(diff_time))
                    #worksheet.write(row, col + 2, str(speed))
                    """ TODO: Include landmark location based on either van turned off or/and sitting longer than 1 minute """
                    worksheet.write(row, col + 3, str(stopped_at_landmark))
                    #worksheet.write(row, col + 4, str(event['address']))
                    #worksheet.write(row, col + 4, str(event['lat']))
                    #worksheet.write(row, col + 5, str(event['lon']))

                    row += 1
                event_num += 1

        workbook.close()

    def distance_of_two_points_on_sphere(self, lat1, lon1, lat2, lon2):
        """
            ** Will compare the longitude and latitude of two points on a sphere. **

            For the general purpose this is used for the vehicle compared to any landmark distance. In the end, it
            returns the distance between the two points in meters. The algorithm used is the Haversine algorithm, if you
            would like to improve the accuracy of this function add a third dimension using altitude, but you would have
            to contact Nero to pull that information.

            WARNING: This algorithm assumes a smooth sphere and does not take into account altitude/elevation change.

            :param: lat1 - The latitude of the first point you want to compare.
                    lon1 - The longitude of the first point you want to compare.
                    lat2 - The latitude of the second point you want to compare.
                    lon2 - The longitude of the second point you want to compare.
            :return: meters - The distance between the two longitude and latitude points given in meters
        """
        # Currently this is calculating the distance on the surface of a sphere
        radius = 6378.137 # The radius of the earth in km
        # differences in Latitude and Longitude
        dLat = lat2 * math.pi/180 - lat1 * math.pi/180
        dLon = lon2 * math.pi/180 - lon1 * math.pi/180
        # Haversine Calculation
        a = math.sin(dLat/2) * math.sin(dLat/2) + math.cos(lat1 * math.pi/180) * math.cos(lat2 * math.pi/180) \
            * math.cos(lat2 * math.pi/180) * math.sin(dLon/2) * math.sin(dLon/2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        d = radius * c
        meters = d * 1000 # Convert km to meters
        return meters

def dispatch_reporting():
    """
        ** Runs through the Dispatch Reporting steps. **

            -> Dispatch Reporting
                -> Folder setup
                -> Grabs data from NeroAPI
                -> Constructs the report from the data

        :param:
        :return:
    """
    # Setup Folder Hierarchy
    DispatchReportingFolderSetup()

    # Grabbing the Nero API
    neroApi()

    # Create Report
    ReportConstruction()

if __name__ == "__dispatch_reporting__":
    dispatch_reporting()