export interface ApiEnvelope<T>{data:T;meta:Record<string,unknown>}
export interface Asset{id:number;equipment_id:string;equipment_type:string;display_name:string;status:string;health_score:number|null;last_seen_at:string|null}
export interface Measurement{id:number;timestamp:string;equipment_id:string;equipment_type:string;temperature:number|null;vibration:number|null;rpm:number|null;current:number|null;load:number|null;pressure:number|null;flow_rate:number|null;health_score:number|null;is_anomaly:boolean}
export interface Alert{id:number;alert_id:string;timestamp:string;level:string;title:string;message:string;acknowledged:boolean}
export interface WorkOrder{id:number;work_order_id:string;equipment_id:string;priority:string;status:string;scheduled_start:string|null;estimated_cost:number|null}
export interface RulPrediction{id:number;timestamp:string;equipment_id:string;predicted_rul_hours:number;risk_level:string;prediction_confidence:number|null}
export type RecordRow=Record<string,string|number|boolean|null|undefined>;
