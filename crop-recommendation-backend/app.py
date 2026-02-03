from flask import Flask, request, jsonify
from flask_cors import CORS
from models import db, Prediction, User
from utils import load_model, validate_input, prepare_input
from explainability import CropExplainer
from schemas import (
    CropInput, PredictionResponse, HealthResponse,
    UserRegister, UserLogin, UserResponse, TokenResponse, TokenRefresh
)
from auth_utils import (
    token_required, generate_token, generate_refresh_token, 
    verify_token, hash_password, verify_password
)
import os
import logging
import uuid
import pickle
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from pydantic import ValidationError

# -------------------- LOGGING SETUP --------------------

logging.basicConfig(
    level=os.environ.get('LOG_LEVEL', 'INFO'),
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)

# -------------------- HELPERS --------------------

def sanitize_input(value: Any, field_name: str) -> Optional[float]:
    """
    Clean and convert input values to float.
    Demonstrates senior-level defensive programming.
    """
    try:
        if isinstance(value, str):
            return float(value.strip())
        return float(value)
    except (ValueError, TypeError):
        return None

# -------------------- APP SETUP --------------------

app = Flask(__name__)
CORS(app)

# Load configuration based on environment
from config import config as app_configs
env = os.environ.get('FLASK_ENV', 'development')
logger.info(f"🚀 Starting App in [{env}] mode")

# Standardize config loading
selected_config = app_configs.get(env, app_configs['default'])
app.config.from_object(selected_config)

# Ensure required directories exist
os.makedirs(os.path.join(app.config.get('BASE_DIR'), 'instance'), exist_ok=True)
os.makedirs(os.path.join(app.config.get('BASE_DIR'), 'ml_models'), exist_ok=True)

db.init_app(app)
# Optionally skip DB creation during imports/tests to avoid locking/permission issues
if os.environ.get('SKIP_DB_INIT') == '1':
    logger.info("⚠️ SKIP_DB_INIT=1 set — skipping automatic database creation on import")
else:
    with app.app_context():
        db.create_all()

# -------------------- LOAD MODEL (With Emergency Fallback) --------------------

model, scaler = None, None
model_error = None

def initialize_model():
    global model, scaler, model_error
    try:
        m_path = app.config.get('MODEL_PATH')
        s_path = app.config.get('SCALER_PATH')
        
        # Check existence or force retrain if files are corrupted/incompatible
        if not (os.path.exists(m_path) and os.path.exists(s_path)):
            logger.warning("🚨 Model files MISSING. Training now...")
            from train_model import train_and_save_model
            train_and_save_model()

        try:
            model, scaler = load_model(m_path, s_path)
            logger.info("✅ Model and scaler loaded successfully")
        except (ModuleNotFoundError, AttributeError, pickle.UnpicklingError) as load_err:
            logger.error(f"⚠️ Library mismatch detected ({load_err}). Forcing RE-TRAIN...")
            from train_model import train_and_save_model
            train_and_save_model()
            model, scaler = load_model(m_path, s_path)
            logger.info("✅ Model recovered with local training")

    except Exception as e:
        logger.error(f"❌ Critical startup error: {str(e)}")
        model_error = str(e)
        model, scaler = None, None

# Allow skipping model initialization for fast test/import (set SKIP_MODEL_LOAD=1)
if os.environ.get('SKIP_MODEL_LOAD') == '1':
    logger.info("⚠️ SKIP_MODEL_LOAD=1 set — skipping ML model initialization for faster imports/tests")
    model, scaler, model_error = None, None, None
else:
    initialize_model()

# Initialize Explainer
explainer = None
if model is not None:
    try:
        data_path = os.path.join(app.config.get('BASE_DIR'), 'Data', 'Crop_recommendation.csv')
        explainer = CropExplainer(model, data_path)
        logger.info("✅ Explainability engine initialized")
    except Exception as e:
        logger.warning(f"⚠️ Explainer failed: {e}")

# -------------------- INIT DB --------------------

