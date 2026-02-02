import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import os
from utils import (
    call_prediction_api, get_history, get_stats, 
    get_model_comparison, get_ml_maturity_report
)

# ==================== PAGE CONFIG ====================
st.set_page_config(
    page_title="Crop Recommendation System",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==================== CONFIGURATION ====================
# Change this to your deployed Flask API URL
API_BASE_URL = os.environ.get('API_URL', "http://localhost:5000")

# ==================== CUSTOM CSS ====================
st.markdown("""
<style>
.main-header {
    font-size: 2.5rem;
    color: #22808d;
    font-weight: bold;
    text-align: center;
    margin-bottom: 0.5rem;
}
.sub-header {
    font-size: 1.2rem;
    color: #134252;
    text-align: center;
    margin-bottom: 2rem;
}
.prediction-card {
    background: linear-gradient(135deg, #22808d 0%, #134252 100%);
    padding: 2rem;
    border-radius: 10px;
    color: white;
    text-align: center;
    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
}
.prediction-result {
    font-size: 3rem;
    font-weight: bold;
    margin: 1rem 0;
    text-transform: uppercase;
}
.info-card {
    background: #f0f2f6;
    padding: 1rem;
    border-radius: 8px;
    border-left: 4px solid #22808d;
}
.metric-card {
    background: white;
    padding: 1.5rem;
    border-radius: 8px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    text-align: center;
}
.stSlider > div > div > div > div {
    background-color: #22808d;
}
</style>
""", unsafe_allow_html=True)

# ==================== HEADER ====================
st.markdown('<div class="main-header">🌾 Smart Crop Recommendation System</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">AI-Powered Agricultural Decision Support</div>', unsafe_allow_html=True)

# ==================== SIDEBAR ====================
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/000000/farm.png", width=80)
    st.title("Navigation")
    
    page = st.radio(
        "Select Page",
        ["🏠 Make Prediction", "📊 History & Analytics", "🔬 Model Comparison", "ℹ️ About"]
    )
    
    st.markdown("---")
    st.markdown("### API Configuration")
    st.info(f"**API URL:** {API_BASE_URL}")
    api_status_placeholder = st.empty()
    
    # Check API health
    try:
        import requests
        response = requests.get(f"{API_BASE_URL}/", timeout=3)
        if response.status_code == 200 and response.json().get('status') == 'success':
            api_status_placeholder.success("✓ API Connected")
        else:
            api_status_placeholder.warning("⚠ API Responding (Check Config)")
    except Exception as e:
        api_status_placeholder.error(f"✗ API Offline")

# ==================== PAGE 1: PREDICTION ====================
if page == "🏠 Make Prediction":
    st.header("Enter Farm Parameters")
    
    # Create tabs for better organization
    tab1, tab2 = st.tabs(["📊 Use Sliders", "⌨️ Manual Input"])
    
    with tab1:
        st.markdown("### Adjust parameters using sliders")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("#### 🌱 Soil Nutrients (kg/ha)")
            nitrogen = st.slider(
                "Nitrogen (N)",
                min_value=0.0,
                max_value=140.0,
                value=90.0,
                step=1.0,
                help="Nitrogen content in soil (0-140 kg/ha)"
            )
            st.caption(f"Selected: **{nitrogen} kg/ha**")
            
            phosphorus = st.slider(
                "Phosphorus (P)",
                min_value=5.0,
                max_value=145.0,
                value=42.0,
                step=1.0,
                help="Phosphorus content in soil (5-145 kg/ha)"
            )
            st.caption(f"Selected: **{phosphorus} kg/ha**")
            
            potassium = st.slider(
                "Potassium (K)",
                min_value=5.0,
                max_value=205.0,
                value=43.0,
                step=1.0,
                help="Potassium content in soil (5-205 kg/ha)"
            )
            st.caption(f"Selected: **{potassium} kg/ha**")
        
        with col2:
            st.markdown("#### 🌡️ Climate Conditions")
            temperature = st.slider(
                "Temperature (°C)",
                min_value=8.0,
                max_value=44.0,
                value=20.9,
                step=0.1,
                help="Average temperature in Celsius (8-44°C)"
            )
            st.caption(f"Selected: **{temperature}°C**")
            
            humidity = st.slider(
                "Humidity (%)",
                min_value=14.0,
                max_value=100.0,
                value=82.0,
                step=0.5,
                help="Relative humidity percentage (14-100%)"
            )
            st.caption(f"Selected: **{humidity}%**")
        
        with col3:
            st.markdown("#### 💧 Soil & Water")
            ph = st.slider(
                "pH Level",
                min_value=3.5,
                max_value=10.0,
                value=6.5,
                step=0.1,
                help="Soil pH level (3.5-10.0)"
            )
            st.caption(f"Selected: **{ph}**")
            
            rainfall = st.slider(
                "Rainfall (mm)",
                min_value=20.0,
                max_value=300.0,
                value=202.9,
                step=1.0,
                help="Annual rainfall in millimeters (20-300mm)"
            )
            st.caption(f"Selected: **{rainfall} mm**")
        
        st.markdown("---")
        
        # Preset buttons
        st.markdown("#### 📋 Quick Presets")
        preset_col1, preset_col2, preset_col3, preset_col4 = st.columns(4)
        
        with preset_col1:
            if st.button("🌾 Rice Conditions", use_container_width=True):
                nitrogen = 80.0
                phosphorus = 40.0
                potassium = 40.0
                temperature = 25.0
                humidity = 80.0
                ph = 6.5
                rainfall = 200.0
                st.rerun()
        
        with preset_col2:
            if st.button("🌽 Maize Conditions", use_container_width=True):
                nitrogen = 90.0
                phosphorus = 50.0
                potassium = 50.0
                temperature = 22.0
                humidity = 65.0
                ph = 6.0
                rainfall = 100.0
                st.rerun()
        
        with preset_col3:
            if st.button("☕ Coffee Conditions", use_container_width=True):
                nitrogen = 100.0
                phosphorus = 30.0
                potassium = 30.0
                temperature = 23.0
                humidity = 70.0
                ph = 6.5
                rainfall = 150.0
                st.rerun()
        
        with preset_col4:
            if st.button("🔄 Reset to Default", use_container_width=True):
                st.rerun()
        
        st.markdown("---")
        submit_button = st.button(
            "🚀 Get Crop Recommendation",
            use_container_width=True,
            type="primary"
        )
    
    with tab2:
        st.markdown("### Enter values manually")
        
        with st.form("manual_input_form"):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.subheader("Soil Nutrients (kg/ha)")
                nitrogen_manual = st.number_input(
                    "Nitrogen (N)",
                    min_value=0.0, max_value=140.0, value=90.0, step=1.0,
                    help="Nitrogen content in soil (0-140 kg/ha)"
                )
                phosphorus_manual = st.number_input(
                    "Phosphorus (P)",
                    min_value=5.0, max_value=145.0, value=42.0, step=1.0,
                    help="Phosphorus content in soil (5-145 kg/ha)"
                )
                potassium_manual = st.number_input(
                    "Potassium (K)",
                    min_value=5.0, max_value=205.0, value=43.0, step=1.0,
                    help="Potassium content in soil (5-205 kg/ha)"
                )
            
            with col2:
                st.subheader("Climate Conditions")
                temperature_manual = st.number_input(
                    "Temperature (°C)",
                    min_value=8.0, max_value=44.0, value=20.87, step=0.1,
                    help="Average temperature in Celsius (8-44°C)"
                )
                humidity_manual = st.number_input(
                    "Humidity (%)",
                    min_value=14.0, max_value=100.0, value=82.0, step=0.1,
                    help="Relative humidity percentage (14-100%)"
                )
            
            with col3:
                st.subheader("Soil & Water")
                ph_manual = st.number_input(
                    "pH Level",
                    min_value=3.5, max_value=10.0, value=6.5, step=0.1,
                    help="Soil pH level (3.5-10.0)"
                )
                rainfall_manual = st.number_input(
                    "Rainfall (mm)",
                    min_value=20.0, max_value=300.0, value=202.93, step=0.1,
                    help="Annual rainfall in millimeters (20-300mm)"
                )
            
            st.markdown("---")
            submit_button_manual = st.form_submit_button(
                "🚀 Get Crop Recommendation",
                use_container_width=True
            )
            
            if submit_button_manual:
                nitrogen = nitrogen_manual
                phosphorus = phosphorus_manual
                potassium = potassium_manual
                temperature = temperature_manual
                humidity = humidity_manual
                ph = ph_manual
                rainfall = rainfall_manual
                submit_button = True
    
    # Process prediction (works for both tabs)
    if 'submit_button' in locals() and submit_button:
        with st.spinner("🔄 Analyzing soil and climate data..."):
            # Prepare payload
            payload = {
                "N": float(nitrogen),
                "P": float(phosphorus),
                "K": float(potassium),
                "temperature": float(temperature),
                "humidity": float(humidity),
                "ph": float(ph),
                "rainfall": float(rainfall)
            }
            
            # Call API
            result = call_prediction_api(f"{API_BASE_URL}/api/v1/predict", payload)
            
            if result and result.get('status') == 'success':
                crop = result['predicted_crop']
                
                # Display result with animation
                st.balloons()
                
                st.markdown(f"""
                <div class="prediction-card">
                    <h2>✅ Recommendation Ready</h2>
                    <div class="prediction-result">🌾 {crop}</div>
                    <p>Based on your soil and climate conditions, <strong>{crop.upper()}</strong> is the best crop to cultivate.</p>
                </div>
                """, unsafe_allow_html=True)

                st.markdown("---")
                st.header("🛡️ Trust & Explainability Dashboard")
                st.caption("This dashboard provides transparency into why the AI made this choice and how reliable it is.")

                # Display Confidence
                if 'confidence' in result:
                    confidence_pct = result['confidence'] * 100
                    st.markdown(f"#### 🎯 Prediction Confidence: {confidence_pct:.1f}%")
                    st.progress(result['confidence'])
                    
                    if confidence_pct > 80:
                        st.success("🌟 Highly Reliable Recommendation")
                    elif confidence_pct > 50:
                        st.warning("⚖️ Moderate Confidence - Consider alternatives")
                    else:
                        st.error("⚠️ Low Confidence - Consult an agronomist")
                
                # Display Why this Crop? reasons
                if 'reasons' in result and result['reasons']:
                    st.markdown("### 🔍 Why this crop?")
                    cols = st.columns(len(result['reasons']))
                    for i, reason in enumerate(result['reasons']):
                        with cols[i]:
                            st.markdown(f"""
                            <div style="background: #e1f5fe; padding: 1rem; border-radius: 10px; border-left: 5px solid #03a9f4; height: 100%;">
                                <p style="margin: 0; color: #01579b; font-weight: bold;">Reason {i+1}</p>
                                <p style="margin: 0; color: #0277bd;">{reason.capitalize()}</p>
                            </div>
                            """, unsafe_allow_html=True)
                    st.markdown("<br>", unsafe_allow_html=True)

                # Display Alternatives
                if 'alternatives' in result and result['alternatives']:
                    st.markdown("### 🔄 Alternative Options")
                    st.info("If the primary recommendation isn't suitable, consider these top-ranking alternatives:")
                    
                    # Convert to DataFrame for a clean table look as shown in requirements
                    alt_data = []
                    for alt in result['alternatives']:
                        alt_data.append({
                            "Crop": alt['crop'].upper(),
                            "Suitability": alt['suitability'],
                            "Confidence": f"{alt['confidence']*100:.1f}%"
                        })
                    
                    st.table(pd.DataFrame(alt_data))
                    st.markdown("<br>", unsafe_allow_html=True)
                
                st.success(f"✓ Prediction completed successfully!")
                
                # Display input summary in a nice format
                with st.expander("📋 View Input Summary"):
                    summary_col1, summary_col2, summary_col3 = st.columns(3)
                    
                    with summary_col1:
                        st.metric("Nitrogen (N)", f"{payload['N']} kg/ha")
                        st.metric("Phosphorus (P)", f"{payload['P']} kg/ha")
                        st.metric("Potassium (K)", f"{payload['K']} kg/ha")
                    
                    with summary_col2:
                        st.metric("Temperature", f"{payload['temperature']}°C")
                        st.metric("Humidity", f"{payload['humidity']}%")
                    
                    with summary_col3:
                        st.metric("pH Level", f"{payload['ph']}")
                        st.metric("Rainfall", f"{payload['rainfall']} mm")
            else:
                request_id = result.get('request_id', 'N/A') if result else 'N/A'
                
                if result and 'errors' in result:
                    st.error("❌ Validation Failed")
                    for err in result['errors']:
                        st.write(f"- {err}")
                else:
                    error_msg = result.get('error', 'Unknown error') if result else 'No response from API'
                    st.error(f"❌ Prediction Failed: {error_msg}")
                
                st.info(f"🆔 Request ID: `{request_id}` (Please provide this when reporting issues)")
                
                # Show debug info
                with st.expander("🔍 Debug Information"):
                    st.json(result if result else {"error": "No response"})

# ==================== PAGE 2: HISTORY & ANALYTICS ====================
elif page == "📊 History & Analytics":
    st.header("Prediction History & Statistics")
    
    # Fetch data
    stats_data = get_stats(API_BASE_URL)
    history_data = get_history(API_BASE_URL, limit=20)
    
    # Access stats data correctly
    if stats_data and stats_data.get('status') == 'success':
        total_preds = stats_data.get('total_predictions', 0)
        crop_dist = stats_data.get('crop_distribution', {})
        
        # Metrics row
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown(f"""
            <div class="metric-card">
                <h3 style="color: #22808d;">Total Predictions</h3>
                <p style="font-size: 2.5rem; font-weight: bold; margin: 0;">{total_preds}</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            most_common = max(crop_dist, key=crop_dist.get) if crop_dist else "N/A"
            st.markdown(f"""
            <div class="metric-card">
                <h3 style="color: #22808d;">Most Predicted Crop</h3>
                <p style="font-size: 2rem; font-weight: bold; margin: 0;">{most_common.upper()}</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            unique_crops = len(crop_dist)
            st.markdown(f"""
            <div class="metric-card">
                <h3 style="color: #22808d;">Unique Crops</h3>
                <p style="font-size: 2.5rem; font-weight: bold; margin: 0;">{unique_crops}</p>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Crop distribution chart
        if crop_dist:
            st.subheader("📈 Crop Distribution")
            df_crops = pd.DataFrame(
                list(crop_dist.items()),
                columns=['Crop', 'Count']
            ).sort_values('Count', ascending=False)
            
            fig = px.bar(
                df_crops,
                x='Crop',
                y='Count',
                title='Number of Predictions per Crop',
                color='Count',
                color_continuous_scale='teal',
                text='Count'
            )
            fig.update_layout(showlegend=False, height=400)
            fig.update_traces(textposition='outside')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No predictions yet. Make your first prediction!")
    else:
        st.warning("⚠ Unable to load statistics")
        if stats_data:
            with st.expander("🔍 Debug Info"):
                st.json(stats_data)
    
    # Access history data correctly
    if history_data and history_data.get('status') == 'success':
        st.subheader("📜 Recent Predictions")
        predictions = history_data.get('data', [])
        
        if predictions:
            # Extract input data from nested structure
            history_records = []
            for pred in predictions:
                record = {
                    'ID': pred['id'],
                    'Crop': pred['predicted_crop'],
                    'N': pred['input']['N'],
                    'P': pred['input']['P'],
                    'K': pred['input']['K'],
                    'Temp (°C)': pred['input']['temperature'],
                    'Humidity (%)': pred['input']['humidity'],
                    'pH': pred['input']['ph'],
                    'Rainfall (mm)': pred['input']['rainfall'],
                    'Timestamp': pred['created_at']
                }
                history_records.append(record)
            
            df_history = pd.DataFrame(history_records)
            st.dataframe(df_history, use_container_width=True, height=400)
            
            # Download button
            csv = df_history.to_csv(index=False)
            st.download_button(
                label="📥 Download History as CSV",
                data=csv,
                file_name=f"crop_predictions_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                use_container_width=True
            )
        else:
            st.info("No predictions yet. Make your first prediction!")
    else:
        st.warning("⚠ Unable to load history")
        if history_data:
            with st.expander("🔍 Debug Info"):
                st.json(history_data)

# ==================== PAGE 3: MODEL COMPARISON ====================
elif page == "🔬 Model Comparison":
    st.header("Model Performance Comparison")
    st.markdown("""
    This page shows a systematic comparison of different machine learning algorithms 
    evaluated on the crop recommendation dataset using 5-fold cross-validation.
    """)
    
    with st.spinner("📊 Fetching comparison results..."):
        comparison_data = get_model_comparison(API_BASE_URL)
        
    if comparison_data and comparison_data.get('status') == 'success':
        results = comparison_data.get('data', {})
        
        # Prepare data for Plotly
        model_names = []
        accuracies = []
        stds = []
        
        for name, metrics in results.items():
            if 'error' not in metrics:
                model_names.append(name)
                accuracies.append(metrics['mean_accuracy'] * 100)
                stds.append(metrics['std_accuracy'] * 100)
        
        df_comparison = pd.DataFrame({
            'Model': model_names,
            'Accuracy (%)': accuracies,
            'Std Dev (%)': stds
        }).sort_values('Accuracy (%)', ascending=False)
        
        # Display Best Model Metric
        best_model = df_comparison.iloc[0]
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("🏆 Best Model", best_model['Model'])
        with col2:
            st.metric("🎯 Top Accuracy", f"{best_model['Accuracy (%)']:.2f}%")
        with col3:
            st.metric("📉 Std Deviation", f"{best_model['Std Dev (%)']:.2f}%")
            
        st.markdown("---")
        
        # Visual Comparison
        col_left, col_right = st.columns([2, 1])
        
        with col_left:
            st.subheader("🚀 Accuracy by Algorithm")
            fig = px.bar(
                df_comparison,
                x='Model',
                y='Accuracy (%)',
                error_y='Std Dev (%)',
                color='Accuracy (%)',
                color_continuous_scale='viridis',
                text=df_comparison['Accuracy (%)'].apply(lambda x: f'{x:.2f}%')
            )
            fig.update_layout(height=500, showlegend=False)
            fig.update_traces(textposition='outside')
            st.plotly_chart(fig, use_container_width=True)
            
        with col_right:
            st.subheader("📝 Detailed Metrics")
            st.dataframe(
                df_comparison.style.background_gradient(cmap='Greens', subset=['Accuracy (%)']),
                use_container_width=True,
                hide_index=True
            )
            
        st.markdown("---")
        
        # Detailed stats expander
        with st.expander("🔍 View Raw Analysis Data"):
            st.json(results)
            
        st.info("""
        **Why this matters:** Systematic comparison shows that we don't just pick a 
        random algorithm. We test multiple approaches (Linear, Ensemble, Probabilistic) 
        and choose the one that provides the highest reliability for farmers.
        """)
        
        st.markdown("---")
        st.header("🔬 Advanced Model Insights (ML Maturity)")
        
        with st.spinner("⌛ Loading scientific maturity report..."):
            maturity_res = get_ml_maturity_report(API_BASE_URL)
            
            if maturity_res and maturity_res.get('status') == 'success':
                report = maturity_res['data']
                
                # 1. Overfitting Analysis
                st.subheader("⚖️ Training Stability (Overfitting Check)")
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Train Accuracy", f"{report['cv_metrics']['train_accuracy']*100:.2f}%")
                with col2:
                    st.metric("Test Accuracy", f"{report['cv_metrics']['test_accuracy']*100:.2f}%")
                with col3:
                    gap = (report['cv_metrics']['train_accuracy'] - report['cv_metrics']['test_accuracy']) * 100
                    st.metric("Generalization Gap", f"{gap:.2f}%", delta=f"{gap:.2f}%", delta_color="inverse")
                
                # 2. Confusion Matrix & Feature Importance
                col_left, col_right = st.columns([1, 1])
                
                with col_left:
                    st.subheader("🧩 Confusion Matrix")
                    cm_data = report['confusion_matrix']
                    fig_cm = px.imshow(
                        cm_data['values'],
                        x=cm_data['labels'],
                        y=cm_data['labels'],
                        labels=dict(x="Predicted Crop", y="Actual Crop", color="Count"),
                        color_continuous_scale='RdBu_r',
                        text_auto=True
                    )
                    fig_cm.update_layout(height=500)
                    st.plotly_chart(fig_cm, use_container_width=True)
                    st.caption("This heatmap shows exactly where the AI gets 'confused' between crops.")
                
                with col_right:
                    st.subheader("💡 Feature Importance")
                    fi_df = pd.DataFrame(report['feature_importance'])
                    fig_fi = px.bar(
                        fi_df,
                        y='feature',
                        x='importance',
                        orientation='h',
                        color='importance',
                        color_continuous_scale='Tealgrn'
                    )
                    fig_fi.update_layout(height=500, yaxis={'categoryorder':'total ascending'})
                    st.plotly_chart(fig_fi, use_container_width=True)
                    st.caption("How much weight the AI gives to each factor (NPK, Rainfall, etc.).")
                
                # 3. Best Hyperparameters
                with st.expander("⚙️ View Optimized Hyperparameters"):
                    st.json(report['best_params'])
                    st.caption("These are the mathematically 'perfect' settings found for your Random Forest model.")
            else:
                st.warning("⚠️ High-level scientific report is currently being generated or unavailable.")
    else:
        st.error("❌ Could not load model comparison data.")
        st.info("Ensure the backend server is running and the dataset is available for training.")

# ==================== PAGE 4: ABOUT ====================
elif page == "ℹ️ About":
    st.header("About This System")
    
    st.markdown("""
    ### 🌾 Smart Crop Recommendation System
    
    This is a **production-ready, full-stack machine learning application** that helps farmers 
    make data-driven decisions about which crops to grow based on soil and climate conditions.
    
    #### 🎯 Key Features
    - **Real-time Predictions**: Get instant crop recommendations
    - **Trust & Explainability Dashboard**: SHAP-powered reasoning for every prediction.
    - **Confidence Scoring**: Progress bars and suitability rankings (High/Moderate/Low).
    - **Model Comparison Pipeline**: Comparative analysis of multiple ML algorithms.
    - **Scientific Maturity Reports**: Confusion matrices and feature importance tracking.
    - **Production-Ready Signals**: API versioning, health checks, and request ID tracking.
    
    #### 🛠️ Technology Stack
    - **Frontend**: Streamlit (Python)
    - **Backend**: Flask REST API (Python)
    - **Database**: PostgreSQL (Production) / SQLite (Development)
    - **ML Model**: scikit-learn RandomForestClassifier
    - **Deployment**: Render / Railway
    
    #### 📊 Model Inputs
    1. **Nitrogen (N)**: 0-140 kg/ha
    2. **Phosphorus (P)**: 5-145 kg/ha
    3. **Potassium (K)**: 5-205 kg/ha
    4. **Temperature**: 8-44°C
    5. **Humidity**: 14-100%
    6. **pH Level**: 3.5-10.0
    7. **Rainfall**: 20-300mm
    
    #### 🎓 Educational Value
    - **Tiered Development**: Project evolved through 7 industry-standard upgrades.
    - **Explainable AI (XAI)**: Moving beyond "Black Box" predictions with SHAP.
    - **DevOps Excellence**: Implementing request tracking and centralized logging.
    - **Data Rigor**: Domain-specific feature engineering and model tuning.
    
    #### 📝 Sample Crops
    The model can recommend various crops including:
    - Rice, Wheat, Maize
    - Cotton, Jute
    - Coffee, Tea
    - And many more...
    
    ---
    **Version**: 1.0.0  
    **Last Updated**: February 2026  
    **Built with**: ❤️ and Python
    """)
    
    # System status
    st.markdown("### 🔧 System Status")
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div class="info-card">
            <h4>Backend API</h4>
            <p>Flask REST API running on port 5000</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="info-card">
            <h4>Frontend</h4>
            <p>Streamlit web application</p>
        </div>
        """, unsafe_allow_html=True)

# ==================== FOOTER ====================
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #666; padding: 1rem;'>"
    "Built with ❤️ using Streamlit & Flask | © 2026 Crop Recommendation System"
    "</div>",
    unsafe_allow_html=True
)
