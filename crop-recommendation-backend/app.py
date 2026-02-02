from flask import Flask, request, jsonify
from flask_cors import CORS
from models import db, Prediction
from utils import load_model, validate_input, prepare_input
from explainability import CropExplainer
from schemas import CropInput, PredictionResponse, HealthResponse
import os
import logging
import uuid
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
    
    # --- Emergency Schema Migration (Add columns if missing) ---
    try:
        from sqlalchemy import text
        # These are the new columns added in Upgrade 7
        new_columns = [
            ('request_id', 'VARCHAR(36)'),
            ('confidence', 'FLOAT')
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
            "predict": "/predict [POST]",
            "history": "/history [GET]",
            "stats": "/stats [GET]"
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

@app.route("/api/v1/predict", methods=["POST"])
def predict() -> Any:
    """
    Core prediction engine utilizing Pydantic for strict schema validation.
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
            logger.info(f"[{request_id}] Result saved to database")
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
def history() -> Any:
    """Fetch prediction history with type hints"""
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
        logger.error(f"❌ History retrieval failed: {str(e)}")
        return jsonify({
            "status": "error",
            "error": "Database Query Error",
            "details": str(e),
            "hint": "This often happens if you upgraded the schema but the database wasn't updated. Try restarting the server."
        }), 500


@app.route('/api/v1/stats', methods=['GET'])
def stats() -> Any:
    """Fetch system stats with type hints"""
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