# Read temperature data from file
file_path = "/Users/mihirchintawar/agent/terminalUI/devon-tui/weather_stations.csv"

with open(file_path, 'r') as file:
    lines = file.readlines()

print(f"Read {len(lines)} lines from {file_path}")

temps = {}

for line in lines:
    station, temp_str = line.strip().split(';')
    temp = float(temp_str)
    
    if station not in temps:
        temps[station] = {'min': temp, 'max': temp, 'sum': temp, 'count': 1}
    else:
        temps[station]['min'] = min(temps[station]['min'], temp)
        temps[station]['max'] = max(temps[station]['max'], temp)
        temps[station]['sum'] += temp
        temps[station]['count'] += 1

# Calculate mean temperature per station
for station in temps:
    temps[station]['mean'] = round(temps[station]['sum'] / temps[station]['count'], 1)

# Create output dictionary in specified format
output = {station: f"{temps[station]['min']}/{temps[station]['mean']}/{temps[station]['max']}" for station in temps}

print(output)
