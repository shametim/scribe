import os
import logging
import csv
import numpy as np
import matplotlib.pyplot as plt
from scipy.ndimage import gaussian_filter1d
from scipy.signal import find_peaks
from statistics import stdev

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


def read_correlation_results(file_path):
    logging.info(f"Reading correlation results from {file_path}")
    correlation_results = []
    with open(file_path, "r") as f:
        lines = f.readlines()
        for line in lines:
            if line.startswith("Correlation Result"):
                try:
                    result = float(line.split(": ")[1])
                    correlation_results.append(result)
                except (IndexError, ValueError) as e:
                    logging.warning(
                        f"Skipping line due to format error: {line.strip()}"
                    )
    return correlation_results


def find_peaks_in_correlation(correlation_results):
    # Apply Gaussian smoothing
    smoothed = gaussian_filter1d(correlation_results, sigma=2)

    # Find peaks
    peaks, _ = find_peaks(smoothed)

    # Sort peaks by their heights in descending order
    sorted_peaks = sorted(peaks, key=lambda x: smoothed[x], reverse=True)

    if len(sorted_peaks) > 2:
        return sorted(sorted_peaks[:2]), f"More than 2 peaks found: {sorted_peaks}"
    elif len(sorted_peaks) < 2:
        return sorted_peaks, "Less than 2 peaks found."
    else:
        return sorted(sorted_peaks), "Two peaks found."


def plot_combined_chart(correlation_results, peaks, output_image_path):
    smoothed = gaussian_filter1d(correlation_results, sigma=2)

    plt.figure(figsize=(10, 5))
    plt.plot(smoothed, label="Correlation Results", linestyle="--")
    plt.scatter(peaks, [smoothed[p] for p in peaks], color="red", zorder=5)
    for peak in peaks:
        plt.annotate(
            f"Peak {peak}",
            xy=(peak, smoothed[peak]),
            xytext=(peak, smoothed[peak] + 10),
            arrowprops=dict(facecolor="black", shrink=0.05),
        )
    plt.xlabel("Index")
    plt.ylabel("Correlation Result")
    plt.title("Correlation Results with Peaks")
    plt.legend()
    plt.savefig(output_image_path)
    logging.info(f"Combined plot saved to {output_image_path}")
    plt.close()


def process_correlation_results(output_base_folder):
    slice_folders = [
        os.path.join(output_base_folder, folder)
        for folder in os.listdir(output_base_folder)
        if os.path.isdir(os.path.join(output_base_folder, folder))
    ]

    peak_indices_1 = []
    peak_indices_2 = []
    peak_values_1 = []
    peak_values_2 = []

    table_rows = []

    for slice_folder in slice_folders:
        correlation_results_path = os.path.join(slice_folder, "correlation_results.txt")
        if not os.path.exists(correlation_results_path):
            logging.warning(f"File not found: {correlation_results_path}")
            continue

        correlation_results = read_correlation_results(correlation_results_path)

        peaks, message = find_peaks_in_correlation(correlation_results)
        logging.info(message)

        if len(peaks) == 2:
            peak_indices_1.append(peaks[0])
            peak_values_1.append(correlation_results[peaks[0]])
            peak_indices_2.append(peaks[1])
            peak_values_2.append(correlation_results[peaks[1]])
            slice_index = int(os.path.basename(slice_folder).split("_")[1])
            table_rows.append(
                (
                    slice_index,
                    peaks[0],
                    correlation_results[peaks[0]],
                    peaks[1],
                    correlation_results[peaks[1]],
                )
            )
        else:
            slice_index = int(os.path.basename(slice_folder).split("_")[1])
            table_rows.append((slice_index, None, None, None, None))

        # Save peaks information
        peaks_output_path = os.path.join(slice_folder, "peaks.txt")
        with open(peaks_output_path, "w") as f:
            f.write("Peaks in Correlation Results\n")
            f.write("============================\n\n")
            f.write(f"Peaks at indices: {peaks}\n")
            f.write(f"Message: {message}\n")

        # Plot combined chart
        combined_plot_path = os.path.join(slice_folder, "combined_plot.png")
        plot_combined_chart(correlation_results, peaks, combined_plot_path)

    # Sort table rows by slice index
    table_rows.sort(key=lambda x: x[0])

    # Output the table and statistics into a CSV file
    csv_output_path = os.path.join(output_base_folder, "peaks_and_statistics.csv")
    with open(csv_output_path, "w", newline="") as csvfile:
        csvwriter = csv.writer(csvfile)
        csvwriter.writerow(
            ["Slice Index", "P1 Index", "P1 Value", "P2 Index", "P2 Value"]
        )
        for row in table_rows:
            csvwriter.writerow(row)

        if peak_values_1 and peak_values_2:
            value_stdev_1 = stdev(peak_values_1)
            value_stdev_2 = stdev(peak_values_2)
            index_stdev_1 = stdev(peak_indices_1)
            index_stdev_2 = stdev(peak_indices_2)
            csvwriter.writerow([])
            csvwriter.writerow(["Statistics"])
            csvwriter.writerow(["Standard Deviation of P1 Values", value_stdev_1])
            csvwriter.writerow(["Standard Deviation of P1 Indices", index_stdev_1])
            csvwriter.writerow(["Standard Deviation of P2 Values", value_stdev_2])
            csvwriter.writerow(["Standard Deviation of P2 Indices", index_stdev_2])
        else:
            logging.warning("Not enough peak data to calculate statistics.")


def main():
    output_folder = "output_slices"
    process_correlation_results(output_folder)


if __name__ == "__main__":
    main()