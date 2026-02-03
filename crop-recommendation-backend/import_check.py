import os
import traceback

# Prevent ML initialization and heavy imports during test imports
os.environ['SKIP_MODEL_LOAD'] = '1'

modules = [
    'app', 'models', 'utils', 'evaluate_model', 'train_model',
    'explainability', 'feature_engineering', 'schemas', 'auth_utils',
    'verify_auth', 'config', 'explainability'
]

results = {}
for m in modules:
    try:
        __import__(m)
        results[m] = 'OK'
    except Exception as e:
        results[m] = traceback.format_exc()

print('IMPORT CHECK RESULTS')
for m, r in results.items():
    if r == 'OK':
        print(f'- {m}: OK')
    else:
        print(f'- {m}: ERROR')
        print(r)
