# from skimage.io import imread


# def extract_png(file_path):
#     img = imread(file_path)
#
#     x_coordinates = []
#     y_coordinates = []
#
#     # scan columns/width
#     for i in range(0, img.shape[1]):
#         # scan rows/height
#         for j in range(0, img.shape[0]):
#             if (img[j][i][0], img[j][i][1], img[j][i][2]) != (255, 255, 255):
#                 # print(f'{i}\t{j}')
#                 x_coordinates.append(i)
#                 y_coordinates.append(j)
#
#     return x_coordinates, y_coordinates


# function to encode png image from file_path into byte data
def encode_png_to_blob(file_path):
    with open(file_path, 'rb') as img:
        file = img.read()
        byte_array = bytearray(file)

    # print(byte_array)
    return byte_array


# function to create and write into a new png file "img_name.png" from obtained byte data
def decode_blob_to_png(img_name, byte_array):
    file = open('{}'.format(img_name), 'wb+')
    file.write(byte_array)
    file.close()
