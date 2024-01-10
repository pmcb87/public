# The purpose of this script is to graph Insight Agent CPU usage and the job responsible for the CPU usage
# Recommend reviewing the output csv files to validate

import re
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.dates import ConciseDateFormatter

# Prompt user for the file name
file_path = input("Enter the file name: ")

# Read the text file
with open(file_path, 'r') as file:
    text = file.read()

# Define the regex pattern with named capture groups
pattern = r"(?P<timestamp>\d{4}-\d{2}-\d{2}\s\d{2}:\d{2}:\d{2}).*?job:\s(?P<agentjob>agent\.jobs\.[a-z\.\_]+).*?'cpuUtil': '(?P<cpuUtil>\d{1,2}\.\d{2})'"

# Find all matches and extract the captured groups
matches = re.findall(pattern, text)

# Write the extracted fields to a new file
output_file_name = input("Name the export name (extention not required): ")
output_csv = output_file_name + ".csv"
with open(output_csv, 'w') as output_file:
    header = ["timestamp", "agent_job", "cpu_util"]
    output_file.write(', '.join(header) + '\n')
    for match in matches:
        fields = ', '.join(match)
        output_file.write(fields + '\n')

# Read the CSV file and create the DataFrame
df = pd.read_csv(output_csv.strip(), skipinitialspace=True)

# Convert the 'timestamp' column to datetime format
df['timestamp'] = pd.to_datetime(df['timestamp'])

# Sort the DataFrame by the date column in ascending order
df_deduplicated = df.sort_values(by='timestamp').copy()

# Identify consecutive instances of 0.00 values in the cpu_util column
consecutive_zeros = (df['cpu_util'] == 0.00) & (df['cpu_util'].shift(1) == 0.00)

# Keep the first and last rows in consecutive instances of 0.00 values
df_deduplicated = df[~consecutive_zeros | consecutive_zeros.shift(-1)].copy()

# Round the timestamp to the nearest minute
df_deduplicated.loc[:, 'rounded_timestamp'] = df_deduplicated['timestamp'].dt.round('min')
# .copy()
# Change the time rounding depending on the volume of logs
df['rounded_timestamp'] = df['timestamp'].dt.round('min')

# Sort the DataFrame by cpu_util column in descending order
df_deduplicated = df_deduplicated.sort_values(by='cpu_util', ascending=False).copy()

# Deduplicate the DataFrame based on the rounded_timestamp column and keep the first occurrence of each rounded timestamp
df_deduplicated = df.drop_duplicates(subset='rounded_timestamp', keep='first').copy()

# Remove the 'rounded_timestamp' column
df_deduplicated = df_deduplicated.drop(columns='rounded_timestamp').copy()

# Save the deduplicated DataFrame to a new CSV file
print("The original version is saved as " + output_file_name + ".csv")
print("This script automatically de-dupes the original for visualizaion purposes.")
print("The modified version is saved as " + output_file_name + "_deduped.csv")
output_file_deduplicated = output_file_name + "_deduped.csv"
df_deduplicated.to_csv(output_file_deduplicated, index=False)

# Rename df and sort by timestamp
df = df_deduplicated
df = df.sort_values(by='timestamp')

# Create the line graph without specifying colors
for job in df['agent_job'].unique():
    job_data = df[df['agent_job'] == job]
    plt.plot(job_data['timestamp'], job_data['cpu_util'], label=job, alpha=0.5)

# Customize the x-axis tick locations and labels
# Assuming 'timestamp' column is a datetime object
tick_locations = df['timestamp']

# Set x-axis formatter to ConciseDateFormatter
formatter = ConciseDateFormatter(tick_locations)
plt.gca().xaxis.set_major_formatter(formatter)

# Set x-axis and y-axis labels, and plot title
plt.xlabel('Timestamp')
plt.ylabel('CPU Utilization')
plt.title('CPU Utilization Over Time')

# Rotate x-axis labels
plt.xticks(rotation=45, ha='right')

# Add a text annotation with the first and last timestamp values
start_time = df['timestamp'].min()
end_time = df['timestamp'].max()
plt.annotate(f'Start Time: {start_time}\nEnd Time: {end_time}',
             xy=(0.02, 0.98),
             xycoords='axes fraction',
             ha='left',
             va='top',
             fontsize=8)

# Add legend
plt.legend()

# Customize the x-axis tick locations and labels
ax = plt.gca()
ax.xaxis.set_major_locator(mdates.DayLocator())  # Set major tick locations to daily intervals
ax.xaxis.set_minor_locator(mdates.HourLocator(interval=6))  # Set minor tick locations to 6-hour intervals

# Set the format of major and minor tick labels
ax.xaxis.set_major_formatter(mdates.ConciseDateFormatter(ax.xaxis.get_major_locator()))
ax.xaxis.set_minor_formatter(mdates.ConciseDateFormatter(ax.xaxis.get_minor_locator()))

# Adjust the figure size
fig = plt.gcf()
fig.autofmt_xdate()  # Automatically format x-axis labels for better visibility
fig.set_size_inches(10, 8)  # Set the width and height of the figure in inches

# Save the graph as an image file
plt.tight_layout()
print("Graph saved as: " + output_file_name + ".png")
plt.savefig(output_file_name + ".png")
#plt.show()
