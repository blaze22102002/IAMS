from flask import Flask,Response
import json
app = Flask(__name__)

# Make sure IDs are string type
dummy_assets = [
   {
 "asset_id": "A12345",
  "employee_id": "E1001",
  "employee_name": "John Doe",
  "group": "Desktop",
  "business_impact": "High",
  "asset_tag": "AT123456",
  "description": "Laptop - Dell XPS 13",
  "product_name": "Dell XPS 13",
  "serial_number": "SN123456789",
  "remarks": "Newly purchased",
  "status": "Active",
  "it_poc_remarks": "Assigned to employee John Doe",
  "branch_code": "F001"
   },
   {
  "asset_id": "E2ewdfwf1dw",
  "employee_id": "Fgdkj",
  "employee_name": "Nithin",
  "group": "Laptop",
  "business_impact": "High",
  "asset_tag": "USTMUT",
  "description": "Laptop - Dell XPS 13",
  "product_name": "Dell XPS 13",
  "serial_number": "SN123456789",
  "remarks": "Newly purchased",
  "status": "Active",
  "it_poc_remarks": "Assigned to employee John Doe",
  "branch_code": "F113"
   
   }
]



@app.route('/external-api/assets', methods=['GET'])
def get_assets():
    json_data = json.dumps(dummy_assets)
    
    # Return the response with appropriate content-type
    return Response(json_data, mimetype='application/json')

if __name__ == '__main__':
    app.run(port=5001, debug=True)
