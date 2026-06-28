/**
 * @file TanStack Query hook for paginated audit log data.
 */

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { auditApi } from "@/lib/api";

interface UseAuditOptions {
  pageSize?: number;
  clusterContext?: string;
  riskLevel?: string;
}

export function useAudit(options: UseAuditOptions = {}) {
  const { pageSize = 50, clusterContext, riskLevel } = options;
  const [page, setPage] = useState(1);

  const query = useQuery({
    queryKey: ["audit", page, pageSize, clusterContext, riskLevel],
    queryFn: () =>
      auditApi.list({
        page,
        page_size: pageSize,
        ...(clusterContext ? { cluster_context: clusterContext } : {}),
        ...(riskLevel ? { risk_level: riskLevel } : {}),
      }),
    staleTime: 10_000,
  });

  return {
    ...query,
    page,
    setPage,
    totalPages: query.data?.total_pages ?? 1,
  };
}
