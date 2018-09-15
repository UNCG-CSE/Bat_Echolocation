#
# AnabatTools: an R script to read, display and analyse binary files produced by
# the Anabat frequency-division bat recording system.
#    Copyright (C) 2013  Peter D. Wilson
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# See http://www.gnu.org/licenses/ for a copy of the license.
# 
# Development of an Anabat data file reader was undertaken by
# Peter D. Wilson between 11 and 17 December 2013. I can be contacted by
# email: peterbat_at_tpg.com.au (replace _at_ with the ASCII "at" symbol, of course.)
#
# This R script implements and extends earlier software (now lost in unfortunate
# circumstances) written by me in Borland Delphi between 2003 and 2011.
#
# This code (like its lost predecessor) is based on the comprehensive notes on
# Anabat file formats and how to read them, including example C++ code, provided
# by Chris Corben on his website:
#      http://users.lmi.net/corben/fileform.htm#Anabat%20File%20Formats
# (last accessed 5 May 2014).
#

require(stringr)
require(bitops)

# Some constants:
maxSize <- 16384 # As a legacy of its early PC origins, Anabat files represent
# 16kbyte chunks of data

#################################################
getTextHeader <- function(zz)
{
  # At some point in the past it appears that there was a bug in the Anabat
  # software so that null or zero bytes would be written into the text header
  # fields instead of ASCII 32 for a space. It only shows up in a few files for
  # example in the NSW Bat Call Library data set. This patch should fix this
  # problem. PDW 3 May 2014
  stuff <- as.raw(zz[7:281])
  stuff[which(stuff==0)] <- charToRaw(" ")
  
  TAPE <- str_trim(rawToChar(stuff[1:8]))
  DATE <- str_trim(rawToChar(stuff[9:16]))
  LOC <- str_trim(rawToChar(stuff[17:56]))
  SPECIES <- str_trim(rawToChar(stuff[57:106]))
  SPEC <- str_trim(rawToChar(stuff[107:122]))
  NOTE <- str_trim(rawToChar(stuff[123:196]))
  NOTE1 <- str_trim(rawToChar(stuff[197:275]))
  
  # Following lines are for parsing text header in the original data:
  #   TAPE <- str_trim(rawToChar(as.raw(zz[7:14])))
  #   DATE <- str_trim(rawToChar(as.raw(zz[15:22])))
  #   LOC <- str_trim(rawToChar(as.raw(zz[23:62])))
  #   SPECIES <- str_trim(rawToChar(as.raw(zz[63:112])))
  #   SPEC <- str_trim(rawToChar(as.raw(zz[113:128])))
  #   NOTE <- str_trim(rawToChar(as.raw(zz[129:202])))
  #   NOTE1 <- str_trim(rawToChar(as.raw(zz[203:281])))
  
  return(list(TAPE=TAPE,DATE=DATE,LOC=LOC,SPECIES=SPECIES,SPEC=SPEC,NOTE=NOTE,NOTE1=NOTE1)) 
}

#################################################
getDateTime <- function(fileType,p,zz)
{
  if (fileType == 129)
  {
    YEAR <- 0
    MON <- 0
    DAY <- 0
    HOURS <- 0
    MINS <- 0
    SECS <- 0
    HUNDS <- 0
    MICROS <- 0
  }
  else
  {
    # Get file date and time:
    YEAR <- zz[p+6] + 256*zz[p+7]
    MON <- zz[p+8]
    DAY <- zz[p+9]
    HOURS <- zz[p+10]
    MINS <- zz[p+11]
    SECS <- zz[p+12]
    HUNDS <- zz[p+13]
    MICROS <- zz[p+14] + 256*zz[p+15]
  }
  
  return(list(DAY=DAY,MON=MON,YEAR=YEAR,HOURS=HOURS,MIN=MIN,SECS=SECS,HUNDS=HUNDS,MICROS=MICROS))
}


#################################################
getParams <- function(p,zz)
{
  RES1 <- zz[p+2] + 256*zz[p+3]
  
  if (RES1 != 25000)
  {
    timeFactor <- 25000/RES1
  }
  else
  {
    timeFactor <- 1
  }
  
  DIVRAT <- zz[p+4]
  
  VRES <- zz[p+5]
  
  return(list(RES1=RES1,DIVRAT=DIVRAT,VRES=VRES,timeFactor=timeFactor))
}


