# 09092018 Yang Peng
source("C:\\Users\\Administrator\\Dropbox\\CSC 505 Data Science\\Project\\AnabatTools.R")
chirp <- readAnabat("C:\\Users\\Administrator\\Dropbox\\CSC 505 Data Science\\Project\\data0\\P7132033.37#")

x <- data.frame(chirp$timeData,chirp$frequencyData)
colnames(x) <- c("Time","Frequency")
write.csv(x,file = "C:\\Users\\Administrator\\Dropbox\\CSC 505 Data Science\\Project\\data0\\P7132033_37.csv",row.names = F)
