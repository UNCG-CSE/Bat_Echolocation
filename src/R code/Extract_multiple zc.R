#Get script from online http://www.peterwilson.id.au/Rcode/AnabatTools.R
#AnabatTools.R Copyright (C) 2013  Peter D. Wilson

#Load AnabatTools.R script that was saved (anywhere) in your computer
source("~/R/win-library/3.3/AnabatTools.R")

#Set and process all files in working directory
setwd("C:/Users/bty/Desktop/CSC505/Processing zc data/Bat data_Trial size")
filenames <- dir(pattern =".zc")

for(i in 1:length(filenames)){
  extract_zc<-readAnabat(filenames[i])
  outfile<-substr(filenames,1,nchar(filenames)-3)
  dataframe<-data.frame(Filename=rep(outfile[i],length(extract_zc$timeData)),
    Time=extract_zc$timeData, Frequency=extract_zc$frequencyData)
  write.csv(dataframe,file=paste0(outfile[i],'.csv'),row.names=FALSE)
}
   