#################################################
getData129 <- function(p,params,zz)
{
  #print("Start 129")
  #print(paste("  p =",p))
  if ((params$RES1 > 60000) || (params$RES1 < 10000)) return(NULL)
  
  t <- 1
  s <- 0
  lastdif <- 0
  timeData <- rep(0,maxSize)
  showDot <- rep(0,maxSize)
  nBytes <- length(zz)
  time <- 0
  
  while (p < nBytes)
  {
    #print(paste("     while p: p =",p))
    if (zz[p] < 128)
    {
      dif <- zz[p]
      lastdif <- lastdif + dif
      time <- time + floor(params$timeFactor*lastdif+0.5)
      timeData[t] <- time
      t <- t + 1
      p <- p + 1
    }
    else
    {
      if (zz[p] > 248)
      {
        s <- zz[p] - 248
          showDot[t:t+s-1] <- 1
        p <- p + 1
      }
      else
      {
        nShift <- zz[p]
        nShift <- bitwShiftR(nShift,3)
        nShift <- bitwAnd(nShift,as.integer("0x0f"))
        dif <- (bitwAnd(zz[p],as.integer("0x07")))*256 + zz[p+1]
        if (nShift > 0) dif <- bitwShiftL(dif,nShift)
        lastdif <- dif
        time <- time + floor(params$timeFactor*lastdif + 0.5)
        timeData[t] <- time
        t <- t + 1
        p <- p + 2
      }
    }
  }
  
  return(list(timeData=timeData,last.t=t,showDot=showDot))
}



#################################################
getData130 <- function(p,params,fileType,zz)
{
  time <- 0
  dif <- 0
  lastdif <- 0
  t <- 1
  s <- 0
  timeData <- rep(0,maxSize)
  showDot <- rep(2,maxSize)
  showDot[0] <- 0
  showDot[1] <- 1
  
  nBytes <- length(zz)
  
  if ((params$RES1 > 60000) || (params$RES1 < 10000)) return(NULL)
  
  while ((p < nBytes) && (t < maxSize))
  {
    if (zz[p] < 128)
    {
      dif <- zz[p]
      if (dif > 63) dif <- -1*(bitFlip(dif,bitWidth=6) + 1)
      lastdif <- lastdif + dif
      time <- time + floor(params$timeFactor*lastdif + 0.5)
      timeData[t] <- time
      t <- t + 1
      p <- p + 1
    }
    else
    {
      if (zz[p] >= 224 ) # Show status
      {
        if (fileType > 130)
        {
          # Filetpes 131 and 132
          if (p >= nBytes) break
          c <- bitwAnd(zz[p],3)
          s <- zz[p+1]
          if ((t+s-1) > 16384) s <- 16384 - t # limit index to arrays
          showDot[t:(t+s-1)] <- c
          p <- p + 2
        }
        else
        {
          # Filetype 130
          s <- zz[p] - 224
          if ((t+s-1) > 16383) s <- 16384 - t
          showDot[t:(t+s-1)] <- c
          p <- p +1
        }
      }
      else
      {
        if ((128 <= zz[p]) && (zz[p] <= 159))
        {
          if ((p+1) >= nBytes) break
          dif <- 256*bitwAnd(zz[p],as.integer("0x1f")) + zz[p+1]
          lastdif <- dif
          time <- time  + floor(params$timeFactor*lastdif + 0.5)
          timeData[t] <- time
          t <- t + 1
          p <- p + 2
        }
        else
        {
          if ((160 <= zz[p]) && (zz[p] <= 191))
          {
            if ((p+2) >= nBytes) break
            dif  <- 256*256*bitwAnd(zz[p],as.integer("0x1f"))+256*zz[p+1]+zz[p+2]
            lastdif <- dif
            time <- time + floor(params$timeFactor*lastdif + 0.5)
            timeData[t] <- time
            t <- t + 1
            p <- p + 3
            #break
          }
          else
          {
            if ((192 <= zz[p]) && (zz[p] <= 239))
            {
              if ((p+3) >= nBytes) break
              dif <- 256*256*256*bitwAnd(zz[p],as.integer("0x1f"))+256*256*zz[p+1]+256*zz[p+2]+zz[p+3]
              lastdif <- dif
              time <- time + floor(params$timeFactor*lastdif + 0.5)
              timeData[t] <- time
              t <- t + 1
              p <- p + 4
            }
          }
        }
      }
    }
  }
  
  return(list(timeData=timeData,last.t=t,showDot=showDot))
}


