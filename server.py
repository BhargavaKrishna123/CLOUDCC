from flask import Flask, request, Response
import boto3
import os

app = Flask(__name__)

# AWS setup
AWS_REGION = 'us-east-1'
ASU_ID = os.environ.get('ASU_ID', '1233283339')  # Replace or set as environment variable
S3_BUCKET = f"{ASU_ID}-in-bucket"
SIMPLEDB_DOMAIN = f"{ASU_ID}-simpleDB"

session = boto3.Session(
    aws_access_key_id="AKIA4RCAOGXU2E3DFERI",
    aws_secret_access_key="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",
    region_name="us-east-1"
)

# Initialize boto3 clients
s3_client = session.client('s3')
sdb_client = session.client('sdb')

@app.route('/', methods=['POST'])
def handle_request():
    # 1. Extract the image file from the request
    if 'inputFile' not in request.files:
        return Response("Missing inputFile", status=400)
    file = request.files['inputFile']
    file_name = os.path.splitext(file.filename)[0]
    
    # 2. Upload the image to the S3 bucket
    try:
        s3_client.upload_fileobj(file, S3_BUCKET, file_name)
    except Exception as e:
        return Response(f"Error uploading file: {str(e)}", status=500)
    
    # 3. Query SimpleDB for the classification result
    try:
        response = sdb_client.get_attributes(
            DomainName=SIMPLEDB_DOMAIN,
            ItemName=file_name,
            AttributeNames=['prediction']
        )
        attributes = response.get('Attributes', [])
        # Extract the prediction from the returned attributes
        prediction = next((attr['Value'] for attr in attributes if attr['Name'] == 'prediction'), 'Unknown')
    except Exception as e:
        return Response(f"Error querying SimpleDB: {str(e)}", status=500)
    
    # 4. Return the result in plain text in the required format
    result_text = f"{file_name}:{prediction}"
    return Response(result_text, mimetype='text/plain')

if __name__ == '__main__':
    # Enable threaded mode for handling concurrent requests
    app.run(host='0.0.0.0', port=8000, threaded=True)