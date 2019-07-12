import numpy as np
import cv2
from cnn import MODEL


templates = [
    'templates/rotation/rot_12.jpg',
    'templates/rotation/rot_22.jpg',
]

deltas = [
    # Class 1:
    [[26, 36], 6, 16, 25],
    # Class 2:
    [[14, 24], 6, 15, 25]
]


def declare_template_class(region_of_interest):
    """Declares the clamp class of the given region of interest."""
    roi = np.asarray(region_of_interest)
    roi = roi.reshape(1, 128, 128, 1)

    template_class = MODEL.predict_classes([roi, ])[0]
    if template_class == 0:
        return False, False

    delta = deltas[template_class - 1]
    template_as_image = cv2.imread(templates[template_class - 1], cv2.IMREAD_GRAYSCALE)

    return template_as_image, delta
