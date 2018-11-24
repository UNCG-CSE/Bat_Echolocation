from skimage.io import imread
import numpy as np


def extract_png(file_path):
    img = imread(file_path)

    # img.shape returns a tuple (rows, columns, ...) where rows = height and columns = width
    # print(img.shape)
    # print(f'rows/height: {img.shape[0]}')
    # print(f'columns/width: {img.shape[1]}')

    x_coordinates = []
    y_coordinates = []

    # scan columns/width
    for i in range(0, img.shape[1]):
        # scan rows/height
        for j in range(0, img.shape[0]):
            if (img[j][i][0], img[j][i][1], img[j][i][2]) != (255, 255, 255):
                # print(f'{i}\t{j}')
                x_coordinates.append(i)
                y_coordinates.append(j)

    return x_coordinates, y_coordinates
