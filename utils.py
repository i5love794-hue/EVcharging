import pandas as pd
import numpy as np

def load_data():
    """데이터를 로드하고 기본 전처리를 수행합니다."""
    usage = pd.read_parquet('data/EVChargingStationUsage.parquet')
    pop = pd.read_parquet('data/Electric_Vehicle_Population_Data.parquet')
    patterns = pd.read_parquet('data/ev_charging_patterns.parquet')
    
    # 시간 데이터 변환
    patterns['Charging Start Time'] = pd.to_datetime(patterns['Charging Start Time'])
    patterns['Start Hour'] = patterns['Charging Start Time'].dt.hour
    
    return usage, pop, patterns

def calculate_revenue(df):
    """최신 시장 트렌드를 반영한 시간 기반 수익 모델 적용
    - 기본 요금: $3.0 (고정)
    - 시간당 요금: 
        - Off-peak (00-12, 19-23): $2.0/h
        - Peak (12-18): $5.0/h
    - 장기 점유 페널티 (유휴료): 3시간 초과 시 시간당 $10.0 추가
    """
    def compute_row_rev(row):
        duration = row['Charging Duration (hours)']
        hour = row['Start Hour']
        
        # 피크 타임 여부
        is_peak = 12 <= hour <= 18
        hourly_rate = 5.0 if is_peak else 2.0
        
        # 매출 계산
        revenue = 3.0 + (duration * hourly_rate)
        
        # 유휴 페널티 (3시간 초과분)
        if duration > 3:
            idle_fee = (duration - 3) * 10.0
            revenue += idle_fee
            
        return revenue

    df['Revenue'] = df.apply(compute_row_rev, axis=1)
    
    # 시간별 세그먼트 분류
    df['Duration Bin'] = pd.cut(
        df['Charging Duration (hours)'], 
        bins=[0, 1, 2, 3, 24], 
        labels=['1시간 이내', '1-2시간', '2-3시간', '3시간 이상']
    )
    
    return df

def get_region_gap(usage, pop):
    """지역별 EV 보급 대비 충전소 부족 분석"""
    station_counts = usage.groupby('City').size().reset_index(name='Station_Count')
    ev_counts = pop.groupby('City').size().reset_index(name='EV_Count')
    
    merged = pd.merge(ev_counts, station_counts, on='City', how='left').fillna(0)
    # 격차 지수: EV 대수 / (충전소 수 + 1)
    merged['Gap_Score'] = merged['EV_Count'] / (merged['Station_Count'] + 1)
    
    return merged.sort_values(by='Gap_Score', ascending=False).head(10)
