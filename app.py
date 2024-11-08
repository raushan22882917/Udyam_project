# udyam\app.py

from flask import Flask, request, jsonify, abort
from automate_form import initiate_adhar, submit_otp, submit_pan, submit_form, automate_form_next, get_captcha_url, submit_captcha_and_complete
from database import UdyamRegistration, get_db_session, Vendor, FormStatus, Gender, SocialCategory
import re
import os
import logging
from functools import wraps
from werkzeug.exceptions import HTTPException
import threading
import uuid
from datetime import datetime
import json

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "7X9Y2Z4A1B8C3D6E5F")

logging.basicConfig(level=logging.DEBUG)
DEBUG_MODE = os.environ.get("DEBUG_MODE", "False").lower() == "true"

def validate_aadhaar(aadhaar):
    return bool(re.match(r"^\d{12}$", aadhaar))

def validate_name(name):
    return bool(re.match(r"^[a-zA-Z\s]{1,100}$", name))

def validate_api_key(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        if not api_key:
            return jsonify({"status": "error", "message": "Missing API key"}), 401
        
        db_session = get_db_session()
        try:
            vendor = db_session.query(Vendor).filter_by(api_key=api_key).first()
            if not vendor:
                return jsonify({"status": "error", "message": "Invalid API key"}), 401
            
            if vendor.api_key_expires_at < datetime.utcnow():
                return jsonify({"status": "error", "message": "API key has expired"}), 401
            
            request.vendor_id = vendor.id
            
            return f(*args, **kwargs)
        finally:
            db_session.close()
    
    return decorated_function

class InvalidAPIUsage(Exception):
    status_code = 400

    def __init__(self, message, status_code=None, payload=None):
        super().__init__()
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        rv = dict(self.payload or ())
        rv['message'] = self.message
        return rv

@app.errorhandler(InvalidAPIUsage)
def invalid_api_usage(e):
    return jsonify(e.to_dict()), e.status_code

@app.errorhandler(Exception)
def handle_exception(e):
    if isinstance(e, HTTPException):
        response = e.get_response()
        response.data = json.dumps({
            "code": e.code,
            "name": e.name,
            "description": e.description,
        })
        response.content_type = "application/json"
    else:
        response = jsonify({
            "code": 500,
            "name": "Internal Server Error",
            "description": str(e),
        })
        response.status_code = 500
    return response

def process_registration(registration_id):
    session = get_db_session()
    try:
        registration = session.query(UdyamRegistration).filter_by(id=registration_id).first()
        if not registration:
            app.logger.error(f"Registration not found for ID: {registration_id}")
            return

        # Step 1: Initiate Aadhaar
        result = initiate_adhar(registration.aadhaar, registration.name)
        if "Error" in result:
            raise Exception(result)
        
        registration.form_status = FormStatus.AWAITING_OTP
        session.commit()

        # Wait for OTP submission (this will be handled by a separate API endpoint)
        app.logger.info(f"Waiting for OTP submission for registration ID: {registration_id}")
        return

    except Exception as e:
        registration.form_status = FormStatus.ERROR
        session.commit()
        app.logger.error(f"Error processing registration {registration_id}: {str(e)}")
    finally:
        session.close()

def continue_registration_after_otp(registration_id):
    session = get_db_session()
    try:
        registration = session.query(UdyamRegistration).filter_by(id=registration_id).first()
        if not registration:
            app.logger.error(f"Registration not found for ID: {registration_id}")
            return

        # Step 2: Submit PAN
        pan_data = {
            "pan": registration.pan,
            "pan_name": registration.pan_name,
            "dob": registration.dob,
            "have_gstin": registration.have_gstin
        }
        result = submit_pan(pan_data)
        if "Error" in result:
            raise Exception(result)
        
        # Step 3: Submit Form
        form_data = {
            "mobile": registration.mobile,
            "email": registration.email,
            "social_category": registration.social_category.value,
            "gender": registration.gender.value,
            "specially_abled": "Y" if registration.specially_abled else "N",
            "enterprise_name": registration.enterprise_name,
            "unit_name": registration.unit_name,
            "premises_number": registration.premises_number,
            "building_name": registration.building_name,
            "village_town": registration.village_town,
            "block": registration.block,
            "road_street_lane": registration.road_street_lane,
            "city": registration.city,
            "state": registration.state,
            "district": registration.district,
            "pincode": registration.pincode,
            "official_premises_number": registration.official_premises_number,
            "official_address": registration.official_address,
            "official_town": registration.official_town,
            "official_block": registration.official_block,
            "official_lane": registration.official_lane,
            "official_city": registration.official_city,
            "official_state": registration.official_state,
            "official_district": registration.official_district,
            "official_pincode": registration.official_pincode,
            "date_of_incorporation": registration.date_of_incorporation,
            "date_of_commencement": registration.date_of_commencement,
            "bank_name": registration.bank_name,
            "account_number": registration.account_number,
            "ifsc_code": registration.ifsc_code
        }
        result = submit_form(form_data)
        if "Error" in result:
            raise Exception(result)
        
        # Step 4: Submit Additional Details
        additional_data = {
            "major_activity": registration.major_activity,
            "second_form_section": registration.second_form_section,
            "nic_codes": registration.nic_codes,
            "employee_counts": {
                "male": registration.male_employees,
                "female": registration.female_employees,
                "others": registration.other_employees
            },
            "investment_data": {
                "wdv": registration.investment_wdv,
                "exclusion_cost": registration.investment_exclusion_cost
            },
            "turnover_data": {
                "total_turnover": registration.total_turnover,
                "export_turnover": registration.export_turnover
            },
            "district": registration.district
        }
        result = automate_form_next(**additional_data)
        if result['status'] == 'error':
            raise Exception(result['message'])
        
        # Update registration status
        registration.form_status = FormStatus.COMPLETED
        session.commit()
    except Exception as e:
        registration.form_status = FormStatus.ERROR
        session.commit()
        app.logger.error(f"Error continuing registration {registration_id}: {str(e)}")
    finally:
        session.close()

@app.route("/api/udyam/register", methods=["POST"])
@validate_api_key
def register_udyam():
    data = request.json
    if not isinstance(data, list):
        data = [data]  # Convert single registration to list
    
    session = get_db_session()
    registration_ids = []
    
    try:
        for registration_data in data:
            registration_id = str(uuid.uuid4())
            registration_data['id'] = registration_id
            registration_data['vendor_id'] = request.vendor_id
            
            # Convert gender to enum
            registration_data['gender'] = Gender(registration_data['gender'])
            
            # Convert social_category to enum
            registration_data['social_category'] = SocialCategory(registration_data['social_category'])
            
            # Convert specially_abled to boolean
            if isinstance(registration_data['specially_abled'], bool):
                registration_data['specially_abled'] = registration_data['specially_abled']
            elif isinstance(registration_data['specially_abled'], str):
                registration_data['specially_abled'] = registration_data['specially_abled'].lower() == 'true'
            else:
                registration_data['specially_abled'] = False
            
            new_registration = UdyamRegistration(**registration_data)
            session.add(new_registration)
            registration_ids.append(registration_id)
        
        session.commit()
        
        # Start the registration process for each registration in separate threads
        for reg_id in registration_ids:
            threading.Thread(target=process_registration, args=(reg_id,)).start()
        
        return jsonify({
            "status": "success", 
            "message": f"{len(registration_ids)} registrations initiated successfully",
            "registration_ids": registration_ids
        }), 202
    except Exception as e:
        session.rollback()
        app.logger.error(f"Error in register_udyam: {str(e)}")
        raise InvalidAPIUsage(str(e), status_code=400)
    finally:
        session.close()

@app.route("/api/udyam/submit_otp", methods=["POST"])
@validate_api_key
def submit_otp_route():
    data = request.json
    if 'otp' not in data or 'registration_id' not in data:
        raise InvalidAPIUsage("OTP and registration ID are required", status_code=400)
    
    registration_id = data['registration_id']
    db_session = get_db_session()
    try:
        registration = db_session.query(UdyamRegistration).filter_by(id=registration_id, vendor_id=request.vendor_id).first()
        if not registration:
            raise InvalidAPIUsage("Registration not found", status_code=404)
        
        if registration.form_status != FormStatus.AWAITING_OTP:
            raise InvalidAPIUsage("Registration is not awaiting OTP", status_code=400)
        
        result = submit_otp(data['otp'])
        if "Error" in result:
            raise InvalidAPIUsage(result, status_code=500)
        
        registration.form_status = FormStatus.OTP_VERIFIED
        db_session.commit()
        
        # Continue with the rest of the registration process
        threading.Thread(target=continue_registration_after_otp, args=(registration_id,)).start()
        
        return jsonify({"status": "success", "message": "OTP verified, continuing registration"})
    except Exception as e:
        db_session.rollback()
        raise InvalidAPIUsage(str(e), status_code=500)
    finally:
        db_session.close()

@app.route("/api/udyam/status/<registration_id>", methods=["GET"])
@validate_api_key
def get_registration_status(registration_id):
    session = get_db_session()
    try:
        registration = session.query(UdyamRegistration).filter_by(id=registration_id, vendor_id=request.vendor_id).first()
        if not registration:
            raise InvalidAPIUsage("Registration not found", status_code=404)
        
        status_info = {
            "status": "success",
            "registration_id": registration_id,
            "form_status": registration.form_status.value
        }

        if registration.form_status == FormStatus.ERROR:
            status_info["error_details"] = "Error occurred during registration process"

        return jsonify(status_info)
    except Exception as e:
        raise InvalidAPIUsage(str(e), status_code=400)
    finally:
        session.close()

@app.route("/api/udyam/retry", methods=["POST"])
@validate_api_key
def retry_registration():
    data = request.json
    if 'registration_id' not in data:
        raise InvalidAPIUsage("Registration ID is required", status_code=400)
    
    registration_id = data['registration_id']
    db_session = get_db_session()
    try:
        registration = db_session.query(UdyamRegistration).filter_by(id=registration_id, vendor_id=request.vendor_id).first()
        if not registration:
            raise InvalidAPIUsage("Registration not found", status_code=404)
        
        if registration.form_status != FormStatus.ERROR:
            raise InvalidAPIUsage("Only failed registrations can be retried", status_code=400)
        
        # Reset the status and start the process again
        registration.form_status = FormStatus.INITIATED
        db_session.commit()
        
        # Start the registration process in a separate thread
        threading.Thread(target=process_registration, args=(registration_id,)).start()
        
        return jsonify({
            "status": "success", 
            "message": "Registration retry initiated successfully",
            "registration_id": registration_id
        }), 202
    except Exception as e:
        db_session.rollback()
        raise InvalidAPIUsage(str(e), status_code=500)
    finally:
        db_session.close()

@app.route("/api/udyam/fetch_captcha", methods=["GET"])
@validate_api_key
def fetch_captcha():
    registration_id = request.args.get('registration_id')
    if not registration_id:
        raise InvalidAPIUsage("Registration ID is required", status_code=400)

    db_session = get_db_session()
    try:
        registration = db_session.query(UdyamRegistration).filter_by(id=registration_id, vendor_id=request.vendor_id).first()
        if not registration:
            raise InvalidAPIUsage("Registration not found", status_code=404)

        captcha_url = get_captcha_url(registration_id)
        return jsonify({"status": "success", "captcha_url": captcha_url})
    except Exception as e:
        raise InvalidAPIUsage(str(e), status_code=500)
    finally:
        db_session.close()

@app.route("/api/udyam/submit_captcha", methods=["POST"])
@validate_api_key
def submit_captcha():
    data = request.json
    if 'captcha' not in data or 'registration_id' not in data:
        raise InvalidAPIUsage("CAPTCHA and registration ID are required", status_code=400)
    
    registration_id = data['registration_id']
    captcha_code = data['captcha']
    
    db_session = get_db_session()
    try:
        registration = db_session.query(UdyamRegistration).filter_by(id=registration_id, vendor_id=request.vendor_id).first()
        if not registration:
            raise InvalidAPIUsage("Registration not found", status_code=404)
        
        result = submit_captcha_and_complete(registration_id, captcha_code)
        if result['status'] == 'success':
            registration.form_status = FormStatus.COMPLETED
            db_session.commit()
        elif result['status'] == 'error':
            registration.form_status = FormStatus.ERROR
            db_session.commit()
        
        return jsonify(result)
    except Exception as e:
        db_session.rollback()
        raise InvalidAPIUsage(str(e), status_code=500)
    finally:
        db_session.close()

@app.route("/api/vendor/register", methods=["POST"])
def register_vendor():
    data = request.json
    if 'name' not in data or 'email' not in data:
        raise InvalidAPIUsage("Vendor name and email are required", status_code=400)
    
    db_session = get_db_session()
    try:
        new_vendor = Vendor(name=data['name'], email=data['email'])
        new_vendor.generate_api_key()
        db_session.add(new_vendor)
        db_session.commit()
        
        return jsonify({
            "status": "success",
            "message": "Vendor registered successfully",
            "vendor_id": new_vendor.id,
            "api_key": new_vendor.api_key
        }), 201
    except Exception as e:
        db_session.rollback()
        raise InvalidAPIUsage(str(e), status_code=400)
    finally:
        db_session.close()

@app.route("/api/vendor/refresh_api_key", methods=["POST"])
@validate_api_key
def refresh_api_key():
    db_session = get_db_session()
    try:
        vendor = db_session.query(Vendor).filter_by(id=request.vendor_id).first()
        if not vendor:
            raise InvalidAPIUsage("Vendor not found", status_code=404)
        
        vendor.generate_api_key()
        db_session.commit()
        
        return jsonify({
            "status": "success",
            "message": "API key refreshed successfully",
            "new_api_key": vendor.api_key
        })
    except Exception as e:
        db_session.rollback()
        raise InvalidAPIUsage(str(e), status_code=400)
    finally:
        db_session.close()

@app.route("/api/vendor/registrations", methods=["GET"])
@validate_api_key
def get_vendor_registrations():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    db_session = get_db_session()
    try:
        registrations = db_session.query(UdyamRegistration).filter_by(vendor_id=request.vendor_id)\
            .order_by(UdyamRegistration.created_at.desc())\
            .paginate(page=page, per_page=per_page, error_out=False)
        
        registration_list = [{
            "id": reg.id,
            "aadhaar": reg.aadhaar,
            "name": reg.name,
            "form_status": reg.form_status.value,
            "created_at": reg.created_at.isoformat()
        } for reg in registrations.items]
        
        return jsonify({
            "status": "success",
            "registrations": registration_list,
            "total": registrations.total,
            "pages": registrations.pages,
            "current_page": page
        })
    except Exception as e:
        raise InvalidAPIUsage(str(e), status_code=400)
    finally:
        db_session.close()

@app.route("/api/vendor/login", methods=["POST"])
def vendor_login():
    data = request.json
    if 'email' not in data or 'api_key' not in data:
        raise InvalidAPIUsage("Email and API key are required", status_code=400)
    
    db_session = get_db_session()
    try:
        vendor = db_session.query(Vendor).filter_by(email=data['email'], api_key=data['api_key']).first()
        if not vendor:
            raise InvalidAPIUsage("Invalid credentials", status_code=401)
        
        return jsonify({
            "status": "success",
            "message": "Login successful",
            "vendor_id": vendor.id
        })
    except Exception as e:
        raise InvalidAPIUsage(str(e), status_code=400)
    finally:
        db_session.close()

if __name__ == '__main__':
    app.run(debug=DEBUG_MODE)
