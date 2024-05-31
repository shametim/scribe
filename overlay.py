import os
import logging
import json
from PIL import Image, ImageDraw

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


def read_shift_from_json(json_path):
    logging.info(f"Reading shift value from {json_path}")
    with open(json_path, "r") as f:
        data = json.load(f)
    num_keys = len(data)
    shift = num_keys // 2
    logging.info(f"Calculated shift value: {shift}")
    return shift


def overlay_peaks_on_images(input_folder, output_base_folder, json_path):
    slice_files = sorted(
        [
            f
            for f in os.listdir(input_folder)
            if f.startswith("slice_") and f.endswith(".bmp")
        ]
    )
    shift = read_shift_from_json(json_path)

    for slice_file in slice_files:
        slice_index = int(
            slice_file.split("_")[-1].split(".")[0]
        )  # Extract slice index from filename
        slice_folder_path = os.path.join(output_base_folder, f"slice_{slice_index}")
        os.makedirs(slice_folder_path, exist_ok=True)

        # Find the image file in the input folder
        slice_path = os.path.join(input_folder, slice_file)

        # Read peaks.txt to get the peak indices
        peaks_file_path = os.path.join(slice_folder_path, "peaks.txt")
        if not os.path.exists(peaks_file_path):
            logging.warning(f"Peaks file not found: {peaks_file_path}")
            continue

        with open(peaks_file_path, "r") as peaks_file:
            lines = peaks_file.readlines()
            peak_indices = []
            for line in lines:
                if line.startswith("Peaks at indices"):
                    peak_indices = [
                        int(x) for x in line.split(": ")[1].strip("[]\n").split(", ")
                    ]
                    break

        if len(peak_indices) < 2:
            logging.warning(f"Not enough peaks found in {peaks_file_path}")
            continue

        logging.info(
            f"Overlaying peaks for {slice_file}: {peak_indices} with shift {shift}"
        )

        # Overlay peak indices on the image
        with Image.open(slice_path) as img:
            draw = ImageDraw.Draw(img)
            width, height = img.size
            for peak in peak_indices:
                shifted_peak = peak + shift
                if 0 <= shifted_peak < width:
                    draw.line(
                        (shifted_peak, 0, shifted_peak, height), fill="red", width=1
                    )

            overlay_image_path = os.path.join(
                slice_folder_path, f"overlay_{slice_file}"
            )
            img.save(overlay_image_path)
            logging.info(f"Saved overlay image to {overlay_image_path}")


def main():
    input_folder = "slices"
    output_base_folder = "output_slices"
    json_path = "correlation_references.json"

    overlay_peaks_on_images(input_folder, output_base_folder, json_path)


if __name__ == "__main__":
    main()