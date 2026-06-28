/**
 * @file TypeScript interfaces for Kubernetes resource objects and audit events.
 */

export interface ContainerInfo {
  name: string;
  image: string;
  ready: boolean;
  restart_count: number;
  state: string;
  state_reason: string | null;
}

export interface PodInfo {
  name: string;
  namespace: string;
  status: string;
  ready: string;
  restarts: number;
  age: string;
  node: string | null;
  labels: Record<string, string>;
  containers: ContainerInfo[];
  created_at: string | null;
}

export interface DeploymentCondition {
  type: string;
  status: string;
  reason: string | null;
  message: string | null;
}

export interface DeploymentInfo {
  name: string;
  namespace: string;
  desired: number;
  ready: number;
  available: number;
  updated: number;
  age: string;
  images: string[];
  conditions: DeploymentCondition[];
  labels: Record<string, string>;
  created_at: string | null;
}

export interface ServicePort {
  name: string | null;
  protocol: string;
  port: number;
  target_port: string | number | null;
  node_port: number | null;
}

export interface ServiceInfo {
  name: string;
  namespace: string;
  type: string;
  cluster_ip: string | null;
  external_ip: string | null;
  ports: ServicePort[];
  selector: Record<string, string>;
  age: string;
  created_at: string | null;
}

export interface NodeCondition {
  type: string;
  status: string;
  reason: string | null;
  message: string | null;
}

export interface NodeInfo {
  name: string;
  status: string;
  roles: string[];
  age: string;
  version: string;
  os_image: string | null;
  kernel_version: string | null;
  container_runtime: string | null;
  cpu_capacity: string | null;
  memory_capacity: string | null;
  conditions: NodeCondition[];
  unschedulable: boolean;
}

export interface EventInfo {
  name: string;
  namespace: string;
  type: string;
  reason: string;
  message: string;
  involved_object_kind: string;
  involved_object_name: string;
  count: number;
  first_time: string | null;
  last_time: string | null;
  source_component: string | null;
  source_host: string | null;
}

export interface AuditEvent {
  id: string;
  timestamp: string;
  session_id: string;
  user_intent: string;
  cluster_context: string;
  namespace: string;
  generated_command: string | null;
  risk_level: string;
  dry_run_result: unknown | null;
  approved: boolean | null;
  execution_result: unknown | null;
  error: string | null;
}

export interface PaginatedAuditEvents {
  items: AuditEvent[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}
