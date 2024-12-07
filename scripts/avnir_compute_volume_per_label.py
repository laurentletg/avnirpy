#!/usr/bin/env python3

"""
Quality control of labels in NRRD format from 3DSlicer.

If --output_json is provided, a json file will be created with the QC report. If -v WARNING is used,
warning messages will be printed in the console if something is wrong with the label file.
If -v WARNING is not used, the script will stop raising an error if something is wrong with the
label file.

Change the datatype of the labels and volume files for uint8 and int16 respectively.
"""

import argparse
import json

import numpy as np

from avnirpy.io.image import load_image
from avnirpy.io.utils import (
    add_overwrite_arg,
    assert_inputs_exist,
    assert_outputs_exist,
)
from avnirpy.io.utils import add_version_arg


def _build_arg_parser():
    """Build argparser.

    Returns:
        parser (ArgumentParser): Parser built.
    """
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument("input_labels", help="Path to the .nii.gz/.nrrd label image.")
    parser.add_argument("output_json", help="Path to the json file containing volumes.")

    parser.add_argument("--brain_mask", help="Path to the .nii.gz/.nrrd brain mask.")

    add_overwrite_arg(parser)
    add_version_arg(parser)
    return parser


def main():
    parser = _build_arg_parser()
    args = parser.parse_args()

    assert_inputs_exist(parser, args.input_labels, args.brain_mask)
    assert_outputs_exist(parser, args, args.output_json)

    label_data, label_header, _ = load_image(args.input_labels)
    zooms = label_header.get_zooms()

    if args.brain_mask:
        brain_mask_data, mask_header, _ = load_image(args.brain_mask)
        if zooms != mask_header.get_zooms() or not np.allclose(
            label_header.get_best_affine(), mask_header.get_best_affine()
        ):
            raise ValueError("Label and brain mask images are in a different sapce.")

    labels_id = np.unique(label_data[label_data != 0])

    volumes = {}
    for label_id in labels_id:
        if label_id not in volumes:
            volumes[label_id] = {}
        volumes[label_id]["volume"] = np.sum(label_data == label_id) * np.prod(zooms)
        if args.brain_mask:
            volumes[label_id]["volume_normalized"] = (
                np.sum(label_data == label_id) * np.prod(zooms)
            ) / np.sum(brain_mask_data)

    with open(args.output_json, "w") as file:
        json.dump(volumes, file, indent=4)


if __name__ == "__main__":
    main()
