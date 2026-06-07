class MetroSimulator:
    """
    A simulator for the Delhi Metro system.
    """
    def __init__(self):
        """
        Initializes the MetroSimulator, loading and pre-processing data.
        """
        self.blue_noida, self.blue_vaishali, self.magenta = [], [], []
        self.station_data = {}
        self.interchange_time = 5
        self.start_hour = 6
        self.end_hour = 23
        self.peak_hour_start_1 = self.time_to_int('08:00')
        self.peak_hour_end_1 = self.time_to_int('10:00')
        self.peak_hour_start_2 = self.time_to_int('17:00')
        self.peak_hour_end_2 = self.time_to_int('19:00')
        self.peak_hour_frequency = 4
        self.normal_frequency = 8
        self.dwk_list = []
        self.bot_list = []
        self.line_total_times = {}
        self.line_name_mapping = {
            "Blue_N": self.blue_noida,
            "Blue_V": self.blue_vaishali,
            "Magenta": self.magenta
        }
        self.file_read()
        self.precompute_timetables()

    def _generate_timetable(self):
        """
        Generates a timetable for a line.
        """
        timetable = []
        start = self.time_to_int('06:00')
        end = self.time_to_int('23:00')
        while True:
            timetable.append(start)
            if (self.peak_hour_start_1 <= start < self.peak_hour_end_1) or \
               (self.peak_hour_start_2 <= start < self.peak_hour_end_2):
                start += self.peak_hour_frequency
            else:
                start += self.normal_frequency
            if start > end:
                break
        return timetable

    def precompute_timetables(self):
        """
        Pre-computes the timetables for the start of the lines.
        """
        self.dwk_list = self._generate_timetable()
        self.bot_list = self._generate_timetable()


    def file_read(self):
        """
        Reads the metro data from the file and populates the data structures.
        """
        with open("metro_data.txt", 'r') as f:
            heading = f.readline()
            x = f.readlines()
            for i in x:
                s = i.rstrip().split(',')
                s[2] = int(s[2])
                s[3] = int(s[3])
                if s[0] == "Blue_N":
                    self.blue_noida.append(s)
                elif s[0] == "Blue_V":
                    self.blue_vaishali.append(s)
                elif s[0] == "Magenta":
                    self.magenta.append(s)
        
        for line_name, line in self.line_name_mapping.items():
            cumulative_time = 0
            total_time = 0
            for station in line:
                cumulative_time += station[2]
                total_time += station[2]
                self.station_data[station[1]] = {"line": line_name, "cumulative_time": cumulative_time, "is_interchange": station[4] == "yes"}
            self.line_total_times[line_name] = total_time

    def time_to_int(self, s):
        """
        Converts a time string in HH:MM format to minutes.
        """
        try:
            h=int(s[0:2])
            m=int(s[3:])
            if not (0 <= h < 24 and 0 <= m < 60):
                return None
            return h*60+m
        except (ValueError, IndexError):
            return None

    def int_to_time(self, s):
        """
        Converts minutes to a time string in HH:MM format.
        """
        h=str(s//60)
        if len(h)==1:
            h="0"+h
        m=str(s%60)
        if len(m)==1:
            m="0"+m
        return h+":"+m

    def cumulative_time_forward(self, current_station):
        """
        Calculates the cumulative time from the start of the line to the current station.
        """
        return self.station_data[current_station]["cumulative_time"]

    def cumulative_time_backward(self, current_station):
        """
        Calculates the cumulative time from the current station to the end of the line.
        """
        line_name = self.station_data[current_station]["line"]
        return self.line_total_times[line_name] - self.station_data[current_station]["cumulative_time"]


    def _station_time_list(self, current_station, timetable):
        """
        Generates the list of train arrival times at a given station.
        """
        cumalative = self.cumulative_time_forward(current_station)
        current_time = 360 + cumalative
        time_list = [current_time]
        for i in range(1, len(timetable)):
            prev_origin_time = timetable[i - 1]
            curr_origin_time = timetable[i]
            interval = curr_origin_time - prev_origin_time
            current_time += interval
            time_list+=[current_time]
        return time_list

    def get_next_train_time(self, station_times, current_time):
        """
        Gets the next train time from a list of station times.
        """
        for time in station_times:
            if time >= current_time:
                return self.int_to_time(time)
        return "No service available"

    def metro_timings(self, line, current_station, current_time):
        """
        Gets the next train times for a given station and line.
        """
        line=line.lower()
        current_station=current_station.lower()
        
        if not (self.time_to_int(f'{self.start_hour:02d}:00') <= current_time < self.time_to_int(f'{self.end_hour:02d}:00')):
            return "No service available", "No service available"

        station_time_list_f = self._station_time_list(current_station, self.dwk_list)
        station_time_list_b = self._station_time_list(current_station, self.bot_list)
        
        forward_time = self.get_next_train_time(station_time_list_f, current_time)
        backward_time = self.get_next_train_time(station_time_list_b, current_time)
        
        return forward_time, backward_time

    def get_station_data(self, station_name):
        """
        Gets the data for a given station.
        """
        return self.station_data.get(station_name.lower())

    def process_one_way(self, current_station, final_station, current_time, line):
        """
        Processes a one-way journey between two stations.
        """
        currentTime = self.time_to_int(current_time)
        forw_time, back_time = self.metro_timings(line, current_station, currentTime)
        correctLinelist = []
        if line == "Magenta":
            correctLinelist = self.magenta
        elif line == "Blue":
            if final_station in [s[1] for s in self.blue_noida]:
                correctLinelist = self.blue_noida
            else:
                correctLinelist = self.blue_vaishali
        
        currentIdx = -1
        finalIdx = -1
        for i, station in enumerate(correctLinelist):
            if station[1] == current_station:
                currentIdx = i
            if station[1] == final_station:
                finalIdx = i

        if currentIdx == -1 or finalIdx == -1:
            # Handle stations on different branches of the Blue Line
            if line == "Blue":
                # Find path to Yamuna Bank from start
                yb_idx_start = -1
                for i, station in enumerate(self.line_name_mapping[self.station_data[current_station]["line"]]):
                    if station[1] == "yamuna bank":
                        yb_idx_start = i
                        break
                
                # Find path from Yamuna Bank to end
                yb_idx_end = -1
                for i, station in enumerate(self.line_name_mapping[self.station_data[final_station]["line"]]):
                    if station[1] == "yamuna bank":
                        yb_idx_end = i
                        break

                # Calculate duration
                dur1 = abs(self.station_data[current_station]["cumulative_time"] - self.station_data["yamuna bank"]["cumulative_time"])
                dur2 = abs(self.station_data[final_station]["cumulative_time"] - self.station_data["yamuna bank"]["cumulative_time"])
                duration = dur1 + dur2
                
                # Determine direction
                if currentIdx > yb_idx_start: # Moving towards Yamuna Bank
                    departureTime = forw_time
                else:
                    departureTime = back_time

                depValue = self.time_to_int(departureTime)
                arrValue = depValue + duration
                return departureTime, duration, self.int_to_time(arrValue)
            else:
                return None, None, None


        currentCum = self.station_data[current_station]["cumulative_time"]
        finalCum = self.station_data[final_station]["cumulative_time"]
        duration = abs(finalCum - currentCum)

        departureTime = ""
        if finalIdx > currentIdx:
            departureTime = forw_time
        else:
            departureTime = back_time
        depValue = self.time_to_int(departureTime)
        arrValue = depValue + duration
        return departureTime, duration, self.int_to_time(arrValue)

    def calculate_fare(self, duration):
        """
        Calculates the fare for a given duration.
        """
        if 0 <= duration <= 5:
            return 11
        elif 5 < duration <= 11:
            return 21
        elif 11 < duration <= 25:
            return 31
        elif 25 < duration <= 40:
            return 43
        elif 40 < duration <= 60:
            return 54
        elif duration > 60:
            return 64
        return 0

    def journey_planner(self, start, destination, start_time):
        """
        Plans a journey between two stations.
        """
        start = start.lower()
        destination = destination.lower()
        startData = self.get_station_data(start)
        destinationData = self.get_station_data(destination)
        if not startData:
            print(f"Error: Starting station '{start}' not found.")
            return
        if not destinationData:
            print(f"Error: Destination station '{destination}' not found.")
            return
        common_line = None
        if startData["line"] == destinationData["line"]:
            common_line = startData["line"]
        elif startData["line"].startswith("Blue") and destinationData["line"].startswith("Blue"):
            common_line = "Blue"


        if common_line:
            line_family = "Magenta" if common_line == "Magenta" else "Blue"
            departure, duration, arrival = self.process_one_way(start, destination, start_time, line_family)

            if departure:
                fare = self.calculate_fare(duration)
                print("\n")
                print(f"journey plan: {start} to {destination}")
                print(f"direct route ({common_line})")
                print(f"next metro at start location: {departure}")
                print(f"total travel time: {duration} mins")
                print(f"arrival at destination: {arrival}")
                print("Total fare for the journey:",fare, "rupees")
                print("\n")

                return
            else:
                print("impossible direct route")
                return

        interchanges = [station for station, data in self.station_data.items() if data["is_interchange"]]
        best_route = None
        min_arrival_val = 9999999999999999
        for inter in interchanges:
            line1_fam = "Blue" if startData["line"].startswith("Blue") else "Magenta"
            line2_fam = "Blue" if destinationData["line"].startswith("Blue") else "Magenta"
            dep1, dur1, arr1 = self.process_one_way(start, inter, start_time, line1_fam)
            if not dep1:
                continue
            arr1_val = self.time_to_int(arr1)
            leg2_start_val = arr1_val + self.interchange_time
            leg2_start_str = self.int_to_time(leg2_start_val)
            dep2, dur2, arr2 = self.process_one_way(inter, destination, leg2_start_str, line2_fam)
            if not dep2:
                continue
            final_arrival_val = self.time_to_int(arr2)
            if final_arrival_val < min_arrival_val:
                min_arrival_val = final_arrival_val
                best_route = {
                    "interchange": inter,
                    "leg1": (dep1, dur1, arr1),
                    "leg2": (dep2, dur2, arr2),
                    "total_dur": final_arrival_val - self.time_to_int(dep1)
                }
        if best_route:
            total_duration = best_route['total_dur']
            fare = self.calculate_fare(total_duration)
            print("\n")
            print("journey plan:",start, "to", destination)
            print(f"interchange required at {best_route['interchange']}")
            print(f"start at {start} ({best_route['leg1'][0]})")
            print(f"travel: {best_route['leg1'][1]} min")
            print(f"arrive {best_route['interchange']}: {best_route['leg1'][2]}")
            print(f"change train - {self.interchange_time} mins")
            print(f"depart {best_route['interchange']} ({best_route['leg2'][0]})")
            print(f"travel: {best_route['leg2'][1]} min")
            print(f"arrive {destination}: {best_route['leg2'][2]}")
            print(f"total journey time: {best_route['total_dur']} min")
            print(f"Total fare for the journey: {fare} rupees")

        else:
            print("impossible")

    def main_menu(self):
        """
        The main menu of the application.
        """
        while True:
            print("\t\t\t Enter the number according to the function you want to use:"
                  "\n\t\t\t\t 0 - Exit"
                  "\n\t\t\t\t 1 - Metro Timings"
                  "\n\t\t\t\t 2 - Journey Planner")
            try:
                menuInput=int(input())
            except ValueError:
                print("Invalid input. Please enter a number.")
                continue
            if menuInput == 0:
                return
            elif menuInput == 1:
                    line=input("Enter the line: ")
                    line=line.lower()
                    currentStation=input("Enter the Current Station: ")
                    currentStation=currentStation.lower()
                    currentTime_str = input("Enter the Current Time: ")
                    currentTime = self.time_to_int(currentTime_str)
                    if currentTime is None:
                        print("Invalid time format. Please use HH:MM.")
                        continue
                    forwardTime, backwardTime=self.metro_timings(line, currentStation, currentTime)
                    if line == 'blue':
                        print("Train towards Noida/Vaishali: ",forwardTime,"\nTrain towards Dwarka Sec 21: ",backwardTime)
                    elif line == 'magenta':
                        print(f"Train towards Botanical Garden: {forwardTime}\nTrain towards Janakpuri West: {backwardTime}")
            elif menuInput == 2:
                src = input("Enter Source Station: ")
                dst = input("Enter Destination Station: ")
                time_str = input("Enter Time of Travel (HH:MM): ")
                time = self.time_to_int(time_str)
                if time is None:
                    print("Invalid time format. Please use HH:MM.")
                    continue
                self.journey_planner(src, dst, time_str)

if __name__ == "__main__":
    simulator = MetroSimulator()
    simulator.main_menu()
