#!/bin/bash

rm docs/*.txt

cd src
MODULES=`find . -name '*.py' -print | sed -e 's/\.\///' | sed -e 's/\//./g' | sed -e 's/\.py//'`
for m in $MODULES; do
	echo $m
	python3 -m pydoc $m | head --lines=-4 > "../docs/${m}.txt" 
done