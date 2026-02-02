from flask import Flask, request, jsonify
from flask_cors import CORS
from models import db, Prediction
from utils import load_model, validate_input, prepare_input
from explainability import CropExplainer
import os
import logging
import uuid
from datetime import datetime

# -------------------- LOGGING SETUP --------------------

logging.basicConfig(
    level=os.environ.get('LOG_LEVEL', 'INFO'),
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)

# -------------------- HELPERS --------------------

def sanitize_input(value, field_name):
    """Prevent injection attacks and ensure strict data types"""
    try:
        # Agricultural inputs must be numeric
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

with app.app_context():
    if env != 'production':
        os.makedirs(os.path.join(BASE_DIR, 'instance'), exist_ok=True)
    db.create_all()
    print("✓ Database initialized")

# -------------------- ROUTES --------------------

@app.route('/')
def home():
    return jsonify({
        "status": "success",
        "message": "Crop Recommendation API is running",
        "environment": env,
        "endpoints": {
            "predict": "/predict [POST]",
            "history": "/history [GET]",
            "stats": "/stats [GET]"
        }
    })

@app.route("/api/v1/health", methods=["GET"])
def health_check():
    """System heartbeat with model status"""
    return jsonify({
        "status": "healthy",
        "model_loaded": model is not None,
        "scaler_loaded": scaler is not None,
        "explainer_enabled": app.config.get('ENABLE_EXPLAINABILITY', True),
        "timestamp": datetime.now().isoformat()
    })

@app.route("/predict", methods=["POST"])
@app.route("/api/v1/predict", methods=["POST"])
def predict():
    request_id = str(uuid.uuid4())
    try:
        if model is None or scaler is None:
            logger.error(f"[{request_id}] Model is None. Startup Error: {model_error}")
            return jsonify({
                "status": "error",
                "request_id": request_id,
                "error": "ML Integrity Check Failed",
                "details": f"Model or scaler is not initialized. Technical error: {model_error}",
                "paths": {
                    "model": app.config.get('MODEL_PATH'),
                    "scaler": app.config.get('SCALER_PATH')
                },
                "timestamp": datetime.now().isoformat()
            }), 500
        
        data = request.get_json()
        if not data:
            logger.warning(f"[{request_id}] No data provided")
            return jsonify({
                "status": "error",
                "request_id": request_id,
                "error": "No data provided"
            }), 400
        
        logger.info(f"[{request_id}] Input Received: {data}")
        
        # Sanitize Inputs
        sanitized_data = {}
        for field in ['N', 'P', 'K', 'temperature', 'humidity', 'ph', 'rainfall']:
            val = sanitize_input(data.get(field), field)
            if val is not None:
                sanitized_data[field] = val
            else:
                sanitized_data[field] = data.get(field) # validate_input will catch the type error

        # Robust Validation
        errors = validate_input(sanitized_data)
        if errors:
            logger.warning(f"[{request_id}] Validation Failed: {errors}")
            return jsonify({
                "status": "error",
                "request_id": request_id,
                "errors": errors,
                "timestamp": datetime.now().isoformat()
            }), 400
            
        X = prepare_input(sanitized_data)
        print("Prepared input:", X)
        
        X_scaled = scaler.transform(X)
        
        # Get prediction and probabilities
        prediction = model.predict(X_scaled)
        predicted_crop = prediction[0]
        
        # Get probabilities for all classes
        probabilities = model.predict_proba(X_scaled)[0]
        class_probas = sorted(
            zip(model.classes_, probabilities),
            key=lambda x: x[1],
            reverse=True
        )
        
        # Top confidence
        top_confidence = float(class_probas[0][1])
        
        # Alternatives (Top 2-4)
        alternatives = []
        for crop, proba in class_probas[1:4]:
            if proba > 0.01: # Only suggest if it has at least 1% probability
                alternatives.append({
                    "crop": crop,
                    "confidence": float(proba),
                    "suitability": "Moderate" if proba > 0.1 else "Low"
                })
        
        print(f"Prediction: {predicted_crop} ({top_confidence*100:.1f}%)")
        
        try:
            new_prediction = Prediction(
                nitrogen=float(sanitized_data['N']),
                phosphorus=float(sanitized_data['P']),
                potassium=float(sanitized_data['K']),
                temperature=float(sanitized_data['temperature']),
                humidity=float(sanitized_data['humidity']),
                ph=float(sanitized_data['ph']),
                rainfall=float(sanitized_data['rainfall']),
                predicted_crop=predicted_crop,
                confidence=float(top_confidence),
                request_id=request_id
            )
            db.session.add(new_prediction)
            db.session.commit()
            print("✓ Prediction saved to database")
        except Exception as db_error:
            print(f"Warning: Could not save to database: {db_error}")
            db.session.rollback()
        
        # Generate Explanations (only if explainer is available)
        reasons = []
        if explainer:
            try:
                feature_names = [
                    'N', 'P', 'K', 'temperature', 'humidity', 'ph', 'rainfall',
                    'NPK_ratio', 'nutrient_balance', 'temp_humidity_index', 
                    'ph_optimality', 'water_stress_index', 'growing_degree_days', 
                    'N_P_ratio', 'N_K_ratio'
                ]
                reasons = explainer.explain_prediction(X_scaled, feature_names)
            except Exception as e:
                print(f"Explainability Error: {e}")
                reasons = ["Highly favorable conditions"]
        else:
            reasons = ["Prediction based on historical data patterns"]

        return jsonify({
            "status": "success",
            "request_id": request_id,
            "predicted_crop": predicted_crop,
            "confidence": top_confidence,
            "alternatives": alternatives,
            "input_data": data,
            "reasons": reasons
        })

    except Exception as e:
        logger.error(f"[{request_id}] Server Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "status": "error",
            "request_id": request_id,
            "error": "An internal server error occurred. Please contact support with the request ID.",
            "timestamp": datetime.now().isoformat()
        }), 500


@app.route('/history', methods=['GET'])
@app.route('/api/v1/history', methods=['GET'])
def history():
    try:
        limit = request.args.get('limit', 10, type=int)
        records = Prediction.query.order_by(
            Prediction.created_at.desc()
        ).limit(limit).all()

        return jsonify({
            "status": "success",
            "count": len(records),
            "data": [
                {
                    "id": r.id,
                    "predicted_crop": r.predicted_crop,
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
        print("ERROR in history:", e)
        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500


@app.route('/stats', methods=['GET'])
@app.route('/api/v1/stats', methods=['GET'])
def stats():
    try:
        from sqlalchemy import func

        total = Prediction.query.count()

        crop_counts = db.session.query(
            Prediction.predicted_crop,
            func.count(Prediction.id)
        ).group_by(Prediction.predicted_crop).all()

        return jsonify({
            "status": "success",
            "total_predictions": total,
            "crop_distribution": {
                crop: count for crop, count in crop_counts
            }
        })
    except Exception as e:
        print("ERROR in stats:", e)
        return jsonify({
            "status": "error",
            "error": str(e)
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