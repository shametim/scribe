import argparse
import logging
import os
from PIL import Image
import webbrowser

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


def slice_image(input_path, height, output_folder):
    logging.info(f"Reading image from {input_path}")
    img = Image.open(input_path)
    img_width, img_height = img.size
    total_pixels = img_width * img_height

    logging.info(f"Image size: {img_width}x{img_height}")
    logging.info(f"Total pixels in the input image: {total_pixels}")

    slice_count = 0
    for top in range(0, img_height, height):
        if top + height > img_height:
            logging.info(
                "Remaining part of the image is less than the specified height. Stopping slicing."
            )
            break

        bottom = top + height
        box = (0, top, img_width, bottom)
        slice_img = img.crop(box)
        slice_path = os.path.join(output_folder, f"slice_{slice_count}.bmp")
        slice_img.save(slice_path)
        slice_pixels = img_width * height
        logging.info(
            f"Saved slice {slice_count} to {slice_path} with {slice_pixels} pixels"
        )
        slice_count += 1

    return slice_count, output_folder, total_pixels


def main():
    parser = argparse.ArgumentParser(
        description="Slice an image into horizontal strips."
    )
    parser.add_argument("input_image", type=str, help="Path to the input image file.")
    parser.add_argument("height", type=int, help="Height of each slice in pixels.")
    parser.add_argument(
        "output_folder", type=str, help="Folder to save the output slices."
    )

    args = parser.parse_args()

    slice_count, output_folder, total_pixels = slice_image(
        args.input_image, args.height, args.output_folder
    )

    if slice_count > 0:
        first_slice_path = os.path.join(output_folder, "slice_0.bmp")
        logging.info(f"Opening the first slice {first_slice_path}")
        webbrowser.open(first_slice_path)
    else:
        logging.warning("No slices were created.")


if __name__ == "__main__":
    main()