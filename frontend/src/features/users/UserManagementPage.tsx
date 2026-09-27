import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { Users, UserPlus, ShieldAlert, CheckCircle2, Lock, UserX, RefreshCw } from 'lucide-react';
import { apiClient } from '@/services/api/apiClient';

interface UserRecord {
  id: string;
  username: string;
  email: string;
  first_name?: string;
  last_name?: string;
  enabled: boolean;
  roles: string[];
  created_timestamp?: number;
}

export const UserManagementPage: React.FC = () => {
  const [users, setUsers] = useState<UserRecord[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // New User Form State
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [role, setRole] = useState('STUDENT');
  const [creating, setCreating] = useState(false);

  const fetchUsers = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await apiClient.get<UserRecord[]>('/users');
      setUsers(data);
    } catch (err: any) {
      setError(err.message || 'Failed to load Keycloak user accounts.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchUsers();
  }, []);

  const handleCreateUser = async (e: React.FormEvent) => {
    e.preventDefault();
    setCreating(true);
    setError(null);
    try {
      await apiClient.post('/users', {
        username: username.trim(),
        email: email.trim(),
        first_name: firstName.trim(),
        last_name: lastName.trim(),
        role,
      });
      setShowCreateModal(false);
      setUsername('');
      setEmail('');
      setFirstName('');
      setLastName('');
      setRole('STUDENT');
      fetchUsers();
    } catch (err: any) {
      setError(err.message || 'Failed to create user account.');
    } finally {
      setCreating(false);
    }
  };

  const handleToggleUser = async (userId: string, currentEnabled: boolean) => {
    try {
      await apiClient.post(`/users/${userId}/toggle`, { enabled: !currentEnabled });
      fetchUsers();
    } catch (err: any) {
      setError(err.message || 'Failed to update user status.');
    }
  };

  const handleResetPassword = async (userId: string) => {
    try {
      await apiClient.post(`/users/${userId}/reset-password`, { send_required_action_email: true });
      alert('Password reset action email dispatched.');
    } catch (err: any) {
      setError(err.message || 'Failed to reset password.');
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-slate-900 tracking-tight">Keycloak User Administration</h2>
          <p className="text-xs text-slate-500 mt-1">
            Manage realm user accounts, credentials, required actions, and AegisOne RBAC roles.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={fetchUsers} loading={loading}>
            <RefreshCw className="w-3.5 h-3.5 mr-1" /> Refresh
          </Button>
          <Button variant="primary" size="sm" onClick={() => setShowCreateModal(true)}>
            <UserPlus className="w-3.5 h-3.5 mr-1" /> Create User
          </Button>
        </div>
      </div>

      {error && (
        <div className="p-3 bg-red-50 border border-red-200 text-red-700 rounded-xl text-xs flex items-center gap-2">
          <ShieldAlert className="w-4 h-4 text-red-500 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-sm font-semibold flex items-center gap-2">
            <Users className="w-4 h-4 text-indigo-600" /> Keycloak Realm User Directory ({users.length})
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 text-slate-500 uppercase tracking-wider text-[10px] font-semibold border-b border-slate-200">
                <tr>
                  <th className="px-3 py-2">Username</th>
                  <th className="px-3 py-2">Email</th>
                  <th className="px-3 py-2">Full Name</th>
                  <th className="px-3 py-2">Assigned Role</th>
                  <th className="px-3 py-2">Status</th>
                  <th className="px-3 py-2 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {users.map((u) => (
                  <tr key={u.id} className="hover:bg-slate-50/60 transition-colors">
                    <td className="px-3 py-2 font-mono font-semibold text-slate-900">{u.username}</td>
                    <td className="px-3 py-2 font-mono text-slate-600">{u.email}</td>
                    <td className="px-3 py-2 text-slate-700">{`${u.first_name || ''} ${u.last_name || ''}`.trim() || 'N/A'}</td>
                    <td className="px-3 py-2">
                      {u.roles.map((r) => (
                        <Badge key={r} variant="default" className="text-[10px] uppercase mr-1">
                          {r}
                        </Badge>
                      ))}
                    </td>
                    <td className="px-3 py-2">
                      {u.enabled ? (
                        <Badge variant="success" className="text-[10px] gap-1">
                          <CheckCircle2 className="w-3 h-3" /> ACTIVE
                        </Badge>
                      ) : (
                        <Badge variant="outline" className="text-[10px] text-red-600 bg-red-50 border-red-200 gap-1">
                          <UserX className="w-3 h-3" /> DISABLED
                        </Badge>
                      )}
                    </td>
                    <td className="px-3 py-2 text-right space-x-1">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleToggleUser(u.id, u.enabled)}
                      >
                        {u.enabled ? 'Disable' : 'Enable'}
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleResetPassword(u.id)}
                        title="Trigger Reset Password Email"
                      >
                        <Lock className="w-3 h-3 text-slate-500" />
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      {/* Create User Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 backdrop-blur-xs p-4">
          <div className="bg-white rounded-2xl shadow-2xl max-w-md w-full border border-slate-200 p-6 space-y-4">
            <h3 className="text-base font-bold text-slate-900">Create Keycloak User Account</h3>
            <form onSubmit={handleCreateUser} className="space-y-3 text-xs">
              <div>
                <label className="font-semibold text-slate-700 block mb-1">Username</label>
                <input
                  type="text"
                  required
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  className="w-full p-2 border border-slate-300 rounded-lg font-mono"
                  placeholder="jdoe"
                />
              </div>

              <div>
                <label className="font-semibold text-slate-700 block mb-1">Email Address</label>
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full p-2 border border-slate-300 rounded-lg font-mono"
                  placeholder="jdoe@aegisone.local"
                />
              </div>

              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="font-semibold text-slate-700 block mb-1">First Name</label>
                  <input
                    type="text"
                    value={firstName}
                    onChange={(e) => setFirstName(e.target.value)}
                    className="w-full p-2 border border-slate-300 rounded-lg"
                  />
                </div>
                <div>
                  <label className="font-semibold text-slate-700 block mb-1">Last Name</label>
                  <input
                    type="text"
                    value={lastName}
                    onChange={(e) => setLastName(e.target.value)}
                    className="w-full p-2 border border-slate-300 rounded-lg"
                  />
                </div>
              </div>

              <div>
                <label className="font-semibold text-slate-700 block mb-1">AegisOne RBAC Role</label>
                <select
                  value={role}
                  onChange={(e) => setRole(e.target.value)}
                  className="w-full p-2 border border-slate-300 rounded-lg bg-white font-medium"
                >
                  <option value="STUDENT">STUDENT</option>
                  <option value="STAFF">STAFF</option>
                  <option value="SECURITY_ADMIN">SECURITY_ADMIN</option>
                  <option value="ADMIN">ADMIN</option>
                  <option value="BREAK_GLASS">BREAK_GLASS</option>
                </select>
              </div>

              <div className="flex justify-end gap-2 pt-3">
                <Button type="button" variant="outline" size="md" onClick={() => setShowCreateModal(false)}>
                  Cancel
                </Button>
                <Button type="submit" variant="primary" size="md" loading={creating} disabled={creating}>
                  Create Keycloak User
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
