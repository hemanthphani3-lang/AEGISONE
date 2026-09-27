import React, { useEffect, useState } from 'react';
import { auditApi, AuditQueryFilter } from '@/services/api/auditApi';
import { AuditEvent, AuditEventType, AuditOutcome } from '@/types/audit';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { Card, CardContent } from '@/components/ui/Card';
import { EmptyState } from '@/components/ui/EmptyState';
import { ErrorState } from '@/components/ui/ErrorState';
import { Skeleton } from '@/components/ui/Skeleton';
import { Modal } from '@/components/ui/Modal';
import {
  History,
  RefreshCw,
  Search,
  Filter,
  ChevronLeft,
  ChevronRight,
  Eye,
  ShieldAlert,
  Clock,
  User,
  Activity,
  Layers,
  FileCode,
  Link,
  X,
} from 'lucide-react';

export const AuditPage: React.FC = () => {
  const [events, setEvents] = useState<AuditEvent[]>([]);
  const [total, setTotal] = useState<number>(0);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Filters & Pagination State
  const [eventTypeFilter, setEventTypeFilter] = useState<string>('');
  const [outcomeFilter, setOutcomeFilter] = useState<string>('');
  const [resourceTypeFilter, setResourceTypeFilter] = useState<string>('');
  const [resourceIdFilter, setResourceIdFilter] = useState<string>('');
  const [correlationIdSearch, setCorrelationIdSearch] = useState<string>('');
  const [actorFilter, setActorFilter] = useState<string>('');

  const [limit, setLimit] = useState<number>(20);
  const [offset, setOffset] = useState<number>(0);

  // Selected event for detail drawer / modal
  const [selectedEvent, setSelectedEvent] = useState<AuditEvent | null>(null);

  const fetchAuditEvents = async () => {
    setLoading(true);
    setError(null);
    try {
      const queryParams: AuditQueryFilter = {
        limit,
        offset,
      };
      if (eventTypeFilter) queryParams.event_type = eventTypeFilter;
      if (outcomeFilter) queryParams.outcome = outcomeFilter;
      if (resourceTypeFilter) queryParams.resource_type = resourceTypeFilter;
      if (resourceIdFilter.trim()) queryParams.resource_id = resourceIdFilter.trim();
      if (correlationIdSearch.trim()) queryParams.correlation_id = correlationIdSearch.trim();
      if (actorFilter.trim()) queryParams.actor_user_id = actorFilter.trim();

      const response = await auditApi.queryEvents(queryParams);
      setEvents(response.events || []);
      setTotal(response.total || 0);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch audit event log.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAuditEvents();
  }, [offset, limit, eventTypeFilter, outcomeFilter]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setOffset(0);
    fetchAuditEvents();
  };

  const handleResetFilters = () => {
    setEventTypeFilter('');
    setOutcomeFilter('');
    setResourceTypeFilter('');
    setCorrelationIdSearch('');
    setActorFilter('');
    setOffset(0);
  };

  const handleInvestigateCorrelation = (correlationId: string) => {
    setCorrelationIdSearch(correlationId);
    setOffset(0);
    setSelectedEvent(null);
  };

  const currentPage = Math.floor(offset / limit) + 1;
  const totalPages = Math.max(1, Math.ceil(total / limit));

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-slate-900 tracking-tight flex items-center gap-2">
            <History className="w-5 h-5 text-indigo-600" /> Security Audit Investigation Log
          </h2>
          <p className="text-xs text-slate-500 mt-1">
            Immutable audit events persisted in Supabase PostgreSQL by AegisOne Audit Engine
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={fetchAuditEvents} disabled={loading}>
            <RefreshCw className={`w-3.5 h-3.5 mr-1 ${loading ? 'animate-spin' : ''}`} /> Refresh Log
          </Button>
        </div>
      </div>

      {/* Filter & Search Toolbar */}
      <Card>
        <CardContent className="p-4 space-y-4">
          <form onSubmit={handleSearchSubmit} className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
            {/* Correlation ID / Search */}
            <div>
              <label className="block text-[11px] font-semibold text-slate-600 uppercase mb-1">
                Correlation ID
              </label>
              <div className="relative">
                <input
                  type="text"
                  placeholder="e.g. corr-1234..."
                  value={correlationIdSearch}
                  onChange={(e) => setCorrelationIdSearch(e.target.value)}
                  className="w-full pl-8 pr-3 py-1.5 text-xs bg-slate-50 border border-slate-200 rounded-md focus:outline-none focus:ring-1 focus:ring-indigo-500 font-mono"
                />
                <Search className="w-3.5 h-3.5 text-slate-400 absolute left-2.5 top-2.5" />
              </div>
            </div>

            {/* Event Type Filter */}
            <div>
              <label className="block text-[11px] font-semibold text-slate-600 uppercase mb-1">
                Event Type
              </label>
              <select
                value={eventTypeFilter}
                onChange={(e) => {
                  setEventTypeFilter(e.target.value);
                  setOffset(0);
                }}
                className="w-full px-3 py-1.5 text-xs bg-slate-50 border border-slate-200 rounded-md focus:outline-none focus:ring-1 focus:ring-indigo-500"
              >
                <option value="">All Event Types</option>
                {Object.values(AuditEventType).map((type) => (
                  <option key={type} value={type}>
                    {type}
                  </option>
                ))}
              </select>
            </div>

            {/* Outcome Filter */}
            <div>
              <label className="block text-[11px] font-semibold text-slate-600 uppercase mb-1">
                Outcome
              </label>
              <select
                value={outcomeFilter}
                onChange={(e) => {
                  setOutcomeFilter(e.target.value);
                  setOffset(0);
                }}
                className="w-full px-3 py-1.5 text-xs bg-slate-50 border border-slate-200 rounded-md focus:outline-none focus:ring-1 focus:ring-indigo-500"
              >
                <option value="">All Outcomes</option>
                {Object.values(AuditOutcome).map((oc) => (
                  <option key={oc} value={oc}>
                    {oc}
                  </option>
                ))}
              </select>
            </div>

            {/* Actor User ID Filter */}
            <div>
              <label className="block text-[11px] font-semibold text-slate-600 uppercase mb-1">
                Actor User ID
              </label>
              <input
                type="text"
                placeholder="e.g. user-001"
                value={actorFilter}
                onChange={(e) => setActorFilter(e.target.value)}
                className="w-full px-3 py-1.5 text-xs bg-slate-50 border border-slate-200 rounded-md focus:outline-none focus:ring-1 focus:ring-indigo-500 font-mono"
              />
            </div>

            {/* Action Buttons */}
            <div className="flex items-end gap-2">
              <Button type="submit" size="sm" className="flex-1 text-xs">
                <Filter className="w-3 h-3 mr-1" /> Apply Filter
              </Button>
              {(eventTypeFilter || outcomeFilter || resourceTypeFilter || correlationIdSearch || actorFilter) && (
                <Button type="button" variant="ghost" size="sm" onClick={handleResetFilters} title="Clear Filters">
                  <X className="w-3.5 h-3.5 text-slate-500" />
                </Button>
              )}
            </div>
          </form>
        </CardContent>
      </Card>

      {/* Main Audit Data View */}
      {loading ? (
        <div className="space-y-2">
          <Skeleton className="h-12 w-full" />
          <Skeleton className="h-12 w-full" />
          <Skeleton className="h-12 w-full" />
        </div>
      ) : error ? (
        <ErrorState title="Audit Fetch Failed" message={error} onRetry={fetchAuditEvents} />
      ) : events.length === 0 ? (
        <EmptyState
          title="No Audit Events Found"
          description={
            correlationIdSearch || eventTypeFilter || outcomeFilter || actorFilter
              ? 'No security audit logs match the specified search and filter criteria.'
              : 'There are currently no security audit events recorded in the system database.'
          }
          actionLabel="Reset Search Filters"
          onAction={handleResetFilters}
          icon={<History className="w-10 h-10 text-slate-400" />}
        />
      ) : (
        <Card className="overflow-hidden">
          <CardContent className="p-0">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs text-slate-700">
                <thead className="bg-slate-50 text-slate-500 uppercase tracking-wider text-[10px] font-semibold border-b border-slate-200">
                  <tr>
                    <th className="px-4 py-3">Timestamp (UTC)</th>
                    <th className="px-4 py-3">Event Type</th>
                    <th className="px-4 py-3">Actor</th>
                    <th className="px-4 py-3">Action</th>
                    <th className="px-4 py-3">Outcome</th>
                    <th className="px-4 py-3">Correlation ID</th>
                    <th className="px-4 py-3 text-right">Inspect</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {events.map((evt) => (
                    <tr
                      key={evt.id}
                      onClick={() => setSelectedEvent(evt)}
                      className="hover:bg-indigo-50/50 cursor-pointer transition-colors"
                    >
                      <td className="px-4 py-3 font-mono text-[11px] whitespace-nowrap text-slate-600">
                        {new Date(evt.timestamp).toLocaleString()}
                      </td>
                      <td className="px-4 py-3">
                        <Badge variant="outline" className="font-mono text-[10px] bg-white">
                          {evt.event_type}
                        </Badge>
                      </td>
                      <td className="px-4 py-3 font-medium text-slate-900">
                        {evt.actor_username || evt.actor_user_id}
                      </td>
                      <td className="px-4 py-3 font-mono text-[11px]">{evt.action}</td>
                      <td className="px-4 py-3">
                        <Badge
                          variant={
                            evt.outcome === AuditOutcome.SUCCESS
                              ? 'success'
                              : evt.outcome === AuditOutcome.DENIED
                              ? 'warning'
                              : 'danger'
                          }
                        >
                          {evt.outcome}
                        </Badge>
                      </td>
                      <td className="px-4 py-3 font-mono text-[10px] text-indigo-600 hover:underline truncate max-w-[140px]">
                        {evt.correlation_id ? (
                          <span
                            onClick={(e) => {
                              e.stopPropagation();
                              handleInvestigateCorrelation(evt.correlation_id!);
                            }}
                            title="Click to filter trace by this Correlation ID"
                          >
                            {evt.correlation_id}
                          </span>
                        ) : (
                          '-'
                        )}
                      </td>
                      <td className="px-4 py-3 text-right">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={(e) => {
                            e.stopPropagation();
                            setSelectedEvent(evt);
                          }}
                          className="h-6 w-6 p-0 text-slate-400 hover:text-indigo-600"
                        >
                          <Eye className="w-3.5 h-3.5" />
                        </Button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Pagination Controls */}
            <div className="flex items-center justify-between px-4 py-3 bg-slate-50 border-t border-slate-200 text-xs text-slate-600">
              <div>
                Showing <span className="font-medium">{offset + 1}</span> to{' '}
                <span className="font-medium">{Math.min(offset + limit, total)}</span> of{' '}
                <span className="font-medium">{total}</span> events
              </div>
              <div className="flex items-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  disabled={offset === 0}
                  onClick={() => setOffset(Math.max(0, offset - limit))}
                >
                  <ChevronLeft className="w-3.5 h-3.5 mr-1" /> Previous
                </Button>
                <span className="text-xs font-medium px-2">
                  Page {currentPage} of {totalPages}
                </span>
                <Button
                  variant="outline"
                  size="sm"
                  disabled={offset + limit >= total}
                  onClick={() => setOffset(offset + limit)}
                >
                  Next <ChevronRight className="w-3.5 h-3.5 ml-1" />
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Audit Event Detail Drawer Modal */}
      {selectedEvent && (
        <Modal
          isOpen={!!selectedEvent}
          onClose={() => setSelectedEvent(null)}
          title={`Audit Event Investigation (${selectedEvent.event_type})`}
        >
          <div className="space-y-4 text-xs">
            {/* Quick Metadata Headers */}
            <div className="grid grid-cols-2 gap-3 p-3 bg-slate-50 rounded-lg border border-slate-200">
              <div>
                <span className="text-slate-400 block text-[10px] uppercase font-semibold">Event ID</span>
                <span className="font-mono text-slate-800 text-[11px] truncate block">{selectedEvent.id}</span>
              </div>
              <div>
                <span className="text-slate-400 block text-[10px] uppercase font-semibold">Timestamp</span>
                <span className="font-mono text-slate-800 text-[11px]">
                  {new Date(selectedEvent.timestamp).toISOString()}
                </span>
              </div>
              <div>
                <span className="text-slate-400 block text-[10px] uppercase font-semibold">Outcome</span>
                <Badge
                  variant={
                    selectedEvent.outcome === AuditOutcome.SUCCESS
                      ? 'success'
                      : selectedEvent.outcome === AuditOutcome.DENIED
                      ? 'warning'
                      : 'danger'
                  }
                >
                  {selectedEvent.outcome}
                </Badge>
              </div>
              <div>
                <span className="text-slate-400 block text-[10px] uppercase font-semibold">Correlation ID</span>
                {selectedEvent.correlation_id ? (
                  <button
                    onClick={() => handleInvestigateCorrelation(selectedEvent.correlation_id!)}
                    className="font-mono text-indigo-600 hover:underline text-[11px] flex items-center gap-1"
                  >
                    <Link className="w-3 h-3" /> {selectedEvent.correlation_id}
                  </button>
                ) : (
                  <span className="text-slate-400 font-mono text-[11px]">None</span>
                )}
              </div>
            </div>

            {/* Actor Information */}
            <div className="p-3 bg-white rounded-lg border border-slate-200 space-y-2">
              <h4 className="font-semibold text-slate-800 text-xs flex items-center gap-1">
                <User className="w-3.5 h-3.5 text-indigo-600" /> Actor Principal Context
              </h4>
              <div className="grid grid-cols-2 gap-2 text-slate-700">
                <div>
                  <span className="text-slate-500">User ID:</span>{' '}
                  <span className="font-mono text-slate-900">{selectedEvent.actor_user_id}</span>
                </div>
                <div>
                  <span className="text-slate-500">Username:</span>{' '}
                  <span className="font-semibold text-slate-900">
                    {selectedEvent.actor_username || 'Anonymous/Service'}
                  </span>
                </div>
                <div className="col-span-2">
                  <span className="text-slate-500 block mb-1">Assigned Roles:</span>
                  <div className="flex flex-wrap gap-1">
                    {selectedEvent.actor_roles && selectedEvent.actor_roles.length > 0 ? (
                      selectedEvent.actor_roles.map((role) => (
                        <Badge key={role} variant="outline" className="text-[10px]">
                          {role}
                        </Badge>
                      ))
                    ) : (
                      <span className="text-slate-400 italic">No roles recorded</span>
                    )}
                  </div>
                </div>
              </div>
            </div>

            {/* Resource & Action Context */}
            <div className="p-3 bg-white rounded-lg border border-slate-200 space-y-2">
              <h4 className="font-semibold text-slate-800 text-xs flex items-center gap-1">
                <Activity className="w-3.5 h-3.5 text-indigo-600" /> Target Resource & Action
              </h4>
              <div className="grid grid-cols-2 gap-2 text-slate-700">
                <div>
                  <span className="text-slate-500">Resource Type:</span>{' '}
                  <span className="font-mono text-slate-900">{selectedEvent.resource_type}</span>
                </div>
                <div>
                  <span className="text-slate-500">Resource ID:</span>{' '}
                  <span className="font-mono text-slate-900">{selectedEvent.resource_id || 'Global / N/A'}</span>
                </div>
                <div className="col-span-2">
                  <span className="text-slate-500">Action:</span>{' '}
                  <span className="font-mono font-semibold text-slate-900">{selectedEvent.action}</span>
                </div>
              </div>
            </div>

            {/* JSON Metadata Payload */}
            <div className="p-3 bg-slate-950 text-slate-100 rounded-lg space-y-2">
              <h4 className="font-semibold text-xs text-slate-300 flex items-center gap-1 font-mono">
                <FileCode className="w-3.5 h-3.5 text-indigo-400" /> Event Metadata JSON Payload
              </h4>
              <pre className="text-[11px] font-mono overflow-x-auto p-2 bg-slate-900 rounded border border-slate-800 text-indigo-200">
                {JSON.stringify(selectedEvent.metadata || {}, null, 2)}
              </pre>
            </div>

            {/* Footer buttons */}
            <div className="flex justify-between items-center pt-2">
              {selectedEvent.correlation_id && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handleInvestigateCorrelation(selectedEvent.correlation_id!)}
                  className="text-xs"
                >
                  <Search className="w-3.5 h-3.5 mr-1 text-indigo-600" /> Filter Trace by Correlation ID
                </Button>
              )}
              <Button variant="ghost" size="sm" onClick={() => setSelectedEvent(null)} className="ml-auto">
                Close Investigation
              </Button>
            </div>
          </div>
        </Modal>
      )}
    </div>
  );
};

