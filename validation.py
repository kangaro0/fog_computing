import cv2, os
import numpy as np
import peakutils as pu
import matplotlib.pyplot as plt

deltas = [
    # Class 1:
    [[26, 36], 6, 20, 200],
    # Class 2:
    [[14, 24], 6, 15, 25]
]


def template(img):
    """Creates a template for the given region_of_interest."""
    img = cv2.equalizeHist(img)
    img = cv2.convertScaleAbs(img, alpha=1, beta=75)
    ret, img = cv2.threshold(img, 160, 255, cv2.THRESH_BINARY)
    kernel1 = cv2.getStructuringElement(cv2.MORPH_CROSS, (3, 3))
    img = cv2.morphologyEx(img, cv2.MORPH_CLOSE, kernel1)
    kernel2 = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (4, 4))
    img = cv2.dilate(img, kernel2)
    img = cv2.Canny(img, 50, 255)
    ret, img = cv2.threshold(img, 127, 255, cv2.THRESH_BINARY)
    return img


def validate(region_of_interest, template_as_image, delta, folder_id, filename):
    """Validates the given roi while using the template."""
    cols, rows = region_of_interest.shape
    # Erstelle Template zum Vergleich
    img_tmp = template(region_of_interest)

    if folder_id:
        filename, extension = filename.split(".")
        try:
            path = os.path.join('media', str(folder_id), 'preprocessing', '{0}_template.{1}'.format(filename, extension))
            cv2.imwrite(path, img_tmp)
        except:
            pass

    if not delta:
        return False

    # Approximiere Rotation
    # res = np.array(image, copy=True)
    E = np.empty(360)
    for d in range(0, 360):
        M = cv2.getRotationMatrix2D((cols / 2, rows / 2), d, 1)
        rot = cv2.warpAffine(img_tmp, M, (cols, rows))
        cmp = cv2.subtract(template_as_image, rot)
        val = np.sum(cmp[:, :])
        E[d] = val
    rot = np.argmin(E)

    # Drehe Originalbild
    M = cv2.getRotationMatrix2D((cols / 2, rows / 2), rot, 1)
    image = cv2.warpAffine(img_tmp, M, (cols, rows))

    # Bestimme Ausschuss
    r = range(delta[0][0], delta[0][1])  # dy
    for dy in r:
        # Mittelpunkt in Dimension x
        mid = int(rows / 2)
        lb = mid - 10
        ub = mid + 10
        # Hole Reihe aus Bild
        row = np.array(image[dy, lb:ub], dtype=np.int)

        # Finde Maxima in Reihe
        indices = pu.indexes(row, thres=0, min_dist=0)

        # Vergleiche gefundene Maxima
        maxima = np.zeros(2)

        l = len(indices)
        for idx1, v1 in enumerate(indices):
            # Falls am letzten Element angekommen, breche Schleife ab (nur vorwaertsvergleich)
            # oder breche ab, falls gueltige Kombination von Maxima gefunden wurde
            if idx1 == l - 1:
                break

            for idx2, v2 in enumerate(indices[idx1 + 1:l]):
                diff_y = abs(row[v2] - row[v1])
                diff_x = abs(v2 - v1)
                if diff_x > delta[1] and diff_x < delta[2] and diff_y < delta[3]:
                    maxima[0] = v1
                    maxima[1] = v2
                    return True

    return False