if os.environ.get('SKIP_DB_INIT') == '1':
    logger.info("⚠️ SKIP_DB_INIT=1 set — skipping secondary DB init/migration steps on import")
else:
    with app.app_context():
        if env != 'production':
            os.makedirs(os.path.join(app.config.get('BASE_DIR'), 'instance'), exist_ok=True)
        db.create_all()
    
        # --- Emergency Schema Migration (Add columns if missing) ---
        try:
            from sqlalchemy import text
            # These are the new columns added in previous upgrades
            new_columns = [
                ('request_id', 'VARCHAR(36)'),
                ('confidence', 'FLOAT'),
                ('user_id', 'INTEGER')  # JWT auth upgrade
            ]
            
            for col_name, col_type in new_columns:
                try:
                    # Check if column exists
                    db.session.execute(text(f"SELECT {col_name} FROM predictions LIMIT 1"))
                except Exception:
                    # If selection fails, column likely missing - attempt to add
                    db.session.rollback()
                    logger.warning(f"🔧 Schema Mismatch: Adding missing column [{col_name}] to [predictions] table")
                    db.session.execute(text(f"ALTER TABLE predictions ADD COLUMN {col_name} {col_type}"))
                    db.session.commit()
                    logger.info(f"✅ Successfully added column {col_name}")
                    
        except Exception as e:
            logger.error(f"⚠️ Auto-migration failed: {e}")
            db.session.rollback()

    logger.info("✓ Database initialized and verified")

# -------------------- ROUTES --------------------

@app.route('/')
def home():
    return jsonify({
        "status": "success",
        "message": "Crop Recommendation API is running",
        "environment": env,
        "endpoints": {
            "health": "/api/v1/health [GET]",
            "register": "/api/v1/auth/register [POST]",
            "login": "/api/v1/auth/login [POST]",
            "me": "/api/v1/auth/me [GET] (Protected)",
            "refresh": "/api/v1/auth/refresh [POST]",
            "predict": "/api/v1/predict [POST] (Protected)",
            "history": "/api/v1/history [GET] (Protected)",
            "stats": "/api/v1/stats [GET] (Protected)"
        }
    })

@app.route("/api/v1/health", methods=["GET"])
def health() -> Any:
    """System heartbeat with validated schema output"""
    response_data = HealthResponse(
        model_loaded=model is not None,
        scaler_loaded=scaler is not None,
        explainer_enabled=app.config.get('ENABLE_EXPLAINABILITY', True)
    )
    return jsonify(response_data.model_dump())


# -------------------- AUTHENTICATION ROUTES --------------------

@app.route("/api/v1/auth/register", methods=["POST"])
def register() -> Any:
    """Register a new user"""
    try:
        # Validate input
        raw_data = request.get_json()
        validated_data = UserRegister(**raw_data)
        
        # Check if user already exists
        existing_user = User.query.filter(
            (User.email == validated_data.email) | 
            (User.username == validated_data.username)
        ).first()
        
        if existing_user:
            if existing_user.email == validated_data.email:
                return jsonify({
                    "status": "error",
                    "error": "Email Already Registered",
                    "message": "This email is already in use"
                }), 409
            else:
                return jsonify({
                    "status": "error",
                    "error": "Username Already Taken",
                    "message": "This username is already in use"
                }), 409
        
        # Create new user
        new_user = User(
            email=validated_data.email,
            username=validated_data.username
        )
        new_user.set_password(validated_data.password)
        
        db.session.add(new_user)
        db.session.commit()
        
        logger.info(f"✅ New user registered: {new_user.username}")
        
        # Generate tokens
        access_token = generate_token(new_user.id, new_user.email)
        refresh_token = generate_refresh_token(new_user.id, new_user.email)
        
        # Prepare response
        user_data = UserResponse(**new_user.to_dict(include_predictions=True))
        response = TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=app.config.get('JWT_ACCESS_TOKEN_EXPIRES', 3600),
            user=user_data
        )
        
        return jsonify(response.model_dump()), 201
        
    except ValidationError as v_err:
        return jsonify({
            "status": "error",
            "error": "Validation Failed",
            "details": v_err.errors()
        }), 400
    except Exception as e:
        logger.error(f"❌ Registration error: {str(e)}")
        db.session.rollback()
        return jsonify({
            "status": "error",
            "error": "Registration Failed",
            "message": str(e)
        }), 500


