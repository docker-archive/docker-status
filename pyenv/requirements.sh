#!/bin/sh

APPENGINE=google_appengine_1.8.8.zip
STASHBOARD=stashboard-1.5.1

if [ ! -f ../$APPENGINE ]; then
  wget -q http://googleappengine.googlecode.com/files/$APPENGINE
fi
unzip -q ../$APPENGINE

if [ ! -f ../$STASHBOARD.tar.gz ]; then
  wget -O ../$STASHBOARD https://github.com/twilio/stashboard/archive/1.5.1.tar.gz
fi
tar xvf ../$STASHBOARD.tar.gz
mv $STASHBOARD/stashboard .
rm -rf $STASHBOARD
