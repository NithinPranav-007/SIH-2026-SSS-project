export interface DriftMilestone {
  horizon_hours: number;
  timestamp: string;
  latitude: number;
  longitude: number;
  distance_km: number;
  speed_ms: number;
  heading_deg: number;
  uncertainty_radius_km: number;
}

export interface DriftForecastSummary {
  forecast_id: string;
  contact_id?: string | null;
  initial_latitude: number;
  initial_longitude: number;
  initial_timestamp: string;
  depth_m: number;
  model_name: string;
  model_version: string;
  champion_model: string;
  execution_mode: string;
  hotspot_score: number;
  hotspot_evidence: Record<string, any>;
  milestones: Record<string, DriftMilestone>;
  created_at: string;
}

export interface DriftForecastDetail extends DriftForecastSummary {
  geojson: any;
}

export interface OceanDataStatus {
  copernicus: {
    available: boolean;
    dataset_product_id?: string;
    dataset_id?: string;
    drift_mode?: string;
    time_range?: string[];
    depth_levels?: number[];
    latitude_range?: number[];
    longitude_range?: number[];
    variables_available: string[];
    variables_count?: number;
    temporal_resolution?: string;
    spatial_resolution_deg?: number;
    last_update?: string;
    error?: string;
  };
  incois: {
    available: boolean;
    status: string;
    source_mode?: string;
    endpoint_url?: string;
    dataset_name?: string;
    product_family?: string;
    columns: string[];
    variables: string[];
    total_records?: number;
    spatial_coverage?: string;
    last_update?: string;
    error?: string;
  };
  summary: {
    all_sources_ready: boolean;
    drift_mode: string;
    copernicus_variables_count: number;
    incois_status: string;
    missing_variables: string[];
  };
  last_checked: string;
}

export interface DriftModelInfo {
  model_name: string;
  model_class: string;
  version: string;
  status: string;
  description: string;
  metrics: {
    '24h'?: { mae_km: number; rmse_km: number; median_km: number };
    '48h'?: { mae_km: number; rmse_km: number; median_km: number };
    '72h'?: { mae_km: number; rmse_km: number; median_km: number };
    status: string;
  };
}
