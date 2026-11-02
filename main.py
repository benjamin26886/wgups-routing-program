# Author: Nicholas Benjamin
# Project: WGUPS Routing Program (C950 - Data Structures and Algorithms II)
#
# How this program works, start to finish:
#   1. Read packages.csv and put every package into my own hash table.
#   2. Read distances.csv into a list of addresses and a matrix of distances.
#   3. Load the three trucks by hand (the special notes made that easier than
#      trying to automate it) and run Nearest Neighbor on each one. That gives
#      me the route and the delivery time for every package.
#   4. Start a menu so the user can check any package, or all of them, at any
#      time of day and also see the total mileage.

import csv
import datetime
import os

# I use the folder main.py lives in so the csv files get found even if I run
# the program from some other directory.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Constants from the project assumptions so I don't have magic numbers later.
HUB_ADDRESS = '4001 South 700 East'
TRUCK_SPEED_MPH = 18
TRUCK_CAPACITY = 16


# ---------------------------------------------------------------------------
# DATA STRUCTURE: my own hash table (separate chaining)
# ---------------------------------------------------------------------------
# I'm not using a dict here since the project says to build it myself, and the
# table doesn't use any other library or class either. It is just a list of
# buckets and each bucket is a list. If two package IDs end up in the same
# bucket they get chained together in that list, so nothing gets overwritten.
# Every entry is [package_id, [address, deadline, city, zip, weight, status]].
class ChainingHashTable:
    def __init__(self, initial_capacity=40):
        # Start with one empty list for every bucket.
        self.table = []
        for i in range(initial_capacity):
            self.table.append([])

    def _bucket_index(self, package_id):
        # The IDs are plain integers so modulo is enough to pick a bucket.
        return package_id % len(self.table)
 
    def _find(self, package_id):
        # Walk the one bucket the ID hashes to and hand back that package's
        # list of data components, or None if the ID isn't in the table.
        bucket_list = self.table[self._bucket_index(package_id)]
        for kv in bucket_list:
            if kv[0] == package_id:
                return kv[1]
        return None

    # Part A: insert. It takes the package ID and stores the address, deadline,
    # city, zip, weight and status. Once a package is delivered the status
    # also holds the delivery time.
    def insert(self, package_id, address, deadline, city, zip_code, weight, status):
        data = [address, deadline, city, zip_code, weight, status]
        bucket_list = self.table[self._bucket_index(package_id)]

        # If this ID is already in the bucket, replace the old record.
        for kv in bucket_list:
            if kv[0] == package_id:
                kv[1] = data
                return True

        # Otherwise add a new [key, value] pair to the end of the bucket.
        bucket_list.append([package_id, data])
        return True

    # Part B: look-up. Give it a package ID and it returns every data piece:
    # address, deadline, city, zip, weight, status (the status holds the
    # delivery time once the package is delivered).
    def lookup(self, package_id):
        data = self._find(package_id)
        if data is None:
            return None
        return (data[0], data[1], data[2], data[3], data[4], data[5])

    # Small updaters so the program can change a stored status or address
    # (Package 9 gets a new address at 10:20) without rebuilding the entry.
    def set_status(self, package_id, status):
        data = self._find(package_id)
        if data is None:
            return False
        data[5] = status
        return True

    def set_address(self, package_id, address, zip_code):
        data = self._find(package_id)
        if data is None:
            return False
        data[0] = address
        data[3] = zip_code
        return True


# ---------------------------------------------------------------------------
# PackageRecord: the routing details for one package
# ---------------------------------------------------------------------------
# The hash table only holds the six data components the project asks for. This
# little class holds everything the routing code needs on the side: the notes,
# which truck has the package, when that truck leaves, when the package is
# really at the hub, and when it gets delivered.
class PackageRecord:
    def __init__(self, ID, notes):
        self.ID = ID
        self.notes = notes
        self.truck_id = None          # filled in when the package gets loaded
        self.available_time = datetime.timedelta(0)  # when it is actually at the hub
        self.departure_time = None    # when its truck leaves
        self.delivery_time = None     # set by the routing code

        # The "Delayed on flight" packages can't leave before 9:05, so I
        # store that here and check it when I work out the status.
        if 'Delayed on flight' in notes:
            self.available_time = datetime.timedelta(hours=9, minutes=5)


def format_time(td):
    # timedelta prints with fractions of a second, so I turn it into a clean
    # HH:MM:SS string myself.
    total = int(td.total_seconds())
    hours, remainder = divmod(total, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


# ---------------------------------------------------------------------------
# LOAD THE DATA FILES
# ---------------------------------------------------------------------------
my_hash_table = ChainingHashTable()
records = []   # records[package_id] -> PackageRecord, filled in below

# Read packages.csv. The first few rows are titles and blanks, so I skip them.
package_rows = []
with open(os.path.join(BASE_DIR, 'packages.csv')) as f:
    reader = csv.reader(f)
    for _ in range(7):
        next(reader)
    for row in reader:
        # Only rows that start with a number are real packages.
        if row and row[0].strip().isdigit():
            package_rows.append(row)

# The IDs are plain integers, so I size the list from the biggest one.
max_id = 0
for row in package_rows:
    if int(row[0]) > max_id:
        max_id = int(row[0])
for i in range(max_id + 1):
    records.append(None)

for row in package_rows:
    pkg_id = int(row[0])
    address = row[1].strip()
    # The package file and the distance file spell this address
    # differently, so I make them match or the distance look-up breaks.
    if address == "5383 South 900 East #104":
        address = "5383 S 900 East #104"
    city = row[2].strip()
    zip_code = row[4].strip()
    deadline = row[5].strip()
    weight = row[6].strip()
    notes = row[7].strip()

    my_hash_table.insert(pkg_id, address, deadline, city, zip_code, weight, "At Hub")
    records[pkg_id] = PackageRecord(pkg_id, notes)

# Read distances.csv and build the address list and the distance matrix.
distances = []
addresses = []
with open(os.path.join(BASE_DIR, 'distances.csv')) as f:
    reader = csv.reader(f)
    for row in reader:
        if not row or len(row) < 3:
            continue
        try:
            # Skip the title rows by only taking rows that have a real number
            # in them (the hub row is the one exception).
            if row[1].strip() == 'HUB' or float(row[2].strip()) >= 0:
                # The address cell has the location name on the first line
                # and the street address after it, so I keep the street part.
                addr = row[1].strip().split('\n')[0].strip()
                if addr == 'HUB':
                    addr = HUB_ADDRESS
                dists = []
                for d in row[2:]:
                    if d.strip():
                        try:
                            dists.append(float(d.strip()))
                        except ValueError:
                            break
                distances.append(dists)
                addresses.append(addr)
        except ValueError:
            pass


def get_distance(address1, address2):
    # Find where each address sits in the table. Distances are the same going
    # either way, and only the bottom-left half of the table is filled in, so
    # I use the bigger index as the row and the smaller one as the column.
    idx1 = addresses.index(address1)
    idx2 = addresses.index(address2)
    return distances[max(idx1, idx2)][min(idx1, idx2)]


def update_status(pkg_id, current_time):
    # Work out the status for the time the user typed in and save it in the
    # hash table. The order of these checks matters: delivered beats en route
    # beats delayed.
    record = records[pkg_id]

    # Package 9 has the wrong address until 10:20, so before that time I
    # show the bad address and after that I show the corrected one.
    if pkg_id == 9:
        if current_time < datetime.timedelta(hours=10, minutes=20):
            my_hash_table.set_address(9, "300 State St", "84103")
        else:
            my_hash_table.set_address(9, "410 S State St", "84111")

    if record.delivery_time is not None and current_time >= record.delivery_time:
        status = "Delivered at " + format_time(record.delivery_time)
    elif record.departure_time is not None and current_time >= record.departure_time:
        status = "En Route"
    elif current_time < record.available_time:
        status = "Delayed (arrives at hub " + format_time(record.available_time) + ")"
    else:
        status = "At Hub"
    my_hash_table.set_status(pkg_id, status)


# ---------------------------------------------------------------------------
# TRUCKS AND ROUTING
# ---------------------------------------------------------------------------
class Truck:
    def __init__(self, truck_id, packages, departure_time_str):
        # A truck holds 16 packages max, so I stop the program if I overload it.
        if len(packages) > TRUCK_CAPACITY:
            raise ValueError("A truck can carry at most 16 packages.")
        self.truck_id = truck_id
        self.packages = packages
        self.mileage = 0.0
        self.address = HUB_ADDRESS
        # Turn "08:00" into a timedelta so I can do math with it later.
        h, m = map(int, departure_time_str.split(':'))
        self.departure_time = datetime.timedelta(hours=h, minutes=m)
        self.time = self.departure_time
        self.return_time = None   # only set if the truck drives back to the hub

        # Mark each package with its truck number and when that truck leaves.
        for pkg_id in self.packages:
            records[pkg_id].truck_id = truck_id
            records[pkg_id].departure_time = self.departure_time


def deliver_packages(truck, return_to_hub=False):
    # Nearest Neighbor. I put everything on the truck in an "unvisited" list
    # and keep driving to whichever address is closest until the list is empty.
    unvisited = list(truck.packages)

    while len(unvisited) > 0:
        next_id = None
        next_address = None
        min_distance = float('inf')

        # Check every package that is left and remember the closest one. The
        # address comes out of the hash table by package ID.
        for pkg_id in unvisited:
            pkg_address = my_hash_table.lookup(pkg_id)[0]
            dist = get_distance(truck.address, pkg_address)
            if dist < min_distance:
                min_distance = dist
                next_id = pkg_id
                next_address = pkg_address

        # Drive there. Miles go on the odometer and the clock moves forward
        # by distance / speed.
        truck.mileage += min_distance
        truck.address = next_address
        truck.time += datetime.timedelta(hours=min_distance / TRUCK_SPEED_MPH)

        # Save the delivery time on the package and take it off the list so
        # it doesn't get picked again.
        records[next_id].delivery_time = truck.time
        unvisited.remove(next_id)

    # There are only two drivers for three trucks, so one driver has to come
    # back to the hub to take the third truck. That trip counts for mileage.
    if return_to_hub:
        dist_to_hub = get_distance(truck.address, HUB_ADDRESS)
        truck.mileage += dist_to_hub
        truck.address = HUB_ADDRESS
        truck.time += datetime.timedelta(hours=dist_to_hub / TRUCK_SPEED_MPH)
        truck.return_time = truck.time


# ---------------------------------------------------------------------------
# MAIN EXECUTION: load the trucks and run the routes
# ---------------------------------------------------------------------------
# Truck 1 (driver 1): the early deadline packages plus the group that has to
# go together (13, 14, 15, 16, 19, 20). It leaves at 8:00 and then comes back
# to the hub so that same driver can take Truck 3 out.
truck1 = Truck(1, [1, 13, 14, 15, 16, 19, 20, 29, 30, 31, 34, 37, 40], "08:00")
deliver_packages(truck1, return_to_hub=True)

# Truck 2 (driver 2): the "can only be on truck 2" packages and the ones that
# were delayed on the flight. Those get to the hub at 9:05 so the truck can't
# leave before then.
truck2 = Truck(2, [3, 6, 18, 25, 28, 32, 36, 38, 2, 4, 5, 7, 8, 10, 11, 12], "09:05")
deliver_packages(truck2, return_to_hub=False)

# Package 9's address gets fixed at 10:20, which is when Truck 3 leaves, so
# I update it right before building Truck 3. Truck 1's driver is back around
# 9:53, so there's a driver ready for Truck 3 by then.
my_hash_table.set_address(9, "410 S State St", "84111")

# Truck 3 gets everything that's left, including the corrected package 9.
truck3 = Truck(3, [9, 17, 21, 22, 23, 24, 26, 27, 33, 35, 39], "10:20")
deliver_packages(truck3, return_to_hub=False)

trucks = [truck1, truck2, truck3]
total_mileage = truck1.mileage + truck2.mileage + truck3.mileage


# ---------------------------------------------------------------------------
# USER INTERFACE
# ---------------------------------------------------------------------------
def ask_time():
    # Read a time like 09:30 or 09:30:15 and turn it into a timedelta. If the
    # user types something weird this raises ValueError and the menu catches it.
    text = input("Enter a time (HH:MM or HH:MM:SS, 24-hour): ").strip()
    parts = text.split(':')
    if len(parts) == 2:
        parts.append('0')
    if len(parts) != 3:
        raise ValueError
    h, m, s = (int(p) for p in parts)
    if not (0 <= h < 24 and 0 <= m < 60 and 0 <= s < 60):
        raise ValueError
    return datetime.timedelta(hours=h, minutes=m, seconds=s)


def package_line(pkg_id):
    # One line per package so the output is easy to read in the console.
    address, deadline, city, zip_code, weight, status = my_hash_table.lookup(pkg_id)
    return (f"ID: {pkg_id:<2} | {address:<38} | {city:<16} | {zip_code:<5} | "
            f"Deadline: {deadline:<8} | Wt: {weight:<2} | Truck {records[pkg_id].truck_id} | {status}")


def show_all_packages(check_time):
    # Show every package, grouped by the truck it was loaded onto.
    print(f"\n=== Status of ALL packages at {format_time(check_time)} ===")
    for truck in trucks:
        print(f"\n--- Truck {truck.truck_id} (leaves hub {format_time(truck.departure_time)}) ---")
        for pkg_id in sorted(truck.packages):
            update_status(pkg_id, check_time)
            print(package_line(pkg_id))


def show_single_package(check_time):
    text = input("Enter a Package ID (1-40): ").strip()
    # Make sure it's a number and that a package with that ID really exists.
    if not text.isdigit() or my_hash_table.lookup(int(text)) is None:
        print("Invalid Package ID.")
        return
    pkg_id = int(text)
    # Refresh the status for the time the user asked about, then do the
    # Part B look-up, which gives back every piece of package data.
    update_status(pkg_id, check_time)
    address, deadline, city, zip_code, weight, status = my_hash_table.lookup(pkg_id)
    print(f"\n=== Package {pkg_id} at {format_time(check_time)} ===")
    print(f"Delivery address : {address}")
    print(f"Delivery deadline: {deadline}")
    print(f"Delivery city    : {city}")
    print(f"Delivery zip code: {zip_code}")
    print(f"Package weight   : {weight}")
    print(f"Delivery status  : {status}")
    print(f"Loaded on truck  : {records[pkg_id].truck_id}")


def show_mileage():
    # Miles for each truck and then the grand total.
    print("\n=== Mileage ===")
    for truck in trucks:
        print(f"Truck {truck.truck_id}: {truck.mileage:.1f} miles")
    print(f"Total mileage traveled by all trucks: {total_mileage:.1f} miles")


def main():
    # Banner with the total mileage so it's visible as soon as the program runs.
    print("=====================================================")
    print("          WGUPS ROUTING PROGRAM")
    print(f" Total mileage for all trucks: {total_mileage:.1f} miles")
    print("=====================================================")

    # Keep showing the menu until the user picks Exit.
    while True:
        print("\nOptions:")
        print("1. View status of ALL packages at a specific time")
        print("2. Look up a SINGLE package at a specific time")
        print("3. View total mileage of all trucks")
        print("4. Exit program")
        choice = input("Enter your choice (1-4): ").strip()

        if choice == '4':
            print("Exiting program. Have a great day!")
            break
        elif choice == '3':
            show_mileage()
        elif choice in ('1', '2'):
            # Both of these need a time first, so ask for it here.
            try:
                check_time = ask_time()
            except ValueError:
                print("Invalid time format. Please use HH:MM or HH:MM:SS.")
                continue
            if choice == '1':
                show_all_packages(check_time)
            else:
                show_single_package(check_time)
        else:
            print("Invalid choice. Please try again.")


# Only start the menu when this file is run directly.
if __name__ == '__main__':
    main()
