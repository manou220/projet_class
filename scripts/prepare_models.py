"""
Utility to prepare/save ML model artifacts in the expected format for the Flask app.

If your `.joblib` file currently contains a raw model object (e.g. RandomForestRegressor),
this script will wrap it into a dict with keys:
  - 'model': the loaded model object
  - 'feature_columns': a conservative default feature list used by the app

Usage:
  python scripts/prepare_models.py path/to/model.joblib [--inplace]

If `--inplace` is provided the original file will be overwritten; otherwise a new
file will be created next to the original named `<orig>_artifact.joblib`.
"""
import os
import argparse
import joblib

DEFAULT_FEATURE_COLUMNS = [
    'Close_diff',
    'lag_diff_1', 'lag_diff_2', 'lag_diff_3', 'lag_diff_5', 'lag_diff_7', 'lag_diff_14',
    'ma_diff_3', 'ma_diff_7', 'ma_diff_14',
    'ma_price_7', 'ma_price_14', 'ma_price_30',
    'day_of_week', 'day_of_month', 'month',
    'volatility'
]


def prepare_model(path, inplace=False):
    if not os.path.exists(path):
        raise FileNotFoundError(path)

    obj = joblib.load(path)
    if isinstance(obj, dict) and 'model' in obj and 'feature_columns' in obj:
        print(f"{os.path.basename(path)} already in artifact format. Skipping.")
        return path

    artifact = {
        'model': obj,
        'feature_columns': DEFAULT_FEATURE_COLUMNS
    }

    base, ext = os.path.splitext(path)
    out_path = path if inplace else f"{base}_artifact{ext}"
    joblib.dump(artifact, out_path)
    print(f"Saved artifact to: {out_path}")
    return out_path


def main():
    parser = argparse.ArgumentParser(description='Wrap model joblib into artifact dict')
    parser.add_argument('model_path', help='Path to .joblib model file')
    parser.add_argument('--inplace', action='store_true', help='Overwrite original file')
    args = parser.parse_args()

    prepare_model(args.model_path, inplace=args.inplace)


if __name__ == '__main__':
    main()
