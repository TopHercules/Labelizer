from airgoutils.helpers.configs import Config
from airgoutils.measure import IMUs
import pandas as pd

def predict_IMU(imu_data):
    try:
        # Check if 'TS' is already in datetime format
        if not pd.api.types.is_datetime64_any_dtype(imu_data['TS']):
            # Attempt to convert 'TS' to datetime if it's not already
            imu_data['TS'] = pd.to_datetime(imu_data['TS'], unit='s', errors='coerce')
            if imu_data['TS'].isnull().any():
                raise ValueError("TS conversion resulted in NaT values, indicating invalid timestamps.")
        
        imu_data = imu_data.sort_values('TS')
        
        # Initialize and load the model
        cfg = Config(parse_passwords=False).read_file('imu_labelizer.ini')
        imu_model = IMUs(cfg.project.folder + cfg.project.imu_folder, cfg.project.model_name)
        _, predict = imu_model.predict(imu_data, return_p=True)
        
        return predict.prob
    except Exception as e:
        print(f"Error in predict_IMU: {e}")
        return None
