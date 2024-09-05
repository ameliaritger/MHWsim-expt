import datetime

class MEM(object):
    def __init__(self, local_path, external_path):
        self.local_path = local_path
        self.external_path = external_path

        self.dt = datetime.datetime #use this module for getting the date/time

        #self.file_name = "data" + str(self.dt.now()) + ".csv" #construct csv file name using datetime so it is always unique
        self.file_name = "datafile.csv" #construct csv file name using datetime so it is always unique
        self.local_file_name = self.local_path + self.file_name #append to local path
        self.external_file_name = self.external_path + self.file_name #append to external path

        self.local_file = open(self.local_file_name, 'a');
        self.local_file.write('Time,' + 'Tank1 Temp,' + 'Tank2 Temp,' + '\n') #write header to local file
        self.local_file.close()

        self.external_file = open(self.external_file_name, 'a');
        self.external_file.write('Time,' + 'Tank1 Temp,' + 'Tank2 Temp,' + '\n') #write header to external file
        self.external_file.close()

    def save(self, target_temp, measured_temp):
        time = self.dt.now() #get date/time data
        data = str(time) + ',' + str(target_temp) + ',' + str(measured_temp) + ',' #contruct data point

        self.local_file = open(self.local_file_name, 'a');
        self.local_file.write(data + '\n') #write data to local file
        self.local_file.close()

        self.external_file = open(self.external_file_name, 'a');
        self.external_file.write(data + '\n') #write data to external file
        self.external_file.close()
