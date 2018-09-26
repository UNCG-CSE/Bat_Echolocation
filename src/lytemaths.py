# coding: utf-8
import numpy



def dist(ax, ay, bx, by):
    return numpy.sqrt((bx - ax)**2 + (by - ay)**2)

print (dist(1, 2, 3, 4))
