import os
import pandas as pd
import requests
import sys
import json
import seaborn as sns
import matplotlib.pyplot as plt
from scipy import stats as st
import chardet

def get_file_encoding(file_path):
    with open(file_path, 'rb') as f:
        result = chardet.detect(f.read())
    return result['encoding']

# Function to read the CSV file and summarize it
def summarize_data(file_path):
    # Read the dataset into a pandas DataFrame
    encoding=get_file_encoding(file_path)
    df = pd.read_csv(file_path,encoding=encoding)
    
    # Generate summary statistics
    stats = df.describe()

    # Check for missing values
    missing_values = df.isnull().sum()

    # Handle numeric columns for correlation matrix
    numeric_df = df.select_dtypes(include=['number'])
    correlation_matrix = numeric_df.corr() if numeric_df.shape[1] > 1 else "No numeric data for correlation"

    # Check for outliers using Z-score (this is a simple method, you can use more complex ones)
    z_scores = st.zscore(numeric_df) if not numeric_df.empty else None
    outliers = (z_scores > 3).sum(axis=0) if z_scores is not None else "No numeric data for outlier detection"

    # Return summary as a dictionary
    return {
        "stats": stats,
        "missing_values": missing_values,
        "correlation_matrix": correlation_matrix,
        "outliers": outliers,
        "df": df
    }

# Function to generate a story using your AI proxy
def generate_story(summary, output_dir, aip_proxy_token):
    # Define your AI proxy URL
    ai_proxy_url = "https://aiproxy.sanand.workers.dev/openai/v1/chat/completions"
    
    # Prepare the data to send to your AI proxy
    prompt = f"""
    You are a data analyst. Here's a summary of a dataset:

    1. Summary statistics:
    {summary["stats"].to_string()}

    2. Missing values:
    {summary["missing_values"].to_string()}

    3. Correlation matrix (if available):
    {summary["correlation_matrix"]}

    4. Outliers:
    {summary["outliers"]}

    Based on the dataset, write a narrative story summarizing the data analysis, including insights and implications.
    """
    
    # Set up the request payload
    payload = {
        "model": "gpt-4o-mini",  # or specify the model your proxy uses
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 500  # You can adjust the max tokens if needed
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {aip_proxy_token}"
    }

    try:
        # Send the request to your AI proxy
        response = requests.post(ai_proxy_url, json=payload, headers=headers)

        # Check if the request was successful
        if response.status_code == 200:
            # Parse the response and get the generated story
            story = response.json().get("choices", [{}])[0].get("message", {}).get("content", "No story generated.")
        else:
            print(f"Error: Unable to generate story. Status code: {response.status_code}")
            story = "Failed to generate story."

    except Exception as e:
        print(f"Error generating story: {e}")
        story = "Error generating story."

    # Save the story to README.md
    with open(os.path.join(output_dir, "README.md"), "w") as f:
        f.write(story)

# Function to generate visualizations
def generate_visualizations(df, output_dir):
    # Limit to 3 visualizations
    visualizations = 0

    # Histogram of a numeric column (first numeric column available)
    numeric_columns = df.select_dtypes(include=['number']).columns
    if numeric_columns.any():
        fig, ax = plt.subplots()
        df[numeric_columns[0]].plot(kind='hist', bins=20, ax=ax, color='skyblue', edgecolor='black')
        ax.set_title(f"Histogram of {numeric_columns[0]}")
        ax.set_xlabel(numeric_columns[0])
        ax.set_ylabel("Frequency")
        plt.tight_layout()
        fig.savefig(os.path.join(output_dir, "histogram.png"))
        visualizations += 1

    # Correlation Heatmap (if there are more than 1 numeric column)
    if len(numeric_columns) > 1:
        fig, ax = plt.subplots(figsize=(10, 8))
        sns.heatmap(df[numeric_columns].corr(), annot=True, cmap="coolwarm", ax=ax)
        ax.set_title("Correlation Heatmap")
        plt.tight_layout()
        fig.savefig(os.path.join(output_dir, "correlation_heatmap.png"))
        visualizations += 1

    # Boxplot for outlier detection (if numeric columns exist)
    if numeric_columns.any() and visualizations < 3:
        fig, ax = plt.subplots()
        sns.boxplot(data=df[numeric_columns], ax=ax, palette="Set2")
        ax.set_title("Boxplot for Outlier Detection")
        plt.tight_layout()
        fig.savefig(os.path.join(output_dir, "boxplot.png"))
        visualizations += 1

# Main function to process the CSV and generate the report
def process_csv(input_csv, output_dir, aip_proxy_token):
    # Ensure the output directory exists
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Summarize the dataset
    summary = summarize_data(input_csv)

    # Generate a story based on the summary
    generate_story(summary, output_dir, aip_proxy_token)

    # Generate visualizations
    generate_visualizations(summary["df"], output_dir)

# Command line entry point
if __name__ == "__main__":
    # Check if enough arguments are passed
    if len(sys.argv) < 2:
        print("Usage: python autolysis.py <csv_file>")
        sys.exit(1)

    # Get the input CSV file from the command line arguments
    input_csv = sys.argv[1]

    # Check if the file exists
    if not os.path.exists(input_csv):
        print(f"Error: The file {input_csv} does not exist.")
        sys.exit(1)

    # Define the output directory
    output_dir = input_csv[:-4]

    # Your AIPROXY_TOKEN obtained from the AI proxy login
    aip_proxy_token = "eyJhbGciOiJIUzI1NiJ9.eyJlbWFpbCI6IjIzZjEwMDI0NTFAZHMuc3R1ZHkuaWl0bS5hYy5pbiJ9.6FdpxtT8elZfWgvU2T2N8kCCK1bwlJGAxfOSfnjDpMI"


    # Process the CSV and generate the report and visuals
    process_csv(input_csv, output_dir, aip_proxy_token)
