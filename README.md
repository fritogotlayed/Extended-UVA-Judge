# Extended UVa Judge

## Inspiration
While reading "Programming Challenges - The Programming Content Training Manual"
by Steven S. Skiena and Miguel A. Revilla I was inspired to use the problems in
the book as an avenue to learn other programming languages. Traditionally I started
as a C# developer and played around with these problems. The entire time I wished
there was a place to submit my code in order to verify it against the judge program
data. Since the ACM competition only supports C, C++, Java and Pascal it seemed I
did not have that option.

Fast forward many years and my employment asked me to being learning Python. For
whatever reason I was drawn back to the problems in the Programming Challenges book.
Again, I was out of luck for a place to submit my code. This time though I had an
idea. Why not create a framework that allows anyone to add in languages and have them
checked against the same inputs and outputs.

## Goals
The goal of this project is, as stated above, is to create a framework that allows
a developer to write some code and submit it to an electronic judge that accepts more
languages than the standard ACM programming competition rules allow. If this judge
were incorporated into a ACM-like programming competition, the intent is to be a
back-end automated verification tool, possibly as a fleet.

## Getting Started
* Developed and Tested w/ Python 3.6.1 with python submissions

TODO:

## Configuration
TODO: I'm going to try to document the config.yml inline :-)

## Example Usage
The Post
```bash
curl -X POST \
  http://localhost:80/api/v1/problem/100/py2/test \
  -H 'cache-control: no-cache' \
  -H 'content-type: multipart/form-data; boundary=----WebKitFormBoundary7MA4YWxkTrZu0gW' \
  -F main.py=@main.py
```
The Response Object
```bash
{
  "code": "AC",
  "message": "Accepted",
  "output": "<run time / compile time error details, optional>",
  "description": "<Helpful message on submission errors, optional>"
}
```

## Resources
* [UVa Problems](https://uva.onlinejudge.org/index.php?option=com_onlinejudge&Itemid=8&category=1)
* [UVa Solution Generator](http://uvatoolkit.com/problemssolve.php)
* [uDebug](https://www.udebug.com/UVa/100)
