# Bat_Echolocation

## Introduction
This project aims to identify and classify real bat calls according to the purpose of that call, ranging from echolocation to mating. The calls are stored in Zero Crossing format; the data will have to be cleaned up as it contains a significant amount of noise. Once the data is cleaned, the bat calls will be clustered according to their shapes, and then classified for future scientific research. If all goes well, we will also be able to predict the nature of the calls based on metadata such as the time, location, and season that the calls were recorded in. The project is written in Python.

<img width="600" alt="bat echolocation" src="https://www.batconservationireland.org/wp-content/uploads/2013/10/EcholocationII.jpg">

## Members

[Hadi Soufi](https://github.com/HadiSoufi)

[Yang Peng](https://github.com/yangp18)

[Bety Rostandy](https://github.com/brostandy)

[Thien Le](https://github.com/InsertGitHubUsernameHere)

[Kevin Keomalaythong](https://github.com/kkeomalaythong)

## Goals

1. [Extraction](https://plot.ly/~souhad/13/zc-noisy-zc-smoothed-zc-noiseless/):
Extract meaningful signal from noise.

2. [Clustering](https://github.com/UNCG-CSE/Bat_Echolocation/blob/master/src/clustering_yang.ipynb):
Categorize the extracted calls into different types using clustering techniques.

3. [Classification](https://github.com/UNCG-CSE/Bat_Echolocation/blob/master/src/clustering_yang.ipynb):
Classify if a Bat Echolocation(zero-crossing files) contains abnormal calls(i.e. social calls, foraging calls).
