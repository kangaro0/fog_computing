import math
import cv2
import os
import numpy as np
from werkzeug.utils import secure_filename


def preprocess(file, demonstrate=None):
    filename = secure_filename(file.filename)
    nparr = np.frombuffer(file.read(), np.uint8)
    img = cv2.imdecode(nparr,
                       cv2.IMREAD_GRAYSCALE)

    # roi =  region of interest
    result_roi = []
    final_filename = None

    scale = 20

    height, width = img.shape

    img_scaled = cv2.resize(img,
                            (int(width / scale), int(height / scale)),
                            interpolation=cv2.INTER_CUBIC)

    img_blurred = cv2.GaussianBlur(img_scaled,
                                   ksize=(3, 3),
                                   sigmaX=2,
                                   sigmaY=2)

    hough_circles = cv2.HoughCircles(img_blurred,
                                     cv2.HOUGH_GRADIENT,
                                     1,
                                     int(400.0 / scale),
                                     param1=100,
                                     param2=20,
                                     minRadius=int(250.0 / scale),
                                     maxRadius=int(450.0 / scale))

    try:
        circles = hough_circles[0]
    except:
        # if no circles are found we don't need to continue
        return False, False

    folder_id = None
    if demonstrate:
        # CREATE FOLDER
        # get all media folders
        media_folders = os.listdir('media')
        media_folders_cleared = media_folders.copy()

        # exclude all non integer folders
        for folder in media_folders:
            try:
                inted_folder = int(folder)
            except:
                inted_folder = None

            if not inted_folder:
                media_folders_cleared.remove(folder)

        media_folders_cleared.sort(key=int)

        idx = 0
        for idx, folder in enumerate(media_folders_cleared, start=1):
            if str(idx) != str(folder):
                folder_id = idx
                break

        if not folder_id:
            folder_id = idx + 1

        # create the directory
        try:
            os.mkdir(os.path.join('media',
                                  str(folder_id)))
        except:
            pass

        # SAVE PICTURES
        img_colored = cv2.imdecode(nparr,
                                   cv2.IMREAD_COLOR)

        filepath = os.path.join('media',
                                str(folder_id),
                                filename)

        cv2.imwrite(filepath,
                    img_colored)

        # CREATE SUBDIRECTORY - preprocess
        filepath_without_extension, extension = filepath.split('.')
        filepath_only_path, filename = os.path.split(filepath_without_extension)
        folder_name = 'preprocessing'

        final_path = os.path.join(filepath_only_path,
                                  folder_name)

        # create the directory
        try:
            os.mkdir(final_path)
        except:
            pass

    for idx, circle in enumerate(circles):
        if idx > 2:
            continue

        x, y, rad = circle

        rad = rad * 1.5
        x = int(x * scale)
        y = int(y * scale)
        rad = int(rad * scale)

        roi = img[y - rad:y + rad, x - rad:x + rad]

        kernel1 = cv2.getStructuringElement(cv2.MORPH_RECT,
                                            (5, 5))
        roi = cv2.dilate(roi,
                         kernel1)

        kernel2 = cv2.getStructuringElement(cv2.MORPH_ELLIPSE,
                                            (15, 15))
        roi = cv2.erode(roi,
                        kernel2)

        roi = cv2.dilate(roi,
                         kernel2)

        roi = cv2.GaussianBlur(roi,
                               ksize=(3, 3),
                               sigmaX=2,
                               sigmaY=2)

        subcircles = cv2.HoughCircles(roi,
                                      cv2.HOUGH_GRADIENT,
                                      1,
                                      400,
                                      param1=100,
                                      param2=40,
                                      minRadius=250,
                                      maxRadius=450)

        subcircle = []
        try:
            subcircle = subcircles[0][0]
        except TypeError:
            continue

        # cut out square with side length of circle diameter
        x, y, rad = subcircle
        roi = roi[int(y - rad):int(y + rad),
                  int(x - rad):int(x + rad)]
        roi = cv2.resize(roi,
                         (128, 128))

        roi_height, roi_width = roi.shape
        rad = int(roi_width / 2)
        rad_corner = int(math.ceil(math.sqrt(2 * math.pow(rad, 2))))

        center = (roi_width // 2, roi_height // 2)
        cv2.circle(roi,
                   center,
                   rad + (rad_corner - rad) // 2,
                   color=(0, 0, 0),
                   thickness=(rad_corner - rad))

        if demonstrate:
            final_filename = '{0}_{1}.{2}'.format(filename, idx + 1, extension)
            final_filepath = os.path.join(final_path,
                                          final_filename)
            cv2.imwrite(final_filepath, roi)

        result_roi.append((final_filename, roi))

    if len(result_roi) == 0:
        return False, False

    return result_roi, folder_id
