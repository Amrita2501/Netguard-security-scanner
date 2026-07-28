export type RiskLevel = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL'
export type HostStatus = 'online' | 'offline'

export interface Port {
  id: number
  host_id: number
  port_number: number
  protocol: string
  service_name: string | null
  state: string | null
  version: string | null
  banner: string | null
}

export interface Recommendation {
  id: number
  host_id: number
  port_number: number | null
  severity: RiskLevel
  title: string
  description: string
}

export interface Host {
  id: number
  scan_id: number
  ip_address: string
  hostname: string | null
  mac_address: string | null
  vendor: string | null
  os_name: string | null
  os_family: string | null
  os_confidence: number | null
  status: HostStatus
  latency_ms: number | null
  last_seen: string | null
  risk_score: number
  risk_level: RiskLevel
  vlan_id?: number | null
  vlan_name?: string | null
  ports: Port[]
  recommendations?: Recommendation[]
  scan_target?: string
  scan_started_at?: string
}

export interface Scan {
  id: number
  target: string
  scan_type: string
  profile: string
  status: 'running' | 'completed' | 'failed'
  started_at: string
  finished_at: string | null
  duration_seconds: number | null
  total_hosts: number
  live_hosts: number
  error_message: string | null
}

export interface ScanProgress {
  phase: string
  current?: number
  total?: number
  percent: number
  current_host?: string | null
  error?: string
}

export interface DashboardSummary {
  total_devices: number
  live_hosts: number
  offline_hosts: number
  total_open_ports: number
  high_risk_devices: number
  scan_duration: number | null
  last_scan_target: string | null
  last_scan_at: string | null
  risk_distribution: Record<RiskLevel, number>
}

export interface DashboardCharts {
  protocol_distribution: { name: string; value: number }[]
  top_open_ports: { port: string; count: number }[]
  scan_history: { scan_id: number; date: string; live_hosts: number; duration: number | null }[]
  host_status: { name: string; value: number }[]
}

export interface Interface {
  id: number
  host_id: number
  if_index: number
  if_descr: string
  if_type: string
  if_speed_mbps: number | null
  if_admin_status: string
  if_oper_status: string
}

export interface SnmpInfo {
  id: number
  host_id: number
  sys_descr: string | null
  sys_name: string | null
  sys_uptime: string | null
  sys_contact: string | null
  sys_location: string | null
  community_used: string | null
  queried_at: string
}

export interface SnmpResponse {
  available: boolean
  info: SnmpInfo | null
  interfaces: Interface[]
}

export interface Cve {
  cve_id: string
  description: string | null
  severity: string
  cvss_score: number | null
  source: 'offline' | 'nvd'
}

export interface CveFinding {
  port_number: number
  service_name: string
  version: string | null
  cves: Cve[]
}

export interface CveResponse {
  host_id: number
  findings: CveFinding[]
}

export interface TopologyNode {
  id: string
  label: string
  type: 'network' | 'vlan' | 'host'
  hostname?: string | null
  status?: HostStatus
  risk_level?: RiskLevel
  os_family?: string
  vlan_name?: string
}

export interface TopologyEdge {
  source: string
  target: string
}

export interface Topology {
  nodes: TopologyNode[]
  edges: TopologyEdge[]
}
