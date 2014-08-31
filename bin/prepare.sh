#!/bin/bash

ZERO_HOME=`pwd`

mkdir -p tmp
cd tmp

# google-test setup
if [ ! -f $ZERO_HOME/lib/libgtest.a ]; then
    if [ ! -d gtest-1.7.0 ]; then
        if [ ! -f gtest-1.7.0.zip ]; then
            wget http://github.com/ralphjzhang/minus-one/raw/master/gtest-1.7.0.zip
        fi
        unzip gtest-1.7.0.zip
    fi
    cd gtest-1.7.0
    cmake .
    make clean && make
    cp libgtest.a  $ZERO_HOME/lib
    cp libgtest_main.a $ZERO_HOME/lib
    cp -rf include/gtest $ZERO_HOME/include
fi

# clean up
cd $ZERO_HOME
rm -rf tmp

