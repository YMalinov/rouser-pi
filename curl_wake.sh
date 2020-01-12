#!/bin/bash

SECRET=`cat secret.txt`

curl -d "{\"secret\": \"$SECRET\"}" -H "Content-Type: application/json" -X POST http://localhost:8080/wake