#################################################
calcfreq <- function(params,timeData,N)
{
  DIVRAT <- params$DIVRAT
  
  freq <- rep(0,length(timeData))
  showDot <- rep(0,length(timeData))
  t <- 3
  showDot[1] <- 0
  showDot[2] <- 1
  
  Tmin <- ceiling(DIVRAT*4)
  Tmax <- floor(DIVRAT*250)
  if (Tmin < 48) Tmin <- 48
  if (Tmax > 12589) Tmax <- 12589
  
  while(t <= N)
  {
    td <- timeData[t] - timeData[t - 2]
    if ((td >= Tmin) && (td <= Tmax))
    {
      freq[t] <- trunc(DIVRAT*1000000/td)
      showDot[t] <- 2
    }
    else
    {
      freq[t] <- 0
      showDot[t] <- 0
    }
    
    t <- t + 1
  }
  
  return(list(freq=freq,showDot=showDot))
}


#################################################
# Read an Anabat data file and return an S3 object
# containing the recovered data.
#
readAnabat <- function(fileName)
{
  AnabatObj <- list()
  class(AnabatObj) <- "AnabatObj"
  AnabatObj$filename <- fileName
  
  rawData <- readBin(fileName,what="integer",n=16384,size=1,signed=F)
  
  nBytes <- length(rawData)
  
  AnabatObj$fileType <- rawData[4]
  
  # Set Pointer to parameter table:
  p <- rawData[1] + 256*rawData[2] + 1
  
  # Fetch text header:
  AnabatObj$textHeader <- getTextHeader(rawData)
  
  # Get other file  parameters:
  params <- getParams(p,rawData)
  AnabatObj$params <- params
  
  # Set pointer to data block:
  p <- rawData[p] + 256*rawData[p+1]
  
  if (AnabatObj$fileType == 129)
  {
    # Get data from old 129 file
    timeResult <- getData129(p,params,rawData)
  } else
  {
    # Get data from file types 130, 131 & 132
    timeResult <- getData130(p,params,AnabatObj$fileType,rawData)
    #N <- timeResult$last.t
    #timeData <- timeResult$timeData
  }
  
  RES1 <- 25000
  freqResult <- calcfreq(params,timeResult$timeData,timeResult$last.t)
  freq <- freqResult$freq
  showDot <- freqResult$showDot 
  
  badPts <- which(freq == 0)
  freq[badPts] <- NA
  
  AnabatObj$frequencyData <- freq[1:timeResult$last.t]
  AnabatObj$showDot <- showDot[1:timeResult$last.t]
  AnabatObj$timeData <- timeResult$timeData[1:timeResult$last.t]
  
  return(AnabatObj)
}

#################################################
plot.Anabat <- function(AnabatData,showLines=T,showLineType=2,lineColour="black",
                        maxFreq=125000,minFreq=0,cleanBelow=NULL,startTime=NULL,endTime=NULL,
                        dotPch=16,dotCex=0.3,dotCol="blue")
{
  if (class(AnabatData) == "AnabatObj")
  {
    plotFreqData <- AnabatData$frequencyData
    
    if (!is.null(cleanBelow))
    {
      plotFreqData[which(plotFreqData <= cleanBelow)] <- NA
    }
    
    if (is.null(startTime)) startTime <- 0
    if (is.null(endTime)) endTime <- max(AnabatData$timeData/1E06)
    mainText <- AnabatData$textHeader$SPECIES
    plot(AnabatData$timeData/1E06,plotFreqData,
         xlim=c(startTime,endTime),ylim=c(minFreq,maxFreq),
         pch=dotPch,cex=dotCex,col=dotCol,xlab="Time (Seconds)",ylab="Frequency (Hz)",
         main=AnabatData$textHeader$SPECIES)
    
    if (showLines)
    {
      # Find out y-tick positions, but for now...
      nLines <- (maxFreq+10000) %/% 10000
      for (i in 1:nLines)
      {
        abline(h=(i-1)*10000,lty=showLineType,col=lineColour)
      }
    }
    
    
  }
  else
  {
    message("ERROR: AnabatTools:plot.Anabat: Paramater AnabatObj must be class AnabatObj")
    return(NULL)
  }
  
}