@app.route("/api/v1/auth/login", methods=["POST"])
def login() -> Any:
    """Authenticate user and return tokens"""
    try:
        # Validate input
        raw_data = request.get_json()
        validated_data = UserLogin(**raw_data)
        
        # Find user by email or username
        user = User.query.filter(
            (User.email == validated_data.email) | 
            (User.username == validated_data.email)
        ).first()
        
        if not user:
            return jsonify({
                "status": "error",
                "error": "Invalid Credentials",
                "message": "Email/username or password is incorrect"
            }), 401
        
        # Verify password
        if not user.check_password(validated_data.password):
            return jsonify({
                "status": "error",
                "error": "Invalid Credentials",
                "message": "Email/username or password is incorrect"
            }), 401
        
        # Check if account is active
        if not user.is_active:
            return jsonify({
                "status": "error",
                "error": "Account Disabled",
                "message": "Your account has been disabled"
            }), 403
        
        # Update last login
        user.update_last_login()
        db.session.commit()
        
        logger.info(f"✅ User logged in: {user.username}")
        
        # Generate tokens
        access_token = generate_token(user.id, user.email)
        refresh_token = generate_refresh_token(user.id, user.email)
        
        # Prepare response
        user_data = UserResponse(**user.to_dict(include_predictions=True))
        response = TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=app.config.get('JWT_ACCESS_TOKEN_EXPIRES', 3600),
            user=user_data
        )
        
        return jsonify(response.model_dump()), 200
        
    except ValidationError as v_err:
        return jsonify({
            "status": "error",
            "error": "Validation Failed",
            "details": v_err.errors()
        }), 400
    except Exception as e:
        logger.error(f"❌ Login error: {str(e)}")
        return jsonify({
            "status": "error",
            "error": "Login Failed",
            "message": str(e)
        }), 500


