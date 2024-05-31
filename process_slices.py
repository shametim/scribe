import argparse
import logging
import os
import json
from PIL import Image
import numpy as np
import matplotlib.pyplot as plt
from scipy.ndimage import gaussian_filter1d
from scipy.signal import find_peaks

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


def process_image(image_path):
    logging.info(f"Processing image {image_path}")
    img = Image.open(image_path).convert("L")  # Convert image to grayscale
    img_array = np.array(img)
    height, width = img_array.shape
    column_averages = []

    for col in range(width):
        col_data = img_array[:, col]
        avg_grayscale = np.mean(col_data)
        column_averages.append(avg_grayscale)

    return column_averages


def save_column_averages(column_averages, output_path):
    with open(output_path, "w") as f:
        f.write("Column Average Grayscale Values\n")
        f.write("===============================\n\n")
        for col, avg in enumerate(column_averages):
            f.write(f"Column {col}: {avg}\n")


def plot_column_averages(column_averages, output_image_path):
    plt.figure(figsize=(10, 5))
    plt.plot(column_averages, label="Average Grayscale Value")
    plt.xlabel("Column")
    plt.ylabel("Average Grayscale Value")
    plt.title("Column Average Grayscale Values")
    plt.legend()
    plt.savefig(output_image_path)
    logging.info(f"Plot saved to {output_image_path}")
    plt.close()


def validate_and_process_json(json_path):
    with open(json_path, "r") as f:
        data = json.load(f)
    for key, value in data.items():
        if not key.isdigit() or not isinstance(value, (int, float)):
            raise ValueError(f"Invalid entry in JSON file: {key}: {value}")
    return data


def save_correlation_references(data, output_path):
    with open(output_path, "w") as f:
        json.dump(data, f, indent=4)


def calculate_averages(data):
    values = list(data.values())
    correlation_average = np.mean(values)
    return correlation_average


def calculate_correlation_results(json_data, column_averages):
    json_values = list(json_data.values())
    json_avg = np.mean(json_values)
    column_avg_of_avgs = np.mean(column_averages)

    correlation_results = []
    out_of_bounds_instances = set()

    for i in range(len(column_averages)):
        correlation_result = 0
        out_of_bounds_encountered = False
        for j in range(len(json_values)):
            try:
                image_value = column_averages[i + j]
            except IndexError:
                image_value = 0
                out_of_bounds_encountered = True
            correlation_result += (json_values[j] - json_avg) * (
                image_value - column_avg_of_avgs
            )
        correlation_results.append(correlation_result)
        if out_of_bounds_encountered:
            out_of_bounds_instances.add(i)

    return correlation_results, len(out_of_bounds_instances)


def find_peaks_in_correlation(correlation_results):
    # Apply Gaussian smoothing
    smoothed = gaussian_filter1d(correlation_results, sigma=2)

    # Find peaks
    peaks, _ = find_peaks(smoothed)

    # Sort peaks by their heights in descending order
    sorted_peaks = sorted(peaks, key=lambda x: smoothed[x], reverse=True)

    if len(sorted_peaks) > 2:
        return sorted_peaks[:2], f"More than 2 peaks found: {sorted_peaks}"
    elif len(sorted_peaks) < 2:
        return sorted_peaks, "Less than 2 peaks found."
    else:
        return sorted_peaks, "Two peaks found."


def process_folder(folder_path, output_base_folder, json_path, num_files=None):
    files = sorted([f for f in os.listdir(folder_path) if f.endswith(".bmp")])
    if num_files:
        files = files[:num_files]

    correlation_data = validate_and_process_json(json_path)
    correlation_average = calculate_averages(correlation_data)

    for file in files:
        image_path = os.path.join(folder_path, file)
        column_averages = process_image(image_path)

        slice_number = os.path.splitext(file)[0]
        output_folder = os.path.join(output_base_folder, slice_number)
        os.makedirs(output_folder, exist_ok=True)

        output_txt_path = os.path.join(
            output_folder, f"{slice_number}_column_averages.txt"
        )
        save_column_averages(column_averages, output_txt_path)
        logging.info(f"Column averages saved to {output_txt_path}")

        output_image_path = os.path.join(
            output_folder, f"{slice_number}_column_averages.png"
        )
        plot_column_averages(column_averages, output_image_path)

        correlation_output_path = os.path.join(
            output_folder, "correlation_references.json"
        )
        save_correlation_references(correlation_data, correlation_output_path)
        logging.info(f"Correlation references saved to {correlation_output_path}")

        correlation_avg_output_path = os.path.join(
            output_folder, "correlation_references_averages.txt"
        )
        with open(correlation_avg_output_path, "w") as f:
            f.write(f"Correlation References Average: {correlation_average}\n")

        column_avg_of_avgs = np.mean(column_averages)
        column_avg_output_path = os.path.join(
            output_folder, "column_averages_average.txt"
        )
        with open(column_avg_output_path, "w") as f:
            f.write(f"Column Averages Average: {column_avg_of_avgs}\n")

        correlation_results, out_of_bounds_count = calculate_correlation_results(
            correlation_data, column_averages
        )
        correlation_results_output_path = os.path.join(
            output_folder, "correlation_results.txt"
        )
        with open(correlation_results_output_path, "w") as f:
            f.write("Correlation Results\n")
            f.write("==================\n\n")
            for idx, result in enumerate(correlation_results):
                f.write(f"Correlation Result {idx}: {result}\n")
            f.write(
                f"\nOut of bounds instances (deduped by correlation result): {out_of_bounds_count}\n"
            )

        # Find and save peaks
        peaks, message = find_peaks_in_correlation(correlation_results)
        peaks_output_path = os.path.join(output_folder, "peaks.txt")
        with open(peaks_output_path, "w") as f:
            f.write("Peaks in Correlation Results\n")
            f.write("============================\n\n")
            f.write(f"Peaks at indices: {peaks}\n")
            f.write(f"Message: {message}\n")

        # Output one sample calculation step-by-step for verification
        sample_output_path = os.path.join(
            output_folder, "sample_correlation_calculation.txt"
        )
        with open(sample_output_path, "w") as f:
            f.write("Sample Correlation Calculation Step-by-Step\n")
            f.write("===========================================\n\n")
            sample_idx = 0
            sample_correlation_result = 0
            for j in range(len(correlation_data)):
                try:
                    image_value = column_averages[sample_idx + j]
                except IndexError:
                    image_value = 0
                sample_calc = (
                    list(correlation_data.values())[j] - correlation_average
                ) * (image_value - column_avg_of_avgs)
                sample_correlation_result += sample_calc
                f.write(
                    f"Step {j}: ({list(correlation_data.values())[j]} - {correlation_average}) * ({image_value} - {column_avg_of_avgs}) = {sample_calc}\n"
                )
            f.write(f"\nTotal Sample Correlation Result: {sample_correlation_result}\n")


def main():
    parser = argparse.ArgumentParser(
        description="Process image slices to generate column average grayscale values."
    )
    parser.add_argument(
        "input_folder", type=str, help="Folder containing the image slices."
    )
    parser.add_argument(
        "output_folder", type=str, help="Folder to save the output files."
    )
    parser.add_argument(
        "json_path", type=str, help="Path to the JSON file with correlation references."
    )
    parser.add_argument(
        "--num_files", type=int, help="Number of image files to process."
    )

    args = parser.parse_args()
    process_folder(
        args.input_folder, args.output_folder, args.json_path, args.num_files
    )


if __name__ == "__main__":
    main()