import numpy as np, matplotlib.pyplot as plt, pandas as pd

def least_squares_coefficients(x, y):

    # number of observations
    # len(x) = len(y)
    n = len(x)

    # separate means of x and y values
    mean_x = np.mean(x)
    mean_y = np.mean(y)

    # sum of cross-deviations of y and x
    cross_deviation_xy = np.sum(y * x - n * mean_x * mean_y)

    # sum of the squared deviations of x
    deviation_squared_xx = np.sum(x ** 2 - n * (mean_x ** 2))

    slope = cross_deviation_xy / deviation_squared_xx
    y_int = mean_y - slope * mean_x

    return (y_int, slope)

def plot_ls_regression_line(x, y, c):

    #obtain scatter plot
    plt.scatter(x, y)

    # get the equation of the line
    predicted_y = c[0] + c[1] * x

    # plot the line
    plt.plot(x, predicted_y, color="b")

    plt.xlabel('time')
    plt.ylabel('frequency')

    plt.show()

def get_linreg(x, y):
    coefficients = least_squares_coefficients(x, y)
    print("y-intercept: %f" % coefficients[0])
    print("slope: %f" % coefficients[1])
    print("linear regression line: predicted y = %f + %fx" % (coefficients[0], coefficients[1]))
    plot_ls_regression_line(x, y, coefficients)