@app.route("/api/v1/auth/me", methods=["GET"])
@token_required
def get_current_user(current_user: Dict[str, Any]) -> Any:
    """Get current user profile"""
    try:
        user = User.query.get(current_user['user_id'])
        
        if not user:
            return jsonify({
                "status": "error",
                "error": "User Not Found",
                "message": "User account no longer exists"
            }), 404
        
        user_data = UserResponse(**user.to_dict(include_predictions=True))
        return jsonify({
            "status": "success",
            "user": user_data.model_dump()
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Get user error: {str(e)}")
        return jsonify({
            "status": "error",
            "error": "Failed to Retrieve User",
            "message": str(e)
        }), 500


@app.route("/api/v1/auth/refresh", methods=["POST"])
def refresh_token_endpoint() -> Any:
    """Refresh access token using refresh token"""
    try:
        raw_data = request.get_json()
        validated_data = TokenRefresh(**raw_data)
        
        # Verify refresh token
        payload = verify_token(validated_data.refresh_token, token_type='refresh')
        
        if not payload:
            return jsonify({
                "status": "error",
                "error": "Invalid Refresh Token",
                "message": "Refresh token is invalid or expired"
            }), 401
        
        # Get user
        user = User.query.get(payload['user_id'])
        
        if not user or not user.is_active:
            return jsonify({
                "status": "error",
                "error": "Invalid User",
                "message": "User account is invalid or disabled"
            }), 401
        
        # Generate new access token
        new_access_token = generate_token(user.id, user.email)
        
        return jsonify({
            "status": "success",
            "access_token": new_access_token,
            "token_type": "Bearer",
            "expires_in": app.config.get('JWT_ACCESS_TOKEN_EXPIRES', 3600)
        }), 200
        
    except ValidationError as v_err:
        return jsonify({
            "status": "error",
            "error": "Validation Failed",
            "details": v_err.errors()
        }), 400
    except Exception as e:
        logger.error(f"❌ Token refresh error: {str(e)}")
        return jsonify({
            "status": "error",
            "error": "Token Refresh Failed",
            "message": str(e)
        }), 500

@app.route("/api/v1/predict", methods=["POST"])
@token_required
def predict(current_user: Dict[str, Any]) -> Any:
    """
    Core prediction engine utilizing Pydantic for strict schema validation.
    Protected route - requires authentication.
    """
    request_id = str(uuid.uuid4())
    try:
        # 1. Integrity Check
        if model is None or scaler is None:
            return jsonify({
                "status": "error",
                "request_id": request_id,
                "error": "ML Integrity Check Failed",
                "details": f"Model not initialized. Startup error: {model_error}"
            }), 500
        
        # 2. Schema Validation via Pydantic
        try:
            raw_data = request.get_json()
            validated_data = CropInput(**raw_data)
            data = validated_data.model_dump()
        except ValidationError as v_err:
            return jsonify({
                "status": "error",
                "request_id": request_id,
                "error": "Validation Failed",
                "details": v_err.errors()
            }), 400
        except Exception:
            return jsonify({
                "status": "error",
                "request_id": request_id,
                "error": "Invalid JSON payload"
            }), 400
        
        X = prepare_input(data)
        X_scaled = scaler.transform(X)
        
        # 3. Model Inference
        predicted_crop = model.predict(X_scaled)[0]
        probabilities = model.predict_proba(X_scaled)[0]
        
        class_probas = sorted(
            zip(model.classes_, probabilities),
            key=lambda x: x[1],
            reverse=True
        )
        
        top_confidence = float(class_probas[0][1])
        
        # Alternatives (Top 2-4)
        alternatives = []
        for crop, proba in class_probas[1:4]:
            if proba > 0.01:
                alternatives.append({
                    "crop": str(crop),
                    "confidence": float(proba),
                    "suitability": "Moderate" if proba > 0.1 else "Low"
                })
        
        # 4. Persistence
        try:
            new_prediction = Prediction(
                user_id=current_user['user_id'],  # Associate with authenticated user
                nitrogen=data['N'],
                phosphorus=data['P'],
                potassium=data['K'],
                temperature=data['temperature'],
                humidity=data['humidity'],
                ph=data['ph'],
                rainfall=data['rainfall'],
                predicted_crop=predicted_crop,
                confidence=top_confidence,
                request_id=request_id
            )
            db.session.add(new_prediction)
            db.session.commit()
            logger.info(f"[{request_id}] Result saved to database for user {current_user['user_id']}")
        except Exception as db_err:
            logger.warning(f"[{request_id}] Database save failed: {db_err}")
            db.session.rollback()
        
        # 5. Explainability logic
        reasons = ["Highly favorable conditions"]
        if explainer and app.config.get('ENABLE_EXPLAINABILITY'):
            try:
                feature_names = [
                    'N', 'P', 'K', 'temperature', 'humidity', 'ph', 'rainfall',
                    'NPK_ratio', 'nutrient_balance', 'temp_humidity_index', 
                    'ph_optimality', 'water_stress_index', 'growing_degree_days', 
                    'N_P_ratio', 'N_K_ratio'
                ]
                reasons = explainer.explain_prediction(X_scaled, feature_names)
            except Exception as e:
                logger.warning(f"[{request_id}] Explainability failed: {e}")

        # 6. Structured Response
        response = PredictionResponse(
            request_id=request_id,
            predicted_crop=predicted_crop,
            confidence=top_confidence,
            alternatives=alternatives,
            input_data=data,
            reasons=reasons
        )
        return jsonify(response.model_dump())

    except Exception as e:
        logger.error(f"[{request_id}] Server Error: {str(e)}")
        return jsonify({
            "status": "error",
            "request_id": request_id,
            "error": "Internal Server Error",
            "details": str(e)
        }), 500


@app.route('/api/v1/history', methods=['GET'])
@token_required
def history(current_user: Dict[str, Any]) -> Any:
    """Fetch prediction history for authenticated user"""
    try:
        limit = request.args.get('limit', 10, type=int)
        
        # Filter predictions by current user
        records = Prediction.query.filter_by(
            user_id=current_user['user_id']
        ).order_by(
            Prediction.created_at.desc()
        ).limit(limit).all()

        return jsonify({
            "status": "success",
            "count": len(records),
            "data": [
                {
                    "id": r.id,
                    "predicted_crop": r.predicted_crop,
                    "confidence": r.confidence,
                    "created_at": r.created_at.isoformat(),
                    "input": {
                        "N": r.nitrogen,
                        "P": r.phosphorus,
                        "K": r.potassium,
                        "temperature": r.temperature,
                        "humidity": r.humidity,
                        "ph": r.ph,
                        "rainfall": r.rainfall
                    }
                } for r in records
            ]
        })
    except Exception as e:
        logger.error(f"❌ History retrieval failed: {str(e)}")
        return jsonify({
            "status": "error",
            "error": "Database Query Error",
            "details": str(e),
            "hint": "This often happens if you upgraded the schema but the database wasn't updated. Try restarting the server."
        }), 500


@app.route('/api/v1/stats', methods=['GET'])
@token_required
def stats(current_user: Dict[str, Any]) -> Any:
    """Fetch system stats for authenticated user"""
    try:
        from sqlalchemy import func

        # Filter by current user
        total = Prediction.query.filter_by(user_id=current_user['user_id']).count()

        crop_counts = db.session.query(
            Prediction.predicted_crop,
            func.count(Prediction.id)
        ).filter_by(
            user_id=current_user['user_id']
        ).group_by(Prediction.predicted_crop).all()

        return jsonify({
            "status": "success",
            "total_predictions": total,
            "crop_distribution": {
                crop: count for crop, count in crop_counts
            }
        })
    except Exception as e:
        logger.error(f"❌ Statistics retrieval failed: {str(e)}")
        return jsonify({
            "status": "error",
            "error": "Statistics Calculation Error",
            "details": str(e)
        }), 500


@app.route('/api/v1/model-comparison', methods=['GET'])
def get_model_comparison():
    try:
        results_path = os.path.join(os.path.dirname(__file__), 'model_comparison_results.json')
        if not os.path.exists(results_path):
            # If results don't exist, try to run the comparison
            from model_comparison import compare_models
            base_dir = os.path.dirname(os.path.abspath(__file__))
            data_path = os.path.join(base_dir, 'Data', 'Crop_recommendation.csv')
            if os.path.exists(data_path):
                results = compare_models(data_path)
            else:
                return jsonify({
                    "status": "error",
                    "message": "Model comparison results not found and dataset unavailable for training."
                }), 404
        else:
            import json
            with open(results_path, 'r') as f:
                results = json.load(f)
        
        return jsonify({
            "status": "success",
            "data": results
        })
    except Exception as e:
        print(f"Error in model comparison endpoint: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route('/api/v1/ml-maturity-report', methods=['GET'])
def get_ml_maturity_report():
    try:
        report_path = os.path.join(os.path.dirname(__file__), 'ml_maturity_report.json')
        if not os.path.exists(report_path):
            # Run the upgrade if report doesn't exist
            from evaluate_model import run_maturity_upgrade
            results = run_maturity_upgrade()
        else:
            import json
            with open(report_path, 'r') as f:
                results = json.load(f)
        
        return jsonify({
            "status": "success",
            "data": results
        })
    except Exception as e:
        logger.error(f"Error in ML maturity endpoint: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

# -------------------- RUN --------------------

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=(env != 'production'), host='0.0.0.0', port=port)