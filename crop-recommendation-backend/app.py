from flask import Flask, request, jsonify
from flask_cors import CORS
from models import db, Prediction
from utils import load_model, validate_input, prepare_input
import os

# -------------------- APP SETUP --------------------

app = Flask(__name__)
CORS(app)

# Load configuration based on environment
env = os.environ.get('FLASK_ENV', 'development')
if env == 'production':
    from config import ProductionConfig
    app.config.from_object(ProductionConfig)
else:
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    app.config['SQLALCHEMY_DATABASE_URI'] = (
        'sqlite:///' + os.path.join(BASE_DIR, 'instance', 'predictions.db')
    )
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

# -------------------- LOAD MODEL --------------------

try:
    model, scaler = load_model()
    print("✓ Model and scaler loaded successfully")
except Exception as e:
    print(f"✗ Error loading model: {e}")
    model, scaler = None, None

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

@app.route("/predict", methods=["POST"])
def predict():
    try:
        if model is None or scaler is None:
            return jsonify({
                "error": "Model not loaded. Please ensure model files exist in ml_models folder."
            }), 500
        
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        print("Received data:", data)
        validate_input(data)
        X = prepare_input(data)
        print("Prepared input:", X)
        
        X_scaled = scaler.transform(X)
        prediction = model.predict(X_scaled)
        predicted_crop = prediction[0]
        
        print(f"Prediction: {predicted_crop}")
        
        try:
            new_prediction = Prediction(
                nitrogen=float(data['N']),
                phosphorus=float(data['P']),
                potassium=float(data['K']),
                temperature=float(data['temperature']),
                humidity=float(data['humidity']),
                ph=float(data['ph']),
                rainfall=float(data['rainfall']),
                predicted_crop=predicted_crop
            )
            db.session.add(new_prediction)
            db.session.commit()
            print("✓ Prediction saved to database")
        except Exception as db_error:
            print(f"Warning: Could not save to database: {db_error}")
            db.session.rollback()
        
        return jsonify({
            "status": "success",
            "predicted_crop": predicted_crop,
            "input_data": data
        })

    except ValueError as ve:
        print("Validation ERROR:", ve)
        return jsonify({
            "status": "error",
            "error": str(ve)
        }), 400
    
    except Exception as e:
        print("ERROR:", e)
        import traceback
        traceback.print_exc()
        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500


@app.route('/history', methods=['GET'])
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

# -------------------- RUN --------------------

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=(env != 'production'), host='0.0.0.0', port=port)