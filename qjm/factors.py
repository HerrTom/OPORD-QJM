import csv
import bisect


class LookupTable:
    """Base class for lookup tables."""
    def __init__(self, file_path):
        self.name = []
        self.data = {}
        self.headers = []
        self.load_data(file_path)

    def load_data(self, file_path):
        """Loads data from a CSV file."""
        raise NotImplementedError(
            "This method should be implemented by subclasses")


class StandardLookupTable(LookupTable):
    """Standard lookup table for categorical data with text labels and named
       columns."""
    def load_data(self, file_path):
        with open(file_path) as f:
            reader = csv.reader(f, delimiter=',')
            # Store column headers, ignoring the first entry (row label)
            self.headers = next(reader)[1:]
            for row in reader:
                # First column is the row label
                self.name.append(row[0])
                self.data[row[0]] = {self.headers[i]: float(row[i+1]) for i
                                     in range(len(self.headers))}

    def get(self, key, column=None):
        """Fetches the data associated with the given key and optionally a
           specific column."""
        if column:
            return self.data.get(key, {}).get(column)
        return self.data.get(key)

    def get_headers(self):
        """Returns the list of column headers."""
        return self.headers


class InterpolatingLookupTable(LookupTable):
    """Interpolating lookup table for numerical data that allows interpolation
       between values."""
    def load_data(self, file_path):
        self.data = []
        with open(file_path) as f:
            reader = csv.reader(f, delimiter=',')
            next(reader)
            for row in reader:
                self.name.append(float(row[0]))
                self.data.append(float(row[1]))

    def interpolate(self, key):
        """Interpolates to find the value associated with a numerical key."""
        pos = bisect.bisect_left(self.name, key)
        if pos == 0:
            return self.data[0]
        if pos == len(self.name):
            return self.data[-1]
        x0, y0 = self.name[pos - 1], self.data[pos - 1]
        x1, y1 = self.name[pos], self.data[pos]
        return y0 + (y1 - y0) * (key - x0) / (x1 - x0)


# Create the needed data tables
TERRAIN_FACTORS = StandardLookupTable('./database/tables/TerrainFactors.csv')
WEATHER_FACTORS = StandardLookupTable('./database/tables/WeatherFactors.csv')
MORALE_FACTORS = StandardLookupTable('./database/tables/MoraleFactor.csv')
SEASON_FACTORS = StandardLookupTable('./database/tables/SeasonFactors.csv')
SURPRISE_FACTORS = StandardLookupTable('./database/tables/SurpriseFactors.csv')
POSTURE_FACTORS = StandardLookupTable('./database/tables/PostureFactors.csv')
AIR_SUPERIORITY_FACTORS = StandardLookupTable('./database/tables/AirSuperiorityFactors.csv')
OPPOSITION_FACTORS = InterpolatingLookupTable('./database/tables/OppositionFactor.csv')
STRENGTH_SIZE_FACTORS = InterpolatingLookupTable('./database/tables/StrengthSize.csv')
STRENGTH_SIZE_ARMOUR_FACTORS = InterpolatingLookupTable('./database/tables/StrengthSizeArmour.csv')
