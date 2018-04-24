rm lambda_function.zip
zip lambda_function.zip lambda_function.py
aws lambda update-function-code --function-name FlickSearch --zip-file fileb://lambda_function.zip
echo "DONE"